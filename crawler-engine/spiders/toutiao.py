"""今日头条热榜爬虫

数据来源: https://www.toutiao.com/hot-event/hot-board/
通过 Playwright 渲染获取数据（页面为 SPA 渲染）。

降级方案: 解析服务端渲染的 HTML 或使用内部 API。
主方案: 使用头条内部 API:
  https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc

API 返回 JSON，页面内嵌在 <script id="RENDER_DATA"> 中。
"""
import json
import re
from datetime import datetime, timezone

import httpx
from spiders.base import BaseSpider


class ToutiaoSpider(BaseSpider):
    platform_code = "toutiao"
    platform_name = "今日头条"
    base_url = "https://www.toutiao.com/hot-event/hot-board/"

    def fetch_trending_list(self) -> list[dict]:
        """通过解析页面内嵌 JSON 获取热榜"""
        response = self._make_request(self.base_url)
        html = response.text
        now = datetime.now(timezone.utc)

        # 提取 <script id="RENDER_DATA" type="application/json">...</script>
        match = re.search(
            r'<script[^>]*id="RENDER_DATA"[^>]*>(.*?)</script>',
            html, re.DOTALL
        )

        if match:
            data_str = match.group(1)
            try:
                decoded = json.loads(json.loads(f'"{data_str}"'))
                hot_board = _extract_hot_board(decoded)
                if hot_board:
                    items = []
                    for idx, item in enumerate(hot_board[:50], 1):
                        title = item.get("Title", "").strip()
                        if not title:
                            continue
                        items.append({
                            "rank": idx,
                            "title": title,
                            "hot_value": str(item.get("HotValue", 0)),
                            "topic_url": item.get("Url", item.get("Schema", "")),
                            "snapshot_at": now.isoformat(),
                            "category": item.get("Tag", "general"),
                        })
                    return items
            except (json.JSONDecodeError, KeyError):
                pass

        # 降级: 返回空，由 base.safe_run 触发 Playwright 降级
        return []


def _extract_hot_board(data: dict) -> list[dict]:
    """从 RENDER_DATA JSON 中提取热榜列表"""
    # RENDER_DATA 结构较深，遍历寻找 hotBoard 数据
    if isinstance(data, list):
        for item in data:
            result = _extract_hot_board(item)
            if result:
                return result
    elif isinstance(data, dict):
        if "hotBoard" in data:
            return data["hotBoard"]
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                result = _extract_hot_board(value)
                if result:
                    return result
    return []
