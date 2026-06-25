"""Debug weibo 403 - compare raw client vs spider client"""
import sys; sys.path.insert(0, "crawler-engine")
import httpx

# Test 1: raw httpx.Client (should work)
print("="*50)
print("Test 1: raw httpx.Client")
hc = httpx.Client(follow_redirects=True)
hc.cookies.set("SUBP", "0033WrSXqPxfM725Ws9jqgMF55529P9D9WFp8DfV3b2GTaV0.fDVDN-f", domain=".weibo.com", path="/")
r1 = hc.get("https://weibo.com/ajax/side/hotSearch", headers={
    "Referer": "https://weibo.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
})
print(f"  Status: {r1.status_code}")
print(f"  Cookies in jar: {list(hc.cookies)}")
if r1.status_code == 200:
    data = r1.json()
    realtime = data.get("data", {}).get("realtime", [])
    print(f"  Items: {len(realtime)}")
    for item in realtime[:3]:
        print(f"    #{item.get('rank')} {item.get('word')}")
else:
    print(f"  Body: {r1.text[:200]}")

# Test 2: use the spider's http_client with direct .get() instead of _make_request
print()
print("="*50)
print("Test 2: spider http_client + direct .get()")
from spiders.weibo import WeiboSpider
spider = WeiboSpider()
# Get the client (creates it with spider's default headers)
hc2 = spider.http_client
# Set cookie directly
hc2.cookies.set("SUBP", "0033WrSXqPxfM725Ws9jqgMF55529P9D9WFp8DfV3b2GTaV0.fDVDN-f", domain=".weibo.com", path="/")
r2 = hc2.get("https://weibo.com/ajax/side/hotSearch", headers={
    "Referer": "https://weibo.com/",
    "Accept": "application/json, text/plain, */*",
})
print(f"  Status: {r2.status_code}")
print(f"  Request headers: {dict(r2.request.headers)}")
if r2.status_code == 200:
    data = r2.json()
    realtime = data.get("data", {}).get("realtime", [])
    print(f"  Items: {len(realtime)}")
else:
    print(f"  Body: {r2.text[:300]}")

# Test 3: spider http_client via _make_request
print()
print("="*50)
print("Test 3: spider http_client + _make_request with Cookie header")
r3 = spider._make_request("https://weibo.com/ajax/side/hotSearch", headers={
    "Referer": "https://weibo.com/",
    "Accept": "application/json, text/plain, */*",
    "Cookie": "SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFp8DfV3b2GTaV0.fDVDN-f",
})
print(f"  Status: {r3.status_code}")
if r3.status_code == 200:
    data = r3.json()
    realtime = data.get("data", {}).get("realtime", [])
    print(f"  Items: {len(realtime)}")

spider.close()
