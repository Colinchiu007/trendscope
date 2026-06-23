"""代理 IP 池管理

对接代理服务商 API，维护可用 IP 池，自动轮换和健康检查。
"""


class ProxyPool:
    def __init__(self):
        self._proxies: list[str] = []
        self._index = 0

    def get(self) -> str:
        """获取一个代理"""
        if not self._proxies:
            return ""
        proxy = self._proxies[self._index % len(self._proxies)]
        self._index += 1
        return proxy

    def add(self, proxy: str):
        """添加代理"""
        if proxy not in self._proxies:
            self._proxies.append(proxy)

    def remove(self, proxy: str):
        """移除失效代理"""
        if proxy in self._proxies:
            self._proxies.remove(proxy)

    def check_health(self):
        """健康检查"""
        # TODO: 检查每个代理的可用性，移除超时/不可用的
        pass

    def fetch_from_provider(self):
        """从代理服务商获取新 IP"""
        # TODO: 对接芝麻HTTP / 快代理 API
        pass
