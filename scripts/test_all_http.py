"""Comprehensive spider test - run on server"""
import sys; sys.path.insert(0, "crawler-engine")
from spiders import get_spider
from loguru import logger

# Remove loguru's default handler so we control output
logger.remove()
logger.add(lambda msg: None)  # silent

results = {}

def test(code):
    print("[%s] Testing..." % code)
    spider = get_spider(code)
    try:
        items = spider.fetch_trending_list()
        print("[%s] OK - %d items" % (code, len(items)))
        for item in items[:2]:
            r, t = item["rank"], item["title"]
            print("       #%d %s" % (r, t[:50]))
        results[code] = ("OK", len(items))
    except Exception as e:
        msg = str(e).split("\n")[0][:80]
        print("[%s] FAIL - %s" % (code, msg))
        results[code] = ("FAIL", msg)
    finally:
        spider.close()

# HTTP spiders (fast)
for code in ["weibo", "baidu", "bilibili"]:
    test(code)

print("\n" + "="*50)
print("RESULTS:")
for code, (status, detail) in results.items():
    sym = "PASS" if status == "OK" else "FAIL"
    print("  %s: %s (%s)" % (code.ljust(15), sym, detail))
