"""Cookie 池管理

为每个平台维护独立的 Cookie 池，定期刷新，模拟真实用户行为。
"""


class CookieManager:
    def __init__(self):
        self._cookies: dict[str, list[dict]] = {}

    def get(self, platform_code: str) -> dict:
        """获取指定平台的 Cookie"""
        pool = self._cookies.get(platform_code, [])
        if not pool:
            return {}
        import random
        return random.choice(pool)

    def add(self, platform_code: str, cookie: dict):
        """添加 Cookie"""
        if platform_code not in self._cookies:
            self._cookies[platform_code] = []
        if cookie not in self._cookies[platform_code]:
            self._cookies[platform_code].append(cookie)

    def refresh(self, platform_code: str):
        """刷新指定平台的 Cookie 池

        NOTE: 当前使用手动配置的 Cookie（通过 init 或 add 方法注入）。
