"""浏览器指纹伪装

Playwright stealth 配置，隐藏自动化特征。
"""


class FingerprintManager:
    """管理浏览器指纹参数"""

    @staticmethod
    def get_playwright_stealth_args() -> list[str]:
        """获取 Playwright 隐身启动参数"""
        return [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ]

    @staticmethod
    def get_random_viewport() -> dict:
        """获取随机视窗大小"""
        import random
        widths = [1366, 1440, 1536, 1600, 1920]
        heights = [768, 900, 864, 900, 1080]
        idx = random.randint(0, len(widths) - 1)
        return {"width": widths[idx], "height": heights[idx]}
