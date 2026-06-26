"""令牌桶限流中间件 — Redis 分布式限流"""
import time
import hashlib

from fastapi import HTTPException, Request

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None


class RedisTokenBucket:
    """基于 Redis 的分布式令牌桶限流器"""

    def __init__(self, redis_client=None, prefix: str = "trendscope:ratelimit"):
        self.rdb = redis_client
        self.prefix = prefix

    async def consume(self, key: str, rate: int = 100, burst: int = 20) -> bool:
        """消费一个令牌

        Args:
            key: 限流标识 (如 user_id, ip, api_key_prefix)
            rate: 每分钟限额
            burst: 突发容量
        """
        redis_key = f"{self.prefix}:{key}"

        if self.rdb:
            return await self._redis_consume(redis_key, rate, burst)
        else:
            return self._local_consume(redis_key, rate, burst)

    async def _redis_consume(self, key: str, rate: int, burst: int) -> bool:
        """Redis 滑动窗口限流"""
        now = time.time()
        window = 60  # 1分钟窗口

        try:
            async with self.rdb.pipeline() as pipe:
                # 移除过期成员
                pipe.zremrangebyscore(key, 0, now - window)
                # 获取当前窗口请求数
                pipe.zcard(key)
                # 添加当前请求
                pipe.zadd(key, {str(now): now})
                # 设置过期时间
                pipe.expire(key, window + 1)
                results = await pipe.execute()

            current_count = results[1]
            return current_count < rate
        except Exception:
            return True  # Redis故障时放行

    # 本地兜底（无 Redis 时使用）
    _local_buckets: dict = {}

    def _local_consume(self, key: str, rate: int, burst: int) -> bool:
        now = time.time()
        bucket = self._local_buckets.get(key, {"tokens": burst, "last": now})
        elapsed = now - bucket["last"]
        bucket["tokens"] = min(burst, bucket["tokens"] + elapsed * (rate / 60.0))
        bucket["last"] = now

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            self._local_buckets[key] = bucket
            return True
        return False


# 全局限流器
_limiter = RedisTokenBucket()


async def rate_limit(request: Request, rate: int = 100):
    """请求限流依赖"""
    # 使用 IP + 路径作为 key
    ip = request.client.host if request.client else "unknown"
    path = request.url.path
    key = hashlib.md5(f"{ip}:{path}".encode()).hexdigest()[:16]

    if not await _limiter.consume(key, rate=rate):
        raise HTTPException(status_code=429, detail={"code": 1005, "message": "请求过于频繁，请稍后再试"})


def set_redis_client(redis_client):
    """设置 Redis 客户端（用于分布式限流）"""
    global _limiter
    _limiter = RedisTokenBucket(redis_client)
