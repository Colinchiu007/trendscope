"""API 集成测试（使用 FastAPI TestClient）"""
import sys
import os

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def client():
    """创建 FastAPI TestClient — 通过 dependency_overrides 提供 mock service"""
    from trendscope.api.main import app
    from trendscope.api.dependencies import get_trending_service, get_article_service, get_user_service

    # ── mock repos ──
    mock_trending_repo = AsyncMock()
    mock_trending_repo.get_platforms.return_value = []
    mock_trending_repo.get_aggregated_trending.return_value = ([], 0)
    mock_trending_repo.get_platform_trending.return_value = ([], 0)
    mock_trending_repo.get_trending_history.return_value = []

    mock_article_repo = AsyncMock()
    mock_article_repo.list_articles.return_value = ([], 0)
    mock_article_repo.get_article.return_value = None
    mock_article_repo.search_articles.return_value = ([], 0)

    mock_user_repo = AsyncMock()

    # ── mock cache（真实 TrendingCache 实例 + None Redis → 全部缓存穿透）──
    from trendscope.api.cache.trending_cache import TrendingCache
    fake_cache = TrendingCache(redis_client=None)

    from trendscope.api.services.trending_service import TrendingService
    from trendscope.api.services.article_service import ArticleService
    from trendscope.api.services.user_service import UserService

    app.dependency_overrides[get_trending_service] = lambda: TrendingService(mock_trending_repo, fake_cache)
    app.dependency_overrides[get_article_service] = lambda: ArticleService(mock_article_repo, fake_cache)
    app.dependency_overrides[get_user_service] = lambda: UserService(mock_user_repo)

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "trendscope"
    assert "version" in data


@pytest.mark.asyncio
async def test_get_trending_empty(client):
    response = await client.get("/api/v1/trending?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "data" in data
    assert "items" in data["data"]
    assert "pagination" in data


@pytest.mark.asyncio
async def test_get_platform_trending(client):
    response = await client.get("/api/v1/trending/weibo")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "items" in data["data"]
    assert data["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_get_platforms(client):
    response = await client.get("/api/v1/trending/platforms")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "platforms" in data["data"]


@pytest.mark.asyncio
async def test_get_articles(client):
    response = await client.get("/api/v1/articles")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "items" in data["data"]


@pytest.mark.asyncio
async def test_search_requires_query(client):
    response = await client.get("/api/v1/articles/search")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_article_not_found(client):
    response = await client.get("/api/v1/articles/99999")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 1002


@pytest.mark.asyncio
async def test_trending_history_requires_topic_id(client):
    response = await client.get("/api/v1/trending/history")
    assert response.status_code == 422


@pytest.mark.asyncio

@pytest.mark.asyncio

@pytest.mark.asyncio
async def test_profile_requires_auth(client):
    response = await client.get("/api/v1/user/profile")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_requires_auth(client):
    response = await client.get("/api/v1/admin/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_partner_requires_api_key(client):
    response = await client.get("/api/v1/partner/trending")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_single_platform_url_routing(client):
    for platform in ["weibo", "zhihu", "baidu", "bilibili", "toutiao"]:
        response = await client.get(f"/api/v1/trending/{platform}")
        assert response.status_code == 200, f"Platform {platform} route failed"


@pytest.mark.asyncio
async def test_response_pagination_format(client):
    response = await client.get("/api/v1/trending?page=2&page_size=15")
    data = response.json()
    pagination = data["pagination"]
    assert pagination["page"] == 2
    assert pagination["page_size"] == 15
    assert "total" in pagination
    assert "total_pages" in pagination
