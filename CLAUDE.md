# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

TrendScope（热榜）是多平台热榜聚合引擎，作为一站式视频生成平台的数据输入源。从 12 个平台采集热门话题和文章，通过 API 对外提供结构化热榜数据，并可联动 content-aggregator 管道自动将热点送入 AI 改写→视频生成的完整流程。

## 架构

```
用户端                          管理端                      第三方
Next.js 14 SSR (:3000)    Vue 3 + Element Plus    API Key + HTTP
      │                         │                      │
      └──────────┬──────────────┴──────────────────────┘
                 │
          FastAPI (:8001)              ┌─ Celery Beat (定时调度)
     routers/ services/ repos/         ├─ Celery Workers (采集)
          │        │       │           └─ spiders/ (12个爬虫)
     PostgreSQL ← Redis 缓存 ← crawler pipeline (清洗/去重/归一化)
```

数据流: **Celery Beat 触发 → Worker 调用 Spider → Pipeline 处理 → PG 写入 → Redis 刷新 → API 返回 / 管道联动**

## 目录结构

```
trendscope/
├── trendscope/api/          # FastAPI 应用
│   ├── main.py              # 入口 + CORS + 安全中间件
│   ├── dependencies.py      # FastAPI Depends 注入链
│   ├── config.py            # 配置 (环境变量)
│   ├── routers/             # trending, articles, user, admin, partner
│   ├── services/            # trending_svc, article_svc, user_svc
│   ├── repositories/        # trending_repo, article_repo, user_repo, apikey_repo, admin_repo
│   ├── models/              # database.py (SQLAlchemy), session.py
│   ├── middleware/           # auth (JWT), security (CSP/HSTS), ratelimit (令牌桶)
│   ├── cache/               # trending_cache (Redis 4级缓存)
│   └── pipeline/            # bridge.py (→ content-aggregator)
├── crawler-engine/          # 采集引擎 (独立 Python 脚本)
│   ├── scheduler/           # celery_app, beat_schedule, tasks
│   ├── spiders/             # base + 12 平台爬虫
│   ├── pipeline/            # cleaner → deduplicator → normalizer → writer
│   ├── anti_anti_spider/    # proxy_pool, fingerprint, cookie_manager, request_throttle
│   └── models/              # schema.py (SQLAlchemy 独立)
├── frontend/                # Next.js 14 C端
│   └── src/
│       ├── app/             # page, layout, trending/[platform], article/[id], search
│       │   └── user/        # login, register, (app)/profile, favorites, subscriptions
│       ├── components/      # TrendingCard, HotList, ArticleCard, JsonLd
│       ├── hooks/           # useTrending, useArticles, useAuth
│       └── lib/             # api-client (axios+拦截器), auth (JWT存储), types
├── admin/                   # Vue 3 管理后台 (src/views: Dashboard, Platforms, Articles, Users, ApiKeys)
├── tests/                   # pytest + pytest-asyncio (56 用例)
├── scripts/                 # init-db.sql, k6-load-test.js, smoke-test.sh
└── deploy/                  # docker-compose.yml, nginx.conf, start.sh, stop.sh
```

## 关键约定

### 依赖注入链

Router 通过 FastAPI `Depends` 注入 Service，Service 注入 Repository + Cache:

```
Router → Depends(get_trending_service) → TrendingService(Repo, Cache)
Router → Depends(get_article_service)  → ArticleService(Repo, Cache)
Router → Depends(get_user_service)     → UserService(Repo)
```

在 `dependencies.py` 中注册，不要绕过这条链直接访问数据库。

### 数据库操作

- **异步 SQLAlchemy 2.0** (`select(...).where(...)`)
- Repository 层封装所有查询，不要在 Router 或 Service 中写 SQL
- 每个请求自动 commit/rollback（见 `models/session.py` 的 `get_db`）
- PostgreSQL 全文检索用 `to_tsvector('simple', ...)` + `plainto_tsquery`

### Redis 缓存

4 级缓存 TTL:
| 缓存 | Key | TTL |
|------|-----|-----|
| 聚合热榜 | `trendscope:trending:agg:{category}:{page}:{page_size}` | 60s |
| 单平台热榜 | `trendscope:trending:plat:{platform}:{page}:{page_size}` | 120s |
| 文章详情 | `trendscope:article:{id}` | 600s |
| 平台列表 | `trendscope:platforms` | 3600s |

采集完成后必须调用 `cache.invalidate(platform_code)` 刷新。

### API 响应格式

```json
{"code": 0, "message": "success", "data": {...},
 "pagination": {"page": 1, "page_size": 20, "total": N, "total_pages": M}}
```

错误码: `0=成功, 1001=参数错误, 1002=资源不存在, 1003=未认证, 1004=无权限, 1005=频率限制, 1006=重复操作`

### 12 平台爬虫

在 `crawler-engine/spiders/` 下。每个爬虫继承 `BaseSpider`，实现 `fetch_trending_list() → list[dict]`。

标准化 dict 格式: `{rank, title, hot_value, topic_url, snapshot_at, category, _article?}`

注册新爬虫: 在 `spiders/__init__.py` 的 `SPIDER_MAP` 中添加映射。

采集频率分级: T0=60s(微博) / T1=3-5min / T2=15min / T3=30min-1h

### 管道联动

`trendscope/api/pipeline/bridge.py` 实现 TrendScope → content-aggregator 管道桥接。
- 受 `trending_to_pipeline` 功能开关控制
- 优先进程内调用 (import content_aggregator)，失败降级 HTTP
- 在 Celery task 中采集完毕时触发

## 常用命令

```bash
# 安装
pip install -e .

# API
uvicorn trendscope.api.main:app --reload --port 8001

# 采集引擎
celery -A trendscope.crawler.celery_app worker -l info -c 4
celery -A trendscope.crawler.celery_app beat -l info

# 前端
cd frontend && npm run dev

# 测试
pytest tests/ -v --asyncio-mode=auto

# Smoke test
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/trending
curl http://localhost:8001/api/v1/trending/platforms

# 压测
k6 run scripts/k6-load-test.js
```

## 环境变量

见 `trendscope/api/.env.example`。关键变量: `PO_SECRET_KEY`(JWT密钥, 与orchestrator共享), `TS_DB_*`(PostgreSQL), `YOUTUBE_API_KEY`, `TWITTER_BEARER_TOKEN`, `TIKTOK_PROXY_URL`, `FEATURE_GATES_PATH`
