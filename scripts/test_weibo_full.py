"""Full test: weibo spider fetch_trending_list"""
import sys; sys.path.insert(0, "crawler-engine")
from spiders.weibo import WeiboSpider
spider = WeiboSpider()
items = spider.fetch_trending_list()
print("Got %d items" % len(items))
for item in items[:5]:
    print("  #%d %s - %s [%s]" % (item["rank"], item["title"], item["hot_value"], item["category"]))
spider.close()