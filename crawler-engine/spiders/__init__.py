"""平台爬虫模块"""
from spiders.base import BaseSpider
from spiders.weibo import WeiboSpider
from spiders.baidu import BaiduSpider
from spiders.zhihu import ZhihuSpider
from spiders.bilibili import BilibiliSpider
from spiders.toutiao import ToutiaoSpider
from spiders.douyin import DouyinSpider
from spiders.xiaohongshu import XiaohongshuSpider
from spiders.youtube import YouTubeSpider
from spiders.x_twitter import XTwitterSpider
from spiders.weixin_article import WeixinArticleSpider
from spiders.shipinhao import ShipinhaoSpider
from spiders.tiktok import TikTokSpider

SPIDER_MAP = {
    "weibo": WeiboSpider,
    "baidu": BaiduSpider,
    "zhihu": ZhihuSpider,
    "bilibili": BilibiliSpider,
    "toutiao": ToutiaoSpider,
    "douyin": DouyinSpider,
    "xiaohongshu": XiaohongshuSpider,
    "youtube": YouTubeSpider,
    "x_twitter": XTwitterSpider,
    "weixin_article": WeixinArticleSpider,
    "shipinhao": ShipinhaoSpider,
    "tiktok": TikTokSpider,
}


def get_spider(platform_code: str) -> BaseSpider:
    spider_cls = SPIDER_MAP.get(platform_code)
    if spider_cls is None:
        return None
    return spider_cls()
