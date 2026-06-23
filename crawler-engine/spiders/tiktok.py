"""TikTok 热门视频爬虫

数据来源: TikTok Trending API / Playwright 渲染

方案1（优先）: TikTok 非官方 API 端点
  - https://www.tiktok.com/api/trending/item_list/
  - 需要境外 IP + 特定 User-Agent + msToken 参数

方案2（降级）: Playwright 渲染 + 境外代理
  - https://www.tiktok.com/trending

TikTok 有极强的反爬机制（msToken 签名、设备注册），
需要配合境外代理使用。

环境变量: TIKTOK_PROXY_URL (境外代理地址)
"""
import asyncio
import os
from datetime import datetime, timezone

from spiders.base import BaseSpider


class TikTokSpider(BaseSpider):
    platform_code = "tiktok"
    platform_name = "TikTok"
    base_url = "https://www.tiktok.com"
    use_playwright = True

    def __init__(self):
        super().__init__()
        self.proxy_url = os.getenv("TIKTOK_PROXY_URL", "")

    def fetch_trending_list(self) -> list[dict]:
        # 优先尝试 API
        try:
            return self._fetch_via_api()
        except Exception:
            pass

        # 降级：Playwright
        return asyncio.run(self._fetch_with_playwright())

    def _fetch_via_api(self) -> list[dict]:
        """尝试 TikTok 非官方 API"""
        import httpx
        now = datetime.now(timezone.utc).isoformat()

        api_url = "https://www.tiktok.com/api/trending/item_list/"
        params = {
            "aid": 1988,
            "app_name": "tiktok_web",
            "device_platform": "web",
            "count": 50,
        }

        # TikTok 需要特定的 msToken 签名
        # 这里使用公开的默认 token，实际生产需要动态获取
        headers = {
            **self._build_headers(),
            "Referer": "https://www.tiktok.com/trending",
        }

        response = httpx.get(
            api_url,
            params=params,
            headers=headers,
            timeout=15,
        )

        if response.status_code != 200:
            raise Exception(f"API 返回 {response.status_code}")

        data = response.json()
        items = []
        for idx, item in enumerate(data.get("items", [])[:50], 1):
            title = item.get("desc", item.get("title", "")).strip()
            if not title:
                continue
            stats = item.get("stats", {})
            author = item.get("author", {})

            items.append({
                "rank": idx,
                "title": title[:120],
                "hot_value": str(stats.get("playCount", 0)),
                "topic_url": f"https://www.tiktok.com/@{author.get('uniqueId', '')}/video/{item.get('id', '')}",
                "snapshot_at": now,
                "category": "video",
                "_article": {
                    "title": title[:120],
                    "summary": title,
                    "author_name": author.get("nickname", ""),
                    "author_avatar": author.get("avatarMedium", ""),
                    "source_url": f"https://www.tiktok.com/@{author.get('uniqueId', '')}/video/{item.get('id', '')}",
                    "read_count": stats.get("playCount", 0),
                    "like_count": stats.get("diggCount", 0),
                    "comment_count": stats.get("commentCount", 0),
                    "share_count": stats.get("shareCount", 0),
                },
            })

        return items[:50]

    async def _fetch_with_playwright(self) -> list[dict]:
        """Playwright 渲染方案（境外代理）"""
        from playwright.async_api import async_playwright
        from anti_anti_spider.fingerprint import FingerprintManager

        items = []
        async with async_playwright() as p:
            launch_opts = {"headless": True, "args": ["--no-sandbox"]}
            if self.proxy_url:
                launch_opts["proxy"] = {"server": self.proxy_url}

            browser = await p.chromium.launch(**launch_opts)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=self.ua.random,
                locale="en-US",
                timezone_id="America/New_York",
            )
            page = await context.new_page()

            try:
                await page.goto(
                    f"{self.base_url}/trending",
                    wait_until="networkidle",
                    timeout=30000,
                )
                await asyncio.sleep(3)

                # 从页面提取视频数据
                items = await self._extract_tiktok_items(page)
            except Exception:
                pass
            finally:
                await browser.close()

        return items[:50]

    async def _extract_tiktok_items(self, page) -> list[dict]:
        """从 TikTok 页面提取视频列表"""
        now = datetime.now(timezone.utc).isoformat()

        # TikTok 的视频数据通常在 script 标签中
        js_code = """
        () => {
            try {
                const sigiState = window.SIGI_STATE || window.__INIT_PROPS__ || {};
                const itemList = sigiState?.ItemList || sigiState?.itemList || {};
                return Object.values(itemList).slice(0, 50).map((item, idx) => ({
                    rank: idx + 1,
                    title: item.desc || '',
                    author: item.author?.nickname || '',
                    play_count: item.stats?.playCount || 0,
                    like_count: item.stats?.diggCount || 0,
                    video_id: item.id || '',
                    author_id: item.author?.uniqueId || '',
                }));
            } catch(e) { return []; }
        }
        """
        try:
            js_items = await page.evaluate(js_code)
            items = []
            for i in js_items:
                title = i.get("title", "").strip()
                if not title:
                    continue
                items.append({
                    "rank": i.get("rank", 0),
                    "title": title[:120],
                    "hot_value": str(i.get("play_count", 0)),
                    "topic_url": f"https://www.tiktok.com/@{i.get('author_id', '')}/video/{i.get('video_id', '')}",
                    "snapshot_at": now,
                    "category": "video",
                    "_article": {
                        "title": title[:120],
                        "author_name": i.get("author", ""),
                        "source_url": f"https://www.tiktok.com/@{i.get('author_id', '')}/video/{i.get('video_id', '')}",
                        "read_count": i.get("play_count", 0),
                        "like_count": i.get("like_count", 0),
                    },
                })
            return items
        except Exception:
            return []
