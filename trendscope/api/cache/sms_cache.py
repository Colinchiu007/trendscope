"""SMS 验证码缓存 — Redis 存储验证码，Redis 不可用时降级为 dict fallback"""
import random
import string

from loguru import logger

# 缓存 Key 前缀
KEY_PREFIX = "trendscope:sms"

# 默认 TTL（5 分钟）
DEFAULT_TTL = 300


class SmsCache:
    """短信验证码存储与校验

    支持 Redis 和本地 dict 两种存储后端：
    - 有 Redis 时优先使用 Redis（带 TTL 过期）
    - Redis 不可用时自动降级到 _fallback dict（测试环境、无 Redis 时）
    """

    def __init__(self, redis_client=None):
        self.rdb = redis_client
        self._fallback: dict[str, str] = {}

    # ─── 内部 key 生成 ───

    @staticmethod
    def _make_key(phone: str) -> str:
        return f"{KEY_PREFIX}:{phone}"

    @staticmethod
    def generate_code(length: int = 6) -> str:
        """生成纯数字验证码"""
        return "".join(random.choices(string.digits, k=length))

    # ─── 核心操作 ───

    async def set_code(self, phone: str, code: str, ttl: int = DEFAULT_TTL) -> None:
        """存储验证码"""
        key = self._make_key(phone)
        if self.rdb:
            try:
                await self.rdb.setex(key, ttl, code)
                logger.debug(f"[SmsCache] 验证码已存入 Redis: {phone}")
                return
            except Exception as e:
                logger.warning(f"[SmsCache] Redis 写入失败，降级到 fallback: {e}")
        self._fallback[key] = code
        logger.debug(f"[SmsCache] 验证码已存入 fallback: {phone}")

    async def get_code(self, phone: str) -> str | None:
        """获取验证码"""
        key = self._make_key(phone)
        if self.rdb:
            try:
                val = await self.rdb.get(key)
                if val is not None:
                    return val
            except Exception as e:
                logger.warning(f"[SmsCache] Redis 读取失败，降级到 fallback: {e}")
        return self._fallback.get(key)

    async def delete_code(self, phone: str) -> None:
        """删除验证码（校验成功后调用）"""
        key = self._make_key(phone)
        if self.rdb:
            try:
                await self.rdb.delete(key)
            except Exception as e:
                logger.warning(f"[SmsCache] Redis 删除失败: {e}")
        self._fallback.pop(key, None)
