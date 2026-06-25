"""知乎热榜爬虫 - Playwright 方案

数据来源: https://www.zhihu.com/hot
知乎已全面强制登录才能查看热榜（2024年起）。
使用 Playwright + 用户提供的登录 Cookie 方案。

环境变量:
  ZHIHU_COOKIE: 知乎登录后的完整 Cookie 字符串（可选）
  若不配置，爬虫返回空列表并记录提示。
"""
import asyncio
import json
import os
import re
from datetime import datetime, timezone

from spiders.base import BaseSpider


class ZhihuSpider(BaseSpider):
    platform_code = "zhihu"
    platform_name = "知乎"
    base_url = "https://www.zhihu.com/hot"
    use_playwright = True
    requires_auth = True

    def fetch_trending_list(self) -> list[dict]:
        return asyncio.run(self._fetch_with_playwright())

    def _parse_cookies(self, cookie_str: str) -> list[dict]:
        """将 Cookie 字符串解析为 Playwright cookie 列表"""
        cookies = []
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" in part and part.split("=")[0].strip():
                name, value = part.split("=", 1)
                cookies.append({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".zhihu.com",
                    "path": "/",
                })
        return cookies

    async def _fetch_with_playwright(self) -> list[dict]:
        from playwright.async_api import async_playwright
        from anti_anti_spider.fingerprint import FingerprintManager

        cookie_str = os.environ.get("ZHIHU_COOKIE", "")
        if not cookie_str:
            self.logger.warning(
                "ZHIHU_COOKIE 未设置。知乎已强制登录，"
                "请设置环境变量 ZHIHU_COOKIE=你的登录 Cookie"
            )
            return []

        items = []
        async with async_playwright() as p:
            launch_kwargs = FingerprintManager.get_playwright_launch_kwargs()
            browser = await p.chromium.launch(**launch_kwargs)
            context = await browser.new_context(
                viewport=FingerprintManager.get_random_viewport(),
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
            )

            # 注入 stealth 脚本
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                window.chrome = {runtime: {}};
            """)

            # 设置登录 Cookie
            cookies = self._parse_cookies(cookie_str)
            if cookies:
                await context.add_cookies(cookies)

            page = await context.new_page()

            try:
                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)

                # 检查是否被重定向到登录页
                if "signin" in page.url:
                    self.logger.warning("Cookie 已过期或无效，请更新 ZHIHU_COOKIE")
                    await browser.close()
                    return []

                # 从 SSR 内嵌数据提取
                html = await page.content()
                items = self._extract_ssr_data(html)
                if not items:
                    items = await self._extract_from_dom(page)
            except Exception as exc:
                self.logger.error(f"知乎抓取异常: {exc}")
            finally:
                await browser.close()

        return items[:50]

    def _extract_ssr_data(self, html: str) -> list[dict]:
        """从 SSR 内嵌 JSON 中提取热榜"""
        now = datetime.now(timezone.utc).isoformat()
        items = []

        match = re.search(
            r"window\.__INITIAL_STATE__\s*=\s*({.*?});",
            html, re.DOTALL
        )
        if not match:
            return []

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []

        # 知乎 SSR 数据结构: topstory.hotList[]
        hot_list = (
            data.get("topstory", {}).get("hotList", [])
            or data.get("hotList", [])
        )
        if not hot_list:
            return []

        for idx, item in enumerate(hot_list, 1):
            target = item.get("target", item)
            title = target.get("title", "").strip()
            if not title:
                continue

            # 提取热度值
            detail_text = target.get("detail_text", "")
            hot_value = "0"
            if detail_text:
                # "xxx 万热度" → 数值
                num_match = re.search(r"([\d.]+)", detail_text.replace("万", ""))
                if num_match:
                    base = float(num_match.group(1))
                    if "万" in detail_text:
                        base *= 10000
                    hot_value = str(int(base))
                else:
                    hot_value = detail_text

            # 构建话题链接
            question_id = target.get("id", "")
            topic_url = (
                f"https://www.zhihu.com/question/{question_id}"
                if question_id else ""
            )

            items.append({
                "rank": idx,
                "title": title,
                "hot_value": hot_value,
                "topic_url": topic_url,
                "snapshot_at": now,
                "category": _classify(title),
            })

        return items

    async def _extract_from_dom(self, page) -> list[dict]:
        """从 DOM 提取（降级方案）"""
        now = datetime.now(timezone.utc).isoformat()

        js_code = """
        () => {
            const items = [];
            const cards = document.querySelectorAll('.HotList-item');
            cards.forEach((card, idx) => {
                const titleEl = card.querySelector('.HotList-itemTitle a, h2');
                const hotEl = card.querySelector('.HotList-itemHot');
                if (titleEl) {
                    const link = titleEl.getAttribute('href') || '';
                    items.push({
                        rank: idx + 1,
                        title: titleEl.textContent.trim(),
                        hot_value: hotEl ? hotEl.textContent.trim() : '0',
                        url: link.startsWith('/') ? 'https://www.zhihu.com' + link : link
                    });
                }
            });
            return items;
        }
        """
        try:
            dom_items = await page.evaluate(js_code)
            items = []
            for item in dom_items[:50]:
                title = item.get("title", "").strip()
                if not title or len(title) < 2:
                    continue
                items.append({
                    "rank": item.get("rank", 0),
                    "title": title,
                    "hot_value": item.get("hot_value", "0"),
                    "topic_url": item.get("url", ""),
                    "snapshot_at": now,
                    "category": _classify(title),
                })
            return items
        except Exception:
            return []


def _classify(title: str) -> str:
    keywords = {
        "tech": ["AI", "人工智能", "芯片", "5G", "科技", "苹果", "华为", "特斯拉", "手机", "数码"],
        "entertainment": ["电影", "综艺", "明星", "演唱会", "音乐", "游戏", "电视剧"],
        "social": ["政策", "民生", "房价", "教育", "高考", "考研", "就业"],
        "finance": ["股市", "A股", "基金", "经济", "央行", "房价"],
        "sports": ["NBA", "足球", "世界杯", "冠军", "比赛", "奥运"],
    }
    for cat, words in keywords.items():
        for w in words:
            if w.lower() in title.lower():
                return cat
    return "general"
