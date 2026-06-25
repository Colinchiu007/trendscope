"""浏览器指纹伪装

Playwright stealth 配置，隐藏自动化特征。
"""
import os


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
    def get_chromium_executable() -> str | None:
        """自动查找 Chromium 可执行文件路径"""
        candidates = [
            os.path.expanduser("~/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome"),
            os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-1223/chrome-headless-shell-linux64/chrome-headless-shell"),
        ]
        for path in candidates:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        return None

    @staticmethod
    def get_playwright_launch_kwargs() -> dict:
        """获取完整的 Playwright launch 参数字典"""
        kwargs = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-setuid-sandbox"],
        }
        exec_path = FingerprintManager.get_chromium_executable()
        if exec_path:
            kwargs["executable_path"] = exec_path
        return kwargs

    @staticmethod
    def get_random_viewport() -> dict:
        """获取随机视窗大小"""
        import random
        widths = [1366, 1440, 1536, 1600, 1920]
        heights = [768, 900, 864, 900, 1080]
        idx = random.randint(0, len(widths) - 1)
        return {"width": widths[idx], "height": heights[idx]}
