# trendscope — 测试规范

## TDD 流程

```
RED   → 在 tests/ 下写失败测试
         API 测试：TestClient 模拟请求
         服务层测试：mock repository
         爬虫测试：scripts/test_*.py（不纳入 CI）
GREEN → 最小实现让测试通过
REFACTOR → 重构，保持测试通过
```

### 测试组织

```
tests/
+-- conftest.py          # 共享 fixture（async_client, db_session）
+-- test_api.py          # API 端点测试
+-- test_services.py     # 服务层测试
+-- test_pipeline.py     # 管道测试（CI 中排除）

scripts/
+-- test_all_http.py     # 全量 HTTP 爬虫集成测试
+-- test_http_spiders.py # HTTP 爬虫专项测试
```

### 测试规范

```python
# tests/test_api.py
async def test_trending_returns_data(async_client):
    resp = await async_client.get("/api/v1/trending")
    assert resp.status_code == 200
    assert resp.json()["code"] == 0

# tests/test_services.py
async def test_get_trending_calls_cache_and_repo(trending_service, mock_cache, mock_repo):
    result = await trending_service.get_trending("weibo")
    assert mock_cache.get.called
    assert mock_repo.get.called
```

