"""密码修改 & 账号注销 API 测试（TDD: RED → GREEN）"""
import sys
import os

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def auth_headers():
    """模拟 JWT 认证头"""
    from trendscope.api.middleware.auth import create_access_token
    token = create_access_token(user_id=42, username="testuser", role="user")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_user():
    """模拟已认证用户"""
    user = MagicMock()
    user.id = 42
    user.username = "testuser"
    user.phone = "13800138000"
    user.email = "test@example.com"
    user.password_hash = "$2b$12$LJ3m4ys3Lk0TSwHnbfOMiOXPm1Qlq5Gz0E0Y8vQ0C0A0B0C0D0E0F0G0H"  # fake hash
    user.nickname = "TestUser"
    user.role = "user"
    user.status = "active"
    user.avatar_url = ""
    user.created_at = None
    return user


def _make_client(override_current_user=None):
    """创建 TestClient，可选择性注入 mock user"""
    from trendscope.api.main import app
    from trendscope.api.dependencies import get_user_service
    from trendscope.api.middleware.auth import get_current_user

    mock_user_repo = AsyncMock()
    app.dependency_overrides.clear()

    if override_current_user:
        app.dependency_overrides[get_current_user] = lambda: override_current_user

    from trendscope.api.services.user_service import UserService
    svc = UserService(mock_user_repo)
    svc.repo = mock_user_repo
    app.dependency_overrides[get_user_service] = lambda: svc

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    return client, svc, mock_user_repo


# ─── 密码修改 ───

@pytest.mark.asyncio
async def test_password_change_success(auth_headers, mock_user):
    """密码修改 — 正常流程（旧密码正确 → 修改成功）"""
    from trendscope.api.middleware.auth import hash_password, verify_password

    mock_user.password_hash = hash_password("OldPass123")
    client, svc, repo = _make_client(override_current_user={
        "user_id": mock_user.id,
        "username": mock_user.username,
        "role": mock_user.role,
    })

    # Mock find_by_id to return the user
    repo.find_by_id.return_value = mock_user
    repo.update_user.return_value = mock_user

    response = await client.put(
        "/api/v1/user/password",
        json={"old_password": "OldPass123", "new_password": "NewPass456"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["message"] == "密码修改成功"


@pytest.mark.asyncio
async def test_password_change_wrong_old_password(auth_headers, mock_user):
    """密码修改 — 旧密码错误"""
    from trendscope.api.middleware.auth import hash_password

    mock_user.password_hash = hash_password("RealOldPass")
    client, svc, repo = _make_client(override_current_user={
        "user_id": mock_user.id,
        "username": mock_user.username,
        "role": mock_user.role,
    })
    repo.find_by_id.return_value = mock_user

    response = await client.put(
        "/api/v1/user/password",
        json={"old_password": "WrongOldPass", "new_password": "NewPass456"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] != 0
    assert "旧密码" in data["message"]


@pytest.mark.asyncio
async def test_password_change_short_new_password(auth_headers, mock_user):
    """密码修改 — 新密码太短"""
    from trendscope.api.middleware.auth import hash_password

    mock_user.password_hash = hash_password("OldPass123")
    client, svc, repo = _make_client(override_current_user={
        "user_id": mock_user.id,
        "username": mock_user.username,
        "role": mock_user.role,
    })
    repo.find_by_id.return_value = mock_user

    response = await client.put(
        "/api/v1/user/password",
        json={"old_password": "OldPass123", "new_password": "123"},
        headers=auth_headers,
    )
    assert response.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_password_change_requires_auth():
    """密码修改 — 未认证返回 401"""
    client, svc, repo = _make_client()
    response = await client.put(
        "/api/v1/user/password",
        json={"old_password": "OldPass123", "new_password": "NewPass456"},
    )
    assert response.status_code == 401


# ─── 账号注销 ───

@pytest.mark.asyncio
async def test_delete_account_success(auth_headers, mock_user):
    """账号注销 — 正常流程"""
    client, svc, repo = _make_client(override_current_user={
        "user_id": mock_user.id,
        "username": mock_user.username,
        "role": mock_user.role,
    })
    repo.find_by_id.return_value = mock_user
    repo.update_user.return_value = mock_user

    response = await client.delete(
        "/api/v1/user/account",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0


@pytest.mark.asyncio
async def test_delete_account_requires_auth():
    """账号注销 — 未认证返回 401"""
    client, svc, repo = _make_client()
    response = await client.delete("/api/v1/user/account")
    assert response.status_code == 401


# ─── 邮箱注册验证 ───

@pytest.mark.asyncio
async def test_send_email_code_success(client=None):
    """发送邮箱验证码 — 正常流程"""
    from trendscope.api.main import app
    from trendscope.api.dependencies import get_user_service
    from trendscope.api.cache.sms_cache import SmsCache

    sms_cache = SmsCache(redis_client=None)
    sms_cache._fallback.clear()

    mock_repo = AsyncMock()
    from trendscope.api.services.user_service import UserService
    svc = UserService(mock_repo, sms_cache=sms_cache)
    svc.repo = mock_repo
    app.dependency_overrides.clear()
    app.dependency_overrides[get_user_service] = lambda: svc

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as cl:
        response = await cl.post(
            "/api/v1/user/send-email-code",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "验证码已发送"

        stored = await sms_cache.get_code("email:test@example.com")
        assert stored is not None
        assert len(stored) == 6


@pytest.mark.asyncio
async def test_send_email_code_invalid_email():
    """发送邮箱验证码 — 邮箱格式错误"""
    from trendscope.api.main import app
    from trendscope.api.dependencies import get_user_service
    from trendscope.api.cache.sms_cache import SmsCache

    sms_cache = SmsCache(redis_client=None)
    mock_repo = AsyncMock()
    from trendscope.api.services.user_service import UserService
    svc = UserService(mock_repo, sms_cache=sms_cache)
    svc.repo = mock_repo
    app.dependency_overrides.clear()
    app.dependency_overrides[get_user_service] = lambda: svc

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as cl:
        response = await cl.post(
            "/api/v1/user/send-email-code",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_with_email_success():
    """邮箱注册 — 验证码正确 → 注册成功"""
    from trendscope.api.main import app
    from trendscope.api.dependencies import get_user_service
    from trendscope.api.cache.sms_cache import SmsCache

    sms_cache = SmsCache(redis_client=None)
    sms_cache._fallback.clear()
    code = sms_cache.generate_code()
    await sms_cache.set_code("email:newuser@example.com", code)

    mock_repo = AsyncMock()
    mock_repo.find_by_username.return_value = None
    mock_repo.find_by_email.return_value = None

    mock_user = MagicMock()
    mock_user.id = 99
    mock_user.username = "newuser"
    mock_user.role = "user"
    mock_repo.create_user.return_value = mock_user

    from trendscope.api.services.user_service import UserService
    svc = UserService(mock_repo, sms_cache=sms_cache)
    svc.repo = mock_repo
    app.dependency_overrides.clear()
    app.dependency_overrides[get_user_service] = lambda: svc

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as cl:
        response = await cl.post(
            "/api/v1/user/register",
            json={
                "username": "newuser",
                "password": "Password123",
                "email": "newuser@example.com",
                "email_code": code,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == 99


@pytest.mark.asyncio
async def test_register_with_email_wrong_code():
    """邮箱注册 — 验证码错误"""
    from trendscope.api.main import app
    from trendscope.api.dependencies import get_user_service
    from trendscope.api.cache.sms_cache import SmsCache

    sms_cache = SmsCache(redis_client=None)
    sms_cache._fallback.clear()
    await sms_cache.set_code("email:newuser@example.com", "654321")

    mock_repo = AsyncMock()
    from trendscope.api.services.user_service import UserService
    svc = UserService(mock_repo, sms_cache=sms_cache)
    svc.repo = mock_repo
    app.dependency_overrides.clear()
    app.dependency_overrides[get_user_service] = lambda: svc

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as cl:
        response = await cl.post(
            "/api/v1/user/register",
            json={
                "username": "newuser",
                "password": "Password123",
                "email": "newuser@example.com",
                "email_code": "000000",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 0
        assert "验证码" in data["message"]


@pytest.mark.asyncio
async def test_register_with_email_expired_code():
    """邮箱注册 — 验证码过期"""
    from trendscope.api.main import app
    from trendscope.api.dependencies import get_user_service
    from trendscope.api.cache.sms_cache import SmsCache

    sms_cache = SmsCache(redis_client=None)
    sms_cache._fallback.clear()

    mock_repo = AsyncMock()
    from trendscope.api.services.user_service import UserService
    svc = UserService(mock_repo, sms_cache=sms_cache)
    svc.repo = mock_repo
    app.dependency_overrides.clear()
    app.dependency_overrides[get_user_service] = lambda: svc

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as cl:
        response = await cl.post(
            "/api/v1/user/register",
            json={
                "username": "newuser",
                "password": "Password123",
                "email": "newuser@example.com",
                "email_code": "123456",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 0
        assert "验证码" in data["message"] or "获取" in data["message"]


@pytest.mark.asyncio
async def test_register_duplicate_username():
    """邮箱注册 — 用户名已存在"""
    from trendscope.api.main import app
    from trendscope.api.dependencies import get_user_service
    from trendscope.api.cache.sms_cache import SmsCache

    sms_cache = SmsCache(redis_client=None)
    sms_cache._fallback.clear()
    code = sms_cache.generate_code()
    await sms_cache.set_code("email:dup@example.com", code)

    mock_repo = AsyncMock()
    mock_repo.find_by_username.return_value = MagicMock()  # already exists
    mock_repo.find_by_email.return_value = None

    from trendscope.api.services.user_service import UserService
    svc = UserService(mock_repo, sms_cache=sms_cache)
    svc.repo = mock_repo
    app.dependency_overrides.clear()
    app.dependency_overrides[get_user_service] = lambda: svc

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as cl:
        response = await cl.post(
            "/api/v1/user/register",
            json={
                "username": "existing_user",
                "password": "Password123",
                "email": "dup@example.com",
                "email_code": code,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 0
