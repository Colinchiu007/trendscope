"""
last30days 多源搜索服务 — TrendScope 集成版

移植自 content-aggregator/_archive_v1 last30days_collector.py，
移除 BaseCollector 依赖，作为独立服务模块供 API 直接使用。

支持的源（零配置免费）：
  - Reddit: 公开 JSON API
  - Hacker News: Algolia API
  - GitHub: Issues + Repos 搜索（60 req/h 未认证）
  - Polymarket: Gamma API

设计原则：
  1. 零配置即可用
  2. 所有网络错误优雅降级（返回空列表）
  3. log10 归一化跨平台互动数据，RRF 融合排序
  4. 支持 freshness 衰减（近 30 天增益）
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from datetime import datetime, timezone
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_SOURCES = ["reddit", "hackernews", "github", "polymarket"]

ENGAGEMENT_NORMALIZERS: dict[str, tuple[str, float]] = {
    "reddit":     ("upvotes", 5.0),
    "github":     ("stars", 5.0),
    "hackernews": ("points", 5.0),
    "polymarket": ("volume", 100000.0),
}

SOURCE_LABELS: dict[str, str] = {
    "reddit":     "Reddit",
    "hackernews": "Hacker News",
    "github":     "GitHub",
    "polymarket": "Polymarket",
}

SOURCE_FETCHERS: dict[str, Callable] = {}


# ── Scoring ──────────────────────────────────────────────────────────────────


def normalize_engagement(source: str, engagement: dict[str, Any]) -> float:
    """Normalize raw engagement metrics to a 0-1 score (log10 scale)."""
    normalizer = ENGAGEMENT_NORMALIZERS.get(source)
    if normalizer is None:
        return 0.0
    raw_field, divisor = normalizer
    raw_value = engagement.get(raw_field, 0) or 0
    if source == "polymarket":
        return min(raw_value / divisor, 1.0)
    if isinstance(raw_value, (int, float)) and raw_value > 0:
        return min(math.log10(raw_value + 1) / divisor, 1.0)
    return 0.0


def compute_freshness_score(published_at: datetime | None, days_back: int = 30) -> float:
    """Compute a freshness score (0-1) based on how recent the item is."""
    if published_at is None:
        return 0.5
    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_days = (now - published_at).total_seconds() / 86400.0
    if age_days <= 0:
        return 1.0
    if age_days >= days_back:
        return 0.0
    return 1.0 - (age_days / days_back)


def rrf_score(rank: int, k: int = 60) -> float:
    """Reciprocal Rank Fusion score."""
    return 1.0 / (k + rank)


# ── Source Fetchers ──────────────────────────────────────────────────────────


async def _fetch_reddit(client: httpx.AsyncClient, topic: str, limit: int = 12) -> list[dict]:
    """Search Reddit via public JSON API."""
    url = "https://www.reddit.com/search.json"
    params = {"q": topic, "limit": limit, "sort": "top", "t": "month", "raw_json": 1}
    headers = {
        "User-Agent": "TrendScope/1.0 (last30days integration)",
        "Accept": "application/json",
    }
    try:
        response = await client.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    items = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        created = datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc)
        items.append({
            "item_id": f"reddit-t3_{post.get('id', '')}",
            "source": "reddit",
            "source_label": "Reddit",
            "title": post.get("title", "") or "",
            "body": (post.get("selftext", "") or "")[:500],
            "url": f"https://reddit.com{post.get('permalink', '')}",
            "author": post.get("author", "") or "",
            "published_at": created.isoformat(),
            "engagement": {
                "upvotes": post.get("ups", 0),
                "comments": post.get("num_comments", 0),
            },
            "container": post.get("subreddit_name_prefixed", ""),
            "thumbnail": (
                post.get("thumbnail", "")
                if post.get("thumbnail", "").startswith("http")
                else None
            ),
        })
    return items


async def _fetch_hackernews(client: httpx.AsyncClient, topic: str, limit: int = 12) -> list[dict]:
    """Search Hacker News via Algolia API."""
    url = "https://hn.algolia.com/api/v1/search"
    params = {
        "query": topic, "hitsPerPage": limit, "tags": "story",
        "numericFilters": "created_at_i>" + str(int(time.time()) - 30 * 86400),
    }
    try:
        response = await client.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    items = []
    for hit in data.get("hits", []):
        created = datetime.fromtimestamp(hit.get("created_at_i", 0), tz=timezone.utc)
        items.append({
            "item_id": f"hn-{hit.get('objectID', '')}",
            "source": "hackernews",
            "source_label": "Hacker News",
            "title": hit.get("title", "") or "",
            "body": (hit.get("story_text", "") or hit.get("comment_text", "") or "")[:500],
            "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
            "author": hit.get("author", "") or "",
            "published_at": created.isoformat(),
            "engagement": {
                "points": hit.get("points", 0),
                "comments": hit.get("num_comments", 0),
            },
            "container": "Hacker News",
        })
    return items


async def _fetch_github(client: httpx.AsyncClient, topic: str, limit: int = 12) -> list[dict]:
    """Search GitHub Issues and Repositories (rate-limited: 60 req/h unauthenticated)."""
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "TrendScope/1.0"}

    async def _search_issues() -> list[dict]:
        url = "https://api.github.com/search/issues"
        params = {"q": f"{topic} is:public", "sort": "reactions", "order": "desc", "per_page": min(limit, 10)}
        try:
            resp = await client.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json().get("items", [])
        except Exception:
            return []

    async def _search_repos() -> list[dict]:
        url = "https://api.github.com/search/repositories"
        params = {"q": topic, "sort": "stars", "order": "desc", "per_page": min(limit, 10)}
        try:
            resp = await client.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json().get("items", [])
        except Exception:
            return []

    issue_items, repo_items = await asyncio.gather(
        asyncio.create_task(_search_issues()),
        asyncio.create_task(_search_repos()),
    )

    items = []
    for issue in issue_items:
        created = (
            datetime.fromisoformat(issue.get("created_at", "").replace("Z", "+00:00"))
            if issue.get("created_at") else None
        )
        repo_full = issue.get("repository_url", "").replace("https://api.github.com/repos/", "")
        items.append({
            "item_id": f"github-issue-{issue.get('id', '')}",
            "source": "github",
            "source_label": "GitHub",
            "title": issue.get("title", "") or "",
            "body": (issue.get("body", "") or "")[:500],
            "url": issue.get("html_url", ""),
            "author": issue.get("user", {}).get("login", "") if issue.get("user") else "",
            "published_at": created.isoformat() if created else None,
            "engagement": {"stars": issue.get("score", 0), "comments": issue.get("comments", 0)},
            "container": repo_full or "GitHub",
        })
    for repo in repo_items:
        created = (
            datetime.fromisoformat(repo.get("created_at", "").replace("Z", "+00:00"))
            if repo.get("created_at") else None
        )
        items.append({
            "item_id": f"github-repo-{repo.get('id', '')}",
            "source": "github",
            "source_label": "GitHub",
            "title": f"{repo.get('full_name', '')}: {repo.get('description', '') or ''}",
            "body": (repo.get("description", "") or "")[:500],
            "url": repo.get("html_url", ""),
            "author": repo.get("owner", {}).get("login", "") if repo.get("owner") else "",
            "published_at": created.isoformat() if created else None,
            "engagement": {"stars": repo.get("stargazers_count", 0), "comments": repo.get("open_issues_count", 0)},
            "container": repo.get("full_name", ""),
        })
    return items


async def _fetch_polymarket(client: httpx.AsyncClient, topic: str, limit: int = 12) -> list[dict]:
    """Search Polymarket events via Gamma API."""
    url = "https://gamma-api.polymarket.com/events"
    params = {"tag": topic, "limit": limit, "closed": "false", "sort": "volume", "order": "desc"}
    try:
        response = await client.get(url, params=params, timeout=10)
        response.raise_for_status()
        events = response.json()
    except Exception:
        # Fallback: search by title
        params.pop("tag", None)
        params["title"] = topic
        try:
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()
            events = response.json()
        except Exception:
            return []

    items = []
    for event in events:
        start_date_str = event.get("start_date") or event.get("created_at", "")
        created = None
        if start_date_str:
            try:
                created = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            except Exception:
                pass
        outcomes = event.get("outcomes", [])
        volume = sum(float(o.get("volume", 0) or 0) for o in outcomes)
        yes_prob = next(
            (float(o.get("price", 0) or 0) for o in outcomes if o.get("outcome", "").lower() == "yes"),
            None,
        )
        items.append({
            "item_id": f"polymarket-{event.get('id', '')}",
            "source": "polymarket",
            "source_label": "Polymarket",
            "title": event.get("title", "") or "",
            "body": event.get("description", "") or "",
            "url": f"https://polymarket.com/event/{event.get('slug', '')}",
            "author": event.get("creator", {}).get("username", "") if event.get("creator") else "",
            "published_at": created.isoformat() if created else None,
            "engagement": {"volume": volume, "yes_probability": yes_prob},
            "container": event.get("category", "Polymarket"),
        })
    return items


# ── Register Fetchers ───────────────────────────────────────────────────────

SOURCE_FETCHERS["reddit"] = _fetch_reddit
SOURCE_FETCHERS["hackernews"] = _fetch_hackernews
SOURCE_FETCHERS["github"] = _fetch_github
SOURCE_FETCHERS["polymarket"] = _fetch_polymarket


# ── Main Search Function ─────────────────────────────────────────────────────


async def search_multi_source(
    query: str,
    sources: list[str] | None = None,
    per_source: int = 12,
    total_max: int = 50,
    days_back: int = 30,
) -> dict:
    """Execute multi-source search and return fused results.

    Args:
        query: Search keywords.
        sources: Enabled sources (default: all 4 free sources).
        per_source: Max results per source.
        total_max: Max total results after fusion.
        days_back: Freshness decay window.

    Returns:
        dict with keys:
            query: Original query.
            sources: List of sources that returned results.
            total: Total result count.
            results: Fused and sorted result items.
            by_source: Results grouped by source.
            errors: Per-source error messages.
    """
    if not query or not query.strip():
        return {"query": query, "sources": [], "total": 0, "results": [], "by_source": {}, "errors": {}}

    enabled = sources or DEFAULT_SOURCES
    valid = [s for s in enabled if s in SOURCE_FETCHERS]

    if not valid:
        return {"query": query, "sources": [], "total": 0, "results": [], "by_source": {}, "errors": {}}

    async with httpx.AsyncClient() as client:
        tasks: dict[str, asyncio.Task] = {}
        for src in valid:
            fetcher = SOURCE_FETCHERS[src]
            tasks[src] = asyncio.create_task(
                _safe_fetch(fetcher, client, query, per_source),
            )

        all_results: dict[str, list[dict]] = {}
        errors: dict[str, str] = {}
        for src, task in tasks.items():
            try:
                all_results[src] = await task
            except Exception as e:
                errors[src] = str(e)
                all_results[src] = []

    # Score and fuse
    flat: list[dict] = []
    for src, items in all_results.items():
        for rank, item in enumerate(items, start=1):
            pub_date = _parse_datetime(item.get("published_at"))
            eng_score = normalize_engagement(src, item.get("engagement", {}))
            fresh_score = compute_freshness_score(pub_date, days_back)
            rr = rrf_score(rank)
            relevance_score = max(0, 1.0 - (rank - 1) * 0.02)
            final = 0.35 * rr + 0.25 * relevance_score + 0.20 * fresh_score + 0.20 * eng_score
            item["engagement_score"] = round(eng_score, 4)
            item["_score"] = round(final, 4)
            flat.append(item)

    # Dedup
    seen_ids: set[str] = set()
    deduped: list[dict] = []
    for item in sorted(flat, key=lambda x: x["_score"], reverse=True):
        iid = item.get("item_id", "")
        if iid and iid in seen_ids:
            continue
        if iid:
            seen_ids.add(iid)
        item.pop("_score", None)
        deduped.append(item)

    results = deduped[:total_max]

    # Group by source for frontend
    by_source: dict[str, list[dict]] = {}
    for item in results:
        src = item.get("source", "unknown")
        by_source.setdefault(src, []).append(item)

    return {
        "query": query,
        "sources": list(all_results.keys()),
        "total": len(results),
        "results": results,
        "by_source": by_source,
        "errors": errors,
    }


async def _safe_fetch(fetcher: Callable, client: httpx.AsyncClient, topic: str, limit: int) -> list[dict]:
    try:
        return await fetcher(client, topic, limit)
    except Exception as e:
        logger.warning(f"[last30days] Source fetch error: {e}")
        return []


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            pass
    return None
