"""
小象代理 - 可用性检查 & 状态监控

注意: 小象短效IP只有2-5分钟寿命，获取后尽快使用。
     IP过期后会返回连接错误或超时，不是程序bug。
     建议 PROXY_REFRESH_INTERVAL=60 让 Pool 在IP过期前换新。

用法:
  python scripts/proxy_check.py               # 从环境变量读取配置检测
  python scripts/proxy_check.py --all          # 完整检测（含代理实际可用性测试）
  python scripts/proxy_check.py --remaining    # 只查剩余量
"""
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

import httpx

OK = "✅"
WARN = "⚠️"
ERR = "❌"
SKIP = "⏭️"


def color(text, level):
    """Simple terminal coloring."""
    if level == OK:
        return f"\033[32m{text}\033[0m"
    elif level == WARN:
        return f"\033[33m{text}\033[0m"
    elif level == ERR:
        return f"\033[31m{text}\033[0m"
    return text


def parse_api_url(url):
    """从 PROXY_API_URL 中提取 appKey, appSecret, wt(格式)."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    app_key = params.get("appKey", [None])[0]
    app_secret = params.get("appSecret", [None])[0]
    wt = params.get("wt", ["json"])[0]
    return app_key, app_secret, wt


def check_remaining(app_key, app_secret):
    """查询小象代理剩余量."""
    url = "https://api.xiaoxiangdaili.com/ip/remaining"
    params = {"appKey": app_key, "appSecret": app_secret}

    try:
        resp = httpx.get(url, params=params, timeout=10)
        data = resp.json()
    except Exception as e:
        return None, f"请求失败: {e}"

    code = data.get("code")
    msg = data.get("msg", "")
    success = data.get("success", False)
    info = data.get("data")

    if code == 200 and success and info:
        total = int(info.get("total", 0))
        remaining = int(info.get("remaining", 0))
        pct = (remaining / total * 100) if total > 0 else 0
        return {
            "total": total,
            "remaining": remaining,
            "pct": pct,
            "raw": data,
        }, None

    # 错误码映射
    errors = {
        1001: "应用不存在",
        1002: "应用已被冻结或禁用",
        1003: "应用已过期",
        2000: "未知异常",
    }
    hint = errors.get(code, f"未知错误码 {code}")
    return None, f"code={code}, {hint} ({msg})"


def check_extract_api(api_url):
    """测试提取API能否正常返回IP."""
    try:
        resp = httpx.get(api_url, timeout=15)
        text = resp.text.strip()
        ct = resp.headers.get("content-type", "").lower()
    except Exception as e:
        return None, f"请求失败: {e}"

    if not text:
        return None, "API 返回空内容"

    # 尝试JSON解析
    if "json" in ct:
        import json as j
        try:
            data = j.loads(text)
            if data.get("success") or data.get("code") == 200:
                items = data.get("data", [])
                if items:
                    count = len(items)
                    sample = f"{items[0].get('ip', '')}:{items[0].get('port', '')}"
                    return {"count": count, "sample": sample, "raw": data}, None
                else:
                    return None, "API 返回 data 为空列表"
            else:
                return None, f"API 返回错误: {data.get('msg', '')} (code={data.get('code')})"
        except Exception:
            pass

    # Text格式: ip:portip:port
    ips = re.findall(r"(\d+\.\d+\.\d+\.\d+):(\d+)", text)
    valid = [(ip, int(p)) for ip, p in ips if int(p) <= 65535]
    if valid:
        return {"count": len(valid), "sample": f"{valid[0][0]}:{valid[0][1]}", "raw": text[:200]}, None

    return None, f"无法解析API返回: {text[:100]}"


def test_proxy(proxy_addr, test_url="https://httpbin.org/ip", timeout=8):
    """测试代理是否可用."""
    try:
        resp = httpx.get(test_url, proxy=f"http://{proxy_addr}", timeout=timeout)
        if resp.status_code == 200:
            return True, resp.text[:80]
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)[:60]


def main():
    print()
    print("=" * 56)
    print("  小象代理 - 可用性检查")
    print("=" * 56)
    print()

    mode = os.getenv("PROXY_MODE", "none")
    api_url = os.getenv("PROXY_API_URL", "")

    # ── 1. 检查配置 ──
    print("── [1] 配置检查 ──")
    if mode != "xiaoxiang":
        print(f"  {WARN} PROXY_MODE={mode}，非 xiaoxiang 模式，跳过检查")
        print(f"  {SKIP} 设置 PROXY_MODE=xiaoxiang 后重试")
        return 1
    if not api_url:
        print(f"  {ERR} PROXY_API_URL 未设置")
        return 1
    print(f"  {OK} PROXY_MODE=xiaoxiang")
    print(f"  {OK} PROXY_API_URL 已配置 ({len(api_url)} 字符)")

    app_key, app_secret, wt = parse_api_url(api_url)
    if not app_key or not app_secret:
        print(f"  {ERR} 无法从 API URL 解析 appKey/appSecret")
        print(f"  {SKIP} URL 需包含 ?appKey=xxx&appSecret=yyy 参数")
        return 1
    print(f"  {OK} appKey={app_key}")
    print(f"  {OK} 格式={wt}")

    # ── 2. 查剩余量 ──
    print()
    print("── [2] 剩余量检查 ──")
    remaining, err = check_remaining(app_key, app_secret)
    if remaining:
        pct = remaining["pct"]
        pct_str = f"{pct:.1f}%"
        level = OK if pct > 20 else (WARN if pct > 5 else ERR)
        print(f"  {level} 总量: {remaining['total']}")
        print(f"  {level} 剩余: {remaining['remaining']} ({pct_str})")
    else:
        print(f"  {ERR} 查询失败: {err}")
        print(f"  {WARN} 可能原因: appKey/appSecret 错误、应用过期、未绑定白名单IP")

    # ── 3. 测试提取API ──
    print()
    print("── [3] 提取API测试 ──")
    result, err = check_extract_api(api_url)
    if result:
        print(f"  {OK} 成功提取 {result['count']} 个IP")
        print(f"  {OK} 样例: {result['sample']}")
    else:
        print(f"  {ERR} 提取失败: {err}")

    # ── 4. (可选) 代理可用性实测 ──
    do_test = "--all" in sys.argv
    if do_test and result:
        print()
        print("── [4] 代理实测 ──")
        addr = result["sample"]
        print(f"  测试代理: {addr}")
        ok, detail = test_proxy(addr)
        if ok:
            print(f"  {OK} 代理可用! 返回: {detail}")
        else:
            print(f"  {ERR} 代理不可用: {detail}")
            print(f"  {WARN} 可能是IP过期或目标网站屏蔽了代理IP")
    elif result:
        print()
        print(f"  {SKIP} [4] 代理实测跳过 (加 --all 执行)")
    else:
        print()
        print(f"  {SKIP} [4] 代理实测跳过 (API提取失败)")

    # ── 总结 ──
    print()
    print("=" * 56)
    if remaining and result:
        if remaining["pct"] > 20:
            print(f"  {OK} 结论: 代理服务正常，剩余 {remaining['remaining']} 个IP")
        elif remaining["pct"] > 5:
            print(f"  {WARN} 结论: 代理可用，但剩余量不足 ({remaining['remaining']}个)")
            print(f"  {WARN}       建议尽快续费")
        else:
            print(f"  {ERR} 结论: 代理即将用尽 ({remaining['remaining']}/{remaining['total']})")
            print(f"  {ERR}       请立即续费!")
    elif not remaining:
        print(f"  {ERR} 结论: 剩余量查询失败，代理服务可能异常")
    else:
        print(f"  {WARN} 结论: 待补充配置后重试")
    print("=" * 56)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
