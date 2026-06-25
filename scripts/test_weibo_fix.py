"""Test weibo spider fix on server"""
import sys; sys.path.insert(0, "crawler-engine")
from spiders.weibo import WeiboSpider
spider = WeiboSpider()
try:
    items = spider.fetch_trending_list()
    print(f"SUCCESS: got {len(items)} items")
    for item in items[:5]:
        print("  #%d %s - %s" % (item["rank"], item["title"], item["hot_value"]))
except Exception as e:
    print("FAILED: %s" % e)
    import traceback; traceback.print_exc()