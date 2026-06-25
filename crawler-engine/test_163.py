"""Explore 163.com hot data sources"""
import requests, json, re

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Approach 1: Check news.163.com for embedded data
print("=== news.163.com ===")
r = requests.get("https://news.163.com/", timeout=10, headers=headers)
html = r.text
print("Length: %d" % len(html))

# Look for data in script tags
scripts = re.findall(r"<script[^>]*>(.{100,500})</script>", html, re.DOTALL)
for i, s in enumerate(scripts[:10]):
    lower = s.lower()
    if any(w in lower for w in ["hot", "rank", "trend", "list", "news", "data"]):
        print("Script %d (len=%d): %s..." % (i, len(s), s[:200]))

# Look for JSON patterns
json_patterns = re.findall(r"window\.__NUXT__\s*=\s*({.*?});", html, re.DOTALL)
for jp in json_patterns[:2]:
    print("NUXT found, len=%d: %s..." % (len(jp), jp[:300]))

# Approach 2: Try 163.com main page
print("\n=== 163.com ===")
r2 = requests.get("https://www.163.com/", timeout=10, headers=headers)
print("Length: %d" % len(r2.text))
api_calls = re.findall(r'https?://[^"\\s]*api[^"\\s]*', r2.text)
print("API calls found: %d" % len(api_calls))
for a in api_calls[:5]:
    print("  %s" % a)