"""Test HTTP-based spiders on server"""
import sys; sys.path.insert(0, "crawler-engine")
from spiders import get_spider

for code in ["weibo", "baidu", "bilibili"]:
    print("="*40)
    print("Testing %s..." % code)
    try:
        spider = get_spider(code)
        items = spider.fetch_trending_list()
        print("  OK - %d items" % len(items))
        for item in items[:3]:
            print("    #%d %s [%s]" % (item["rank"], item["title"][:40], item.get("category", "")))
        spider.close()
    except Exception as e:
        print("  FAIL - %s" % e)
print("="*40)
print("HTTP spider tests done")