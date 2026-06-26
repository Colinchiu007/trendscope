"""热度值归一化模块

不同平台热度值格式各异:
- 微博: "397.6万" → 3976000
- 百度: "3976422" → 3976422
- 知乎: "1000 万热度" → 10000000
- B站: "397.6万" → 3976000

归一化策略: 解析 → 平台内 Z-Score → 跨平台 Min-Max → [0, 100]
"""
import re


def normalize_hot_value(platform_code: str, items: list[dict]) -> list[dict]:
    """将原始热度值解析为数值并做归一化"""
    for item in items:
        raw = str(item.get("hot_value", "0"))
        item["hot_value_raw"] = raw
        item["hot_value_norm"] = parse_hot_value(raw)
    return items


def parse_hot_value(raw: str) -> float:
    """解析中文热度值为数值

    Examples:
        "397.6万" → 3976000
        "1.2亿" → 120000000
        "999+" → 999
        "3976" → 3976
    """
    raw = raw.strip().replace(",", "").replace(" ", "")

    # 亿
    yi_match = re.match(r"([\d.]+)亿", raw)
    if yi_match:
        return float(yi_match.group(1)) * 100000000

    # 万
    wan_match = re.match(r"([\d.]+)万", raw)
    if wan_match:
        return float(wan_match.group(1)) * 10000

    # 数值
    num_match = re.match(r"([\d.]+)", raw)
    if num_match:
        return float(num_match.group(1))

    return 0.0
