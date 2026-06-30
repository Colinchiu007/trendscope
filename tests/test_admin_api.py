"""管理后台 API 测试（TDD）"""
import sys, os
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from unittest.mock import AsyncMock, MagicMock
from trendscope.api.main import app
from trendscope.api.dependencies import get_user_service, get_db


@pytest.fixture
def admin_headers():
    """模拟管理员 JWT"""
    from trendscope.api.middleware.auth import create_access_token
    token = create_access_token(user_id=1, username="admin", role="admin")
    return {"Authorization": f"Bearer {token}"}


def _make_admin_client():
    """创建 TestClient + mock db + override admin auth"""
    from trendscope.api.middleware.auth import get_current_user
    from trendscope.api.repositories.admin_repo import AdminRepo
    from trendscope.api.repositories.user_repo import UserRepo
    from trendscope.api.repositories.apikey_repo import ApiKeyRepo
    from trendscope.api.repositories.article_repo import ArticleRepo

    app.dependency_overrides.clear()
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": 1, "username": "admin", "role": "admin"
    }

    mock_db = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    return client, mock_db


# ─── 批量审核（Task 18）───

@pytest.mark.asyncio
async def test_batch_audit_success(admin_headers):
    """批量审核 — 正常流程"""
    client, mock_db = _make_admin_client()

    # Mock the execute to return appropriate rowcount
    mock_result = MagicMock()
    mock_result.rowcount = 3
    mock_db.execute.return_value = mock_result

    response = await client.post(
        "/api/v1/admin/articles/batch-audit",
        json={"article_ids": [1, 2, 3], "status": "approved"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["data"]["affected"] == 3


@pytest.mark.asyncio
async def test_batch_audit_invalid_status(admin_headers):
    """批量审核 — 无效状态"""
    client, mock_db = _make_admin_client()
    response = await client.post(
        "/api/v1/admin/articles/batch-audit",
        json={"article_ids": [1, 2, 3], "status": "invalid"},
        headers=admin_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_batch_audit_requires_admin():
    """批量审核 — 非管理员返回 403"""
    from trendscope.api.middleware.auth import get_current_user
    app.dependency_overrides.clear()
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": 2, "username": "user", "role": "user"
    }
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/admin/articles/batch-audit",
            json={"article_ids": [1], "status": "approved"},
            headers={"Authorization": "Bearer some-token"},
        )
        assert resp.status_code == 403


# ─── 用户详情统计（Task 19）───

@pytest.mark.asyncio
async def test_user_stats_success(admin_headers):
    """用户详情统计 — 正常返回"""
    client, mock_db = _make_admin_client()

    result_mock = MagicMock()
    result_mock.scalar.return_value = 5

    async def mock_execute(*args, **kwargs):
        return result_mock
    mock_db.execute = mock_execute

    response = await client.get(
        "/api/v1/admin/users/42/stats",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "favorites_count" in data["data"]


# ─── 采集状态（Task 17）───

@pytest.mark.asyncio
async def test_crawl_status(admin_headers):
    """采集实时状态 — 正常返回"""
    from datetime import datetime, timezone
    client, mock_db = _make_admin_client()

    result_mock = MagicMock()
    now = datetime.now(timezone.utc)
    # 8 columns matching the raw SQL query
    row = (1, "weibo", "微博", "success", 100, None, now, now)
    result_mock.all.return_value = [row]
    mock_db.execute.return_value = result_mock

    response = await client.get(
        "/api/v1/admin/crawl/status",
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert len(data["data"]["items"]) == 1


# ─── Dashboard 统计（已有功能验证）───

@pytest.mark.asyncio
async def test_dashboard_requires_admin():
    """Dashboard — 非管理员返回 403"""
    from trendscope.api.middleware.auth import get_current_user
    app.dependency_overrides.clear()
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": 2, "username": "user", "role": "user"
    }
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": "Bearer some-token"},
        )
        assert resp.status_code == 403
