"""SMS 验证码登录 API 测试（TDD: RED → GREEN）"""
import sys
import os

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from unittest.mock import AsyncMock, MagicMock

# 模块级 SmsCache（client fixture 和测试用例共享同一个实例）
from trendscope.api.cache.sms_cache import SmsCache
_sms_cache = SmsCache(redis_client=None)


@pytest.fixture
def client():
    """创建 FastAPI TestClient — 使用真实 SmsCache（dict fallback）"""
    from trendscope.api.main import app
    from trendscope.api.dependencies import get_user_service

    # ── mock user repo ──
    mock_user_repo = AsyncMock()

    mock_user = MagicMock()
    mock_user.id = 42
    mock_user.username = "sms_user"
    mock_user.phone = "13800138000"
    mock_user.password_hash = ""
    mock_user.nickname = "SMS User"
    mock_user.role = "user"
    mock_user.status = "active"
    mock_user.created_at = None

    mock_user_repo.find_by_phone.return_value = mock_user

    from trendscope.api.services.user_service import UserService
    svc = UserService(mock_user_repo, sms_cache=_sms_cache)
    svc.repo = mock_user_repo  # bypass UserRepo wrapper for mock
    app.dependency_overrides[get_user_service] = lambda: svc

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
async def clear_sms_cache():
    """每个测试前清理 SMS 缓存"""
    _sms_cache._fallback.clear()
    yield


@pytest.mark.asyncio
async def test_send_sms_code_success(client):
    """发送验证码 — 正常流程"""
    response = await client.post(
        "/api/v1/user/send-sms-code",
        json={"phone": "13800138000"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert data["message"] == "验证码已发送"

    # 验证验证码已存储
    stored_code = await _sms_cache.get_code("13800138000")
    assert stored_code is not None
    assert len(stored_code) == 6
    assert stored_code.isdigit()


@pytest.mark.asyncio
async def test_send_sms_code_invalid_phone(client):
    """发送验证码 — 手机号格式错误"""
    response = await client.post(
        "/api/v1/user/send-sms-code",
        json={"phone": "123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_send_sms_code_missing_phone(client):
    """发送验证码 — 缺少手机号"""
    response = await client.post(
        "/api/v1/user/send-sms-code",
        json={},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_by_sms_success(client):
    """短信登录 — 验证码正确"""
    # 先发送验证码
    await client.post(
        "/api/v1/user/send-sms-code",
        json={"phone": "13800138000"},
    )

    stored_code = await _sms_cache.get_code("13800138000")
    assert stored_code is not None

    response = await client.post(
        "/api/v1/user/login-by-sms",
        json={"phone": "13800138000", "code": stored_code},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "access_token" in data["data"]
    assert "user" in data["data"]
    assert data["data"]["user"]["id"] == 42
    assert data["data"]["user"]["username"] == "sms_user"


@pytest.mark.asyncio
async def test_login_by_sms_wrong_code(client):
    """短信登录 — 验证码错误"""
    # 先发送验证码
    await client.post(
        "/api/v1/user/send-sms-code",
        json={"phone": "13800138000"},
    )

    response = await client.post(
        "/api/v1/user/login-by-sms",
        json={"phone": "13800138000", "code": "000000"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] != 0
    assert "验证码" in data["message"]


@pytest.mark.asyncio
async def test_login_by_sms_expired_code(client):
    """短信登录 — 验证码未发送或已过期"""
    response = await client.post(
        "/api/v1/user/login-by-sms",
        json={"phone": "13900139000", "code": "123456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] != 0
    assert "验证码" in data["message"] or "获取" in data["message"]


@pytest.mark.asyncio
async def test_login_by_sms_unknown_phone(client):
    """短信登录 — 手机号未注册"""
    response = await client.post(
        "/api/v1/user/login-by-sms",
        json={"phone": "13900139000", "code": "123456"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] != 0

