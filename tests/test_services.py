"""Service 层单元测试（Mock DB + Redis）"""
import sys
import os

# 确保 trendscope 包可导入
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


# ─── TrendingService 测试 ───

class TestTrendingService:
    @pytest.fixture
    def mock_repo(self):
        repo = AsyncMock()
        repo.get_platforms.return_value = []
        repo.get_aggregated_trending.return_value = ([], 0)
        repo.get_platform_trending.return_value = ([], 0)
        repo.get_trending_history.return_value = []
        repo.get_platform_by_code.return_value = None
        return repo

    @pytest.fixture
    def mock_cache(self):
        cache = AsyncMock()
        cache.get_aggregated.return_value = None
        cache.get_platform_trending.return_value = None
        cache.get_platforms.return_value = None
        return cache

    @pytest.fixture
    def service(self, mock_repo, mock_cache):
        from trendscope.api.services.trending_service import TrendingService
        return TrendingService(mock_repo, mock_cache)

    @pytest.mark.asyncio
    async def test_get_platforms_from_cache(self, service, mock_cache):
        mock_cache.get_platforms.return_value = [{"code": "weibo", "name": "微博"}]
        result = await service.get_platforms()
        assert len(result) == 1
        assert result[0]["code"] == "weibo"

    @pytest.mark.asyncio
    async def test_get_platforms_from_db(self, service, mock_repo, mock_cache):
        mock_cache.get_platforms.return_value = None
        from unittest.mock import MagicMock

        platform = MagicMock()
        platform.id = 1
        platform.code = "weibo"
        platform.name = "微博"
        platform.icon_url = ""
        platform.category = "social"
        platform.is_active = True

        mock_repo.get_platforms.return_value = [platform]

        result = await service.get_platforms()
        assert len(result) == 1
        assert result[0]["code"] == "weibo"
        mock_cache.set_platforms.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_aggregated_empty(self, service, mock_repo):
        mock_repo.get_aggregated_trending.return_value = ([], 0)
        items, total = await service.get_aggregated()
        assert items == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_aggregated_with_default_page(self, service, mock_repo):
        """默认 page=1 page_size=20"""
        await service.get_aggregated()
        mock_repo.get_aggregated_trending.assert_called_with(
            platform_ids=None, category="all", page=1, page_size=20
        )

    @pytest.mark.asyncio
    async def test_get_platform_trending_empty(self, service, mock_repo):
        mock_repo.get_platform_trending.return_value = ([], 0)
        items, total = await service.get_platform_trending("weibo")
        assert items == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_history_returns_format(self, service, mock_repo):
        from unittest.mock import MagicMock

        topic = MagicMock()
        topic.title = "测试话题"
        topic.platform = MagicMock()
        topic.platform.code = "weibo"
        topic.hot_value_norm = 95.0
        topic.rank = 1
        topic.snapshot_at = datetime.now(timezone.utc)

        mock_repo.get_trending_history.return_value = [topic]
        result = await service.get_history(1, "24h")

        assert result["topic_id"] == 1
        assert result["title"] == "测试话题"
        assert result["platform"] == "weibo"
        assert len(result["history"]) == 1


# ─── UserService 密码测试 ───

class TestPasswordHashing:
    def test_hash_and_verify(self):
        from trendscope.api.middleware.auth import hash_password, verify_password

        password = "MySecurePass123!"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)

    def test_different_passwords_generate_different_hashes(self):
        from trendscope.api.middleware.auth import hash_password

        h1 = hash_password("pass1")
        h2 = hash_password("pass2")
        assert h1 != h2

    def test_same_password_generates_different_hash(self):
        from trendscope.api.middleware.auth import hash_password

        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        # bcrypt 生成不同的盐值，所以哈希不同但都能验证
        assert h1 != h2


# ─── 响应格式测试 ───

class TestResponseModel:
    def test_unified_response_structure(self):
        """确保 API 响应格式统一"""
        response = {
            "code": 0,
            "message": "success",
            "data": {"items": []},
            "pagination": {"page": 1, "page_size": 20, "total": 0, "total_pages": 0},
        }
        assert "code" in response
        assert "message" in response
        assert response["code"] == 0
        assert "pagination" in response
        assert response["pagination"]["page"] == 1
        assert response["pagination"]["page_size"] == 20

    def test_error_response_structure(self):
        response = {
            "code": 1001,
            "message": "参数错误",
        }
        assert response["code"] != 0
        assert "message" in response

    def test_pagination_calculation(self):
        """验证分页计算逻辑"""
        total = 50
        page_size = 20
        total_pages = (total + page_size - 1) // page_size
        assert total_pages == 3

        total = 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        assert total_pages == 0


# ─── JWT Token 测试 ───

class TestJWTToken:
    def test_create_and_decode_token(self):
        from trendscope.api.middleware.auth import create_access_token, decode_token

        token = create_access_token(user_id=1, username="testuser", role="user")

        payload = decode_token(token)
        assert payload["user_id"] == 1
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        from trendscope.api.middleware.auth import decode_token
        from jose import JWTError

        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_empty_token(self):
        from trendscope.api.middleware.auth import decode_token
        from jose import JWTError

        with pytest.raises(JWTError):
            decode_token("")
