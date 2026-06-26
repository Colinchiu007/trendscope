#!/bin/bash
# TrendScope API Smoke Test
# 用法: bash scripts/smoke-test.sh [BASE_URL]
set -e

BASE_URL="${1:-http://localhost:8001}"

echo "=== TrendScope Smoke Test ==="
echo "Target: $BASE_URL"
echo ""

pass=0
fail=0

check() {
  local desc="$1"
  local method="$2"
  local url="$3"
  local expected_code="$4"
  local data="$5"

  if [ -n "$data" ]; then
    resp=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" -H "Content-Type: application/json" -d "$data")
  else
    resp=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url")
  fi

  if [ "$resp" = "$expected_code" ]; then
    echo "  ✅ $desc ($resp)"
    pass=$((pass + 1))
  else
    echo "  ❌ $desc (expected $expected_code, got $resp)"
    fail=$((fail + 1))
  fi
}

# Health
check "Health Check"        GET "$BASE_URL/health"                         200

# Public APIs
check "聚合热榜"             GET "$BASE_URL/api/v1/trending?page=1&page_size=10" 200
check "单平台热榜"           GET "$BASE_URL/api/v1/trending/weibo?page=1"   200
check "平台列表"             GET "$BASE_URL/api/v1/trending/platforms"      200
check "文章列表"             GET "$BASE_URL/api/v1/articles?page=1"         200
check "热度趋势"             GET "$BASE_URL/api/v1/trending/history?topic_id=1&range=24h" 200
check "搜索(缺少q)"          GET "$BASE_URL/api/v1/articles/search"         422

# User APIs (require auth → 401)
check "Profile(未认证)"      GET "$BASE_URL/api/v1/user/profile"            401
check "Favorites(未认证)"    GET "$BASE_URL/api/v1/user/favorites"          401

# Register validation
check "注册(参数过短)"        POST "$BASE_URL/api/v1/user/register"          422 \
  '{"username":"ab","password":"12"}'

# Login validation
check "登录(空账号)"          POST "$BASE_URL/api/v1/user/login"            422 \
  '{"account":"","password":""}'

# Admin (require auth → 401)
check "Dashboard(未认证)"    GET "$BASE_URL/api/v1/admin/dashboard"        401

# Partner (require X-API-Key → 401)
check "Partner(无Key)"       GET "$BASE_URL/api/v1/partner/trending"       401

echo ""
echo "=== Results: $pass passed, $fail failed ==="
[ "$fail" -eq 0 ] && echo "✅ All smoke tests passed!" || echo "❌ Some tests failed"
