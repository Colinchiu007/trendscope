"""微信公众号热文爬虫

数据来源: 搜狗微信搜索 https://weixin.sogou.com/

搜狗微信搜索提供公众号文章搜索，可获取最近热文。
页面结构较复杂，需要通过 HTML 解析提取文章列表。

请求参数:
  - type=2: 文章搜索
  - query=: 可选关键词（不传获取推荐）
  - page=: 页码
"""
import re
import urllib.parse
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from spiders.base import BaseSpider


class WeixinArticleSpider(BaseSpider):
    platform_code = "weixin_article"
    platform_name = "公众号"
    base_url = "https://weixin.sogou.com/weixin"

    def fetch_trending_list(self) -> list[dict]:
        """从搜狗微信搜索获取热文"""
        now = datetime.now(timezone.utc)

        # 1. 先访问首页获取 Cookie
        self._make_request("https://weixin.sogou.com/")

        # 2. 搜索热门关键词获取文章列表
        hot_queries = ["热点", "热搜", "热文", "今日", "最新"]
        all_items = []

        for query in hot_queries[:3]:  # 最多3个关键词避免触发反爬
            params = {
                "type": "2",
                "query": query,
                "ie": "utf8",
            }
            try:
                response = self._make_request(
                    self.base_url,
                    params=params,
                )
                items = self._parse_search_results(response.text, now.isoformat())
                all_items.extend(items)
                if len(all_items) >= 30:
                    break
            except Exception:
                continue

        # 排名去重
        seen = set()
        result = []
        for item in all_items:
            if item["title"] not in seen:
                seen.add(item["title"])
                result.append(item)

        # 重新排名
        for i, item in enumerate(result[:50], 1):
            item["rank"] = i

        return result[:50]

    def _parse_search_results(self, html: str, now_iso: str) -> list[dict]:
        """解析搜狗微信搜索结果 HTML"""
        soup = BeautifulSoup(html, "lxml")
        items = []

        # 文章列表在 <ul class="news-list"> 中的 <li> 标签
        news_list = soup.find("ul", class_="news-list")
        if not news_list:
            # 备选选择器
            news_list = soup.find("ul", class_="news-list2") or soup.find("div", class_="news-box")

        if not news_list:
            return items

        for idx, li in enumerate(news_list.find_all("li"), 1):
            # 提取标题和链接
            title_el = li.find("h3") or li.find("a")
            if not title_el:
                continue

            link = title_el.find("a") or title_el
            title = (link.get_text(strip=True) if link else title_el.get_text(strip=True))
            href = link.get("href", "") if link else ""

            if not title or len(title) < 4:
                continue

            # 提取摘要
            desc_el = li.find("p", class_="txt-info") or li.find("p", class_="re-txt")
            summary = desc_el.get_text(strip=True) if desc_el else ""

            # 提取来源
            source_el = li.find("a", class_="account") or li.find("span", class_="s-p")
            author = source_el.get_text(strip=True) if source_el else ""

            items.append({
                "rank": idx,
                "title": title,
                "hot_value": "0",
                "topic_url": href,
                "snapshot_at": now_iso,
                "category": "article",
                "_article": {
                    "title": title,
                    "summary": summary,
                    "author_name": author,
                    "source_url": href,
                    "read_count": 0,
                    "like_count": 0,
                },
            })

        return items


def _extract_weixin_article_detail(html: str) -> dict:
    """提取公众号文章正文（辅助函数，后续用于深度采集）"""
    soup = BeautifulSoup(html, "lxml")
    content_el = soup.find("div", id="js_content") or soup.find("div", class_="rich_media_content")
    if content_el:
        # 移除隐藏元素
        for hidden in content_el.find_all(style=re.compile(r"display:\s*none")):
            hidden.decompose()
        return {
            "content_text": content_el.get_text("\n", strip=True),
            "images": [
                {"url": img.get("data-src", img.get("src", ""))}
                for img in content_el.find_all("img")
                if img.get("data-src") or img.get("src")
            ],
        }
    return {}
