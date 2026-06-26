"""JWT 认证中间件 — FastAPI 标准 HTTPBearer + python-jose"""
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from trendscope.api.config import settings
from trendscope.api.models.session import get_db
from trendscope.api.repositories.apikey_repo import ApiKeyRepo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# 简化版（后续替换为 shared-models 中的 JWTAuthManager）
try:
    from shared_models.auth import JWTAuthManager  # type: ignore
    _auth_manager = JWTAuthManager()
except ImportError:
    _auth_manager = None


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(user_id: int, username: str, role: str = "user") -> str:
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE)
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """从 HTTPBearer 凭证解析当前用户（纯 JWT 验签，不查 DB）"""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="令牌无效或已过期")


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """要求管理员权限"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


async def verify_api_key(api_key: str, db: AsyncSession) -> dict | None:
    """验证 API Key 并返回 payload（含 key_id, user_id, rate_limit, key_prefix）

    调用方负责从 Header 中提取 X-API-Key 并传入。partner.py 有 FastAPI
    Depends 封装版本，可替代此直接调用。
    """
    if not api_key:
        raise HTTPException(status_code=401, detail={"code": 1003, "message": "缺少 API Key"})

    import hashlib
    repo = ApiKeyRepo(db)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    payload = await repo.validate(key_hash)

    if not payload:
        raise HTTPException(status_code=401, detail={"code": 1003, "message": "API Key 无效或已过期"})

    return payload
