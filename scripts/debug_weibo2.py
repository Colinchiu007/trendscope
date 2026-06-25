"""Debug: compare fresh spider vs direct for weibo"""
import sys; sys.path.insert(0, "crawler-engine")
import httpx

SUBP = "0033WrSXqPxfM725Ws9jqgMF55529P9D9WFp8DfV3b2GTaV0.fDVDN-f"

# Test A: raw httpx.Client with Cookie header
print("Test A: raw client with Cookie header")
hc = httpx.Client(follow_redirects=True, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://weibo.com/",
    "Cookie": "SUBP=" + SUBP,
})
ra = hc.get("https://weibo.com/ajax/side/hotSearch")
print("  Status:", ra.status_code)
print("  Resp headers:", dict(ra.headers))

# Test B: raw httpx.Client NO Cookie header at all (should fail)
print("\nTest B: raw client no cookie")
hc2 = httpx.Client(follow_redirects=True, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://weibo.com/",
})
rb = hc2.get("https://weibo.com/ajax/side/hotSearch")
print("  Status:", rb.status_code)

# Test C: raw client with same client-level headers as spider
print("\nTest C: spider's exact headers in raw client")
hc3 = httpx.Client(follow_redirects=True, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
    "Referer": "https://weibo.com/",
})
rc = hc3.get("https://weibo.com/ajax/side/hotSearch", headers={
    "Accept": "application/json, text/plain, */*",
    "Cookie": "SUBP=" + SUBP,
})
print("  Status:", rc.status_code)
print("  Sent headers:", dict(rc.request.headers))

# Test D: what if the client-level Accept is causing issues?
print("\nTest D: override ALL headers at request level")
hc4 = httpx.Client(follow_redirects=True)
rd = hc4.get("https://weibo.com/ajax/side/hotSearch", headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Referer": "https://weibo.com/",
    "Cookie": "SUBP=" + SUBP,
})
print("  Status:", rd.status_code)
if rd.status_code == 403:
    print("  Body:", rd.text[:300])