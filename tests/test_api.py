"""API 集成测试（使用 FastAPI TestClient）"""
import sys
import os

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def client():
    """创建 FastAPI TestClient（Mock DB + Redis）"""
    # Mock 掉数据库和 Redis 依赖
    with patch("trendscope.api.models.session.async_session", autospec=True), \
         patch("trendscope.api.dependencies.get_db", autospec=True), \
         patch("trendscope.api.dependencies.get_redis", autospec=True):

        from trendscope.api.main import app
        from httpx import AsyncClient, ASGITransport

        transport = ASGITransport(app=app)
        client = AsyncClient(transport=transport, base_url="http://test")
        yield client


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
    # 缺少 q 参数应返回校验错误
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_article_not_found(client):
    response = await client.get("/api/v1/articles/99999")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 1002  # 资源不存在


@pytest.mark.asyncio
async def test_trending_history_requires_topic_id(client):
    response = await client.get("/api/v1/trending/history")
    assert response.status_code == 422  # 缺少必填参数


@pytest.mark.asyncio
async def test_register_validation(client):
    response = await client.post("/api/v1/user/register", json={
        "username": "ab",  # 太短
        "password": "123",  # 太短
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_missing_account(client):
    response = await client.post("/api/v1/user/login", json={
        "account": "",
        "password": "",
    })
    # FastAPI 校验 minimum length
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_profile_requires_auth(client):
    response = await client.get("/api/v1/user/profile")
    assert response.status_code == 401  # 未认证


@pytest.mark.asyncio
async def test_admin_requires_auth(client):
    response = await client.get("/api/v1/admin/dashboard")
    assert response.status_code == 401  # JWT 中间件拦截


@pytest.mark.asyncio
async def test_partner_requires_api_key(client):
    response = await client.get("/api/v1/partner/trending")
    assert response.status_code == 401  # API Key 中间件拦截


@pytest.mark.asyncio
async def test_single_platform_url_routing(client):
    """确保 /{platform} 路由正确匹配"""
    # 已实现的平台
    for platform in ["weibo", "zhihu", "baidu", "bilibili", "toutiao"]:
        response = await client.get(f"/api/v1/trending/{platform}")
        assert response.status_code == 200, f"Platform {platform} route failed"


@pytest.mark.asyncio
async def test_response_pagination_format(client):
    """分页响应格式验证"""
    response = await client.get("/api/v1/trending?page=2&page_size=15")
    data = response.json()
    pagination = data["pagination"]
    assert pagination["page"] == 2
    assert pagination["page_size"] == 15
    assert "total" in pagination
    assert "total_pages" in pagination
