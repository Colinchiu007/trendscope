"""JWT 认证中间件 — 复用已有平台 python-jose + passlib"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from trendscope.api.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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


def get_current_user(authorization: str = Header(None)) -> dict:
    """从 Authorization Header 解析当前用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少认证令牌")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="认证格式错误")

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


def verify_api_key(api_key: str) -> str:
    """验证 API Key，返回 key_prefix（后续对接数据库）"""
    if not api_key:
        raise HTTPException(status_code=401, detail="缺少 API Key")
    # TODO: 查询数据库验证 key_hash
    return api_key[:16]
