"""⚠️ 此文件已废弃 — 所有爬虫已迁移至各自独立文件。

保留此文件仅为向后兼容，新代码不应引用此处的类。
实际爬虫实现请直接导入对应模块:
  - from spiders.weibo import WeiboSpider
  - from spiders.douyin import DouyinSpider
  - etc.
"""
# Re-export from independent modules for backward compatibility
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
from spiders.tiktok import TikTokSpider
