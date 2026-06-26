"""请求频率控制

实现令牌桶算法，控制每个平台的请求频率。
"""
import time
from collections import defaultdict


class RequestThrottle:
    def __init__(self):
        self._last_request: dict[str, float] = defaultdict(float)

    def wait(self, platform_code: str, min_interval: float = 10, max_interval: float = 60):
        """等待直到可以发起下一次请求"""
        import random
        elapsed = time.time() - self._last_request.get(platform_code, 0)
        interval = random.uniform(min_interval, max_interval)

        if elapsed < interval:
            time.sleep(interval - elapsed)

        self._last_request[platform_code] = time.time()

    def should_throttle(self, platform_code: str, min_interval: float = 10) -> bool:
        """检查是否需要限速"""
        elapsed = time.time() - self._last_request.get(platform_code, 0)
        return elapsed < min_interval
