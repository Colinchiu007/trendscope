"""视频号爬虫

数据来源: 微信视频号（无公开热榜页面）
目前视频号没有公开的热榜页面，使用占位实现。
实际生产环境中可通过以下方式获取：
1. 微信开放平台 API（需企业资质认证）
2. 视频号爬虫（需模拟微信客户端请求，复杂度极高）
3. 第三方数据服务商（如新视、飞瓜数据等）

当前实现返回空列表，记录占位信息。
"""
from datetime import datetime, timezone

from spiders.base import BaseSpider


class WeixinChannelSpider(BaseSpider):
    """视频号爬虫（占位实现）

    视频号目前没有公开热榜页面，因此 fetch_trending_list
    返回空列表。后续可对接第三方 API 服务商获取数据。
    """
    platform_code = "weixin_channel"
    platform_name = "视频号"
    base_url = ""
    use_proxy = True
    use_playwright = False

    def fetch_trending_list(self) -> list[dict]:
        """获取视频号热门内容（当前无公开数据源）

        视频号的热门内容需要通过以下方式之一获取：
        - 微信开放平台视频号相关 API（企业资质）
        - 第三方数据服务商 API
        - 微信客户端协议模拟（高风险，不推荐）

        Returns:
            当前返回空列表，占位标记
        """
        self.logger.warning("[视频号] 无公开热榜数据源，返回空列表")
        return []
