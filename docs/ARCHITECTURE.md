# TrendScope（热榜）技术架构文档

> **最后更新**: 2026-06-23 | **版本**: v2（整合版）

## 0. 整合背景

TrendScope 作为"一站式视频生成平台"的新模块接入 `/srv/projects/`。已有平台基于 Python/FastAPI 生态（8 个子项目），TrendScope 技术栈调整为与已有平台对齐，共享 PostgreSQL、Redis、JWT 认证等基础设施。

- **已有平台根目录**: `/srv/projects/`
- **TrendScope 目录**: `/srv/projects/trendscope/`
- **整合方式**: 同机部署 + pip install -e + shared-models 数据契约

## 1. 技术栈

| 层次 | 技术选型 | 版本 | 整合依据 |
|------|---------|------|---------|
| **后端 API** | Python + FastAPI | Python 3.12+ / FastAPI 0.115 | 与已有平台统一语言和框架 |
| **采集引擎** | Python + Celery | Celery 5.4 | 已有 Python 生态 |
| **C 端前端** | Next.js (App Router) + TypeScript | Next.js 14 / React 18 | SEO 优势不可替代（热榜是内容型页面） |
| **管理后台** | Vue 3 + Element Plus | Vue 3.x | 与已有 content-aggregator 管理后台统一 |
| **数据校验** | Pydantic v2 | 已有 shared-models | 统一数据契约，全模块可引用 |
| **ORM** | SQLAlchemy 2.0 (async) | 已有 content-aggregator 在用 | 与已有保持一致 |
| **主数据库** | PostgreSQL 15 | 共享已有实例 | 新 Schema，新表 |
| **缓存** | Redis 7 | 共享已有实例 | 已有基础设施 |
| **任务队列** | Redis (Celery broker) | 共享已有 Redis | 统一消息队列 |
| **对象存储** | 阿里云 OSS | 已有 | 图片/封面图存储 |
| **认证** | JWT (python-jose + passlib/bcrypt) | 复用已有 | 共享密钥，SSO |

## 2. 系统架构

### 2.1 整合架构图

```
/srv/projects/                                 阿里云 ECS (4G→8G)
│
├── platform-orchestrator/   FastAPI :8000  ← 统一入口（已有）
│   │  routers/  ← 新增 trendscope_router
│   │
│   └── trendscope/          FastAPI :8001  ← 新增（可独立或嵌入）
│       ├── api/         API 服务
│       ├── crawler/     采集引擎
│       ├── frontend/    Next.js :3000 (C端SEO)
│       └── admin/       Vue3 SPA (管理后台)
│
├── content-aggregator/      FastAPI + Vue3  ← 已有
├── shared-models/           Pydantic v2     ← 已有 → 新增 trending 模型
├── rpa-common/              ★ 新增共享模块
│   ├── browser_pool.py      (Playwright 池)
│   ├── proxy_manager.py     (代理管理)
│   ├── cookie_manager.py    (Cookie 持久化)
│   └── request_throttle.py  (频率控制)
│
├── Multi-Publish/           发布端  ← 已有
│   └── 引用 rpa-common →
│
├── feature_gates.yaml       ← 已有 → 新增 trending 开关
├── PostgreSQL 15            共享实例（新 Schema: trendscope）
└── Redis 7                  共享实例
```

### 2.2 数据流

**采集流**:
```
Celery Beat 定时触发 → Worker (rpa-common 代理) → 请求目标平台
→ 解析 HTML/API → Pipeline 清洗去重归一化 → PostgreSQL 写入
→ Redis 缓存刷新 → 采集日志
```

**查询流**:
```
用户 → Nginx → Next.js SSR (SEO关键页) / FastAPI (API/管理后台)
→ Redis 缓存命中 → 返回
→ 未命中 → PostgreSQL → 填充 Redis → 返回
```

**管道联动（核心价值）**:
```
TrendScope 发现热点 → trending_to_pipeline: true
→ source_url 送入 content-aggregator
→ AI 改写 → 分句 → 提示词 → 图片 → 视频 → Multi-Publish 发布
```

## 3. 模块设计

### 3.1 Python FastAPI 应用（trendscope/api/）

```
trendscope/
├── setup.py
├── pyproject.toml
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口 + lifespan
│   ├── config.py             # 配置（环境变量 + feature_gates）
│   ├── routers/
│   │   ├── trending.py       # 热榜接口
│   │   ├── articles.py       # 文章接口
│   │   ├── user.py           # 用户接口（JWT）
│   │   ├── admin.py          # 管理后台接口（Admin JWT）
│   │   └── partner.py        # 第三方 API（API Key）
│   ├── services/
│   │   ├── trending_service.py
│   │   ├── article_service.py
│   │   └── user_service.py
│   ├── middleware/
│   │   ├── auth.py           # JWT 认证（复用 python-jose）
│   │   ├── ratelimit.py      # 令牌桶限流
│   │   └── cors.py           # CORS
│   └── models/
│       └── database.py       # SQLAlchemy 模型
├── crawler/
│   └── ...（同原结构）
├── frontend/
│   └── ...（Next.js）
└── admin/
    └── ...（Vue3）
```

### 3.2 rpa-common 共享模块（/srv/projects/rpa-common/）

```
rpa-common/
├── setup.py
├── pyproject.toml
├── rpa_common/
│   ├── __init__.py
│   ├── browser_pool.py       # Playwright 浏览器实例池
│   ├── proxy_manager.py      # 统一代理 IP 管理（芝麻HTTP/快代理）
│   ├── cookie_manager.py     # Cookie 持久化 + 轮换
│   ├── request_throttle.py   # 跨平台请求频率控制
│   └── fingerprint.py        # 浏览器指纹伪装
```

## 4. 数据模型

### 4.1 Pydantic v2 模型（shared-models）

```python
# shared-models/trendscope/models.py
from pydantic import BaseModel
from datetime import datetime

class PlatformModel(BaseModel):
    code: str
    name: str
    icon_url: str | None = None
    category: str = "general"
    is_active: bool = True

class TrendingTopicModel(BaseModel):
    id: int | None = None
    platform_code: str
    rank: int
    title: str
    hot_value: str
    hot_value_norm: float = 0.0
    topic_url: str | None = None
    snapshot_at: datetime

class HotArticleModel(BaseModel):
    id: int | None = None
    platform_code: str
    title: str
    summary: str | None = None
    content_text: str | None = None
    images: list[dict] = []
    source_url: str
    author_name: str | None = None
    read_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    publish_at: datetime | None = None
```

### 4.2 PostgreSQL Schema

与 `scripts/init-db.sql` 保持一致，在已有 PostgreSQL 中以 `trendscope` Schema 或表前缀方式创建。

## 5. 采集策略

### 5.1 平台采集方式

| 平台 | 方式 | 难度 | 频率 | 基类 |
|------|------|------|------|------|
| 微博 | 移动端 API | 中 | 60s (T0) | rpa-common |
| 百度 | HTML 解析 | 低 | 3min (T1) | rpa-common |
| 知乎 | API 接口 | 中 | 3min (T1) | rpa-common |
| Bilibili | API 接口 | 低 | 3min (T1) | rpa-common |
| 今日头条 | Playwright | 高 | 5min (T1) | rpa-common browser_pool |
| 抖音 | Playwright | 高 | 15min (T2) | rpa-common browser_pool |
| 小红书 | App API + Playwright | 高 | 15min (T2) | rpa-common browser_pool |
| YouTube | YouTube Data API v3 | 低 | 15min (T2) | 标准 |
| 公众号 | 搜狗微信搜索 | 中 | 30min (T3) | rpa-common |
| 视频号 | 企业微信 API + Playwright | 极高 | 30min (T3) | rpa-common browser_pool |
| TikTok | Playwright + 境外代理 | 极高 | 1h (T3) | rpa-common browser_pool + proxy |
| X | Twitter API v2 | 低 | 30min (T3) | 标准 |

### 5.2 反爬策略（由 rpa-common 统一提供）

| 层面 | 策略 | 实现 |
|------|------|------|
| IP | 动态住宅 IP 池轮换 | proxy_manager.py |
| 请求头 | UA 轮换池（100+） | fingerprint.py |
| 行为 | 请求间隔随机化 | request_throttle.py |
| 浏览器 | Playwright stealth | browser_pool.py |
| Cookie | 持久化 + 轮换 | cookie_manager.py |

## 6. API 设计

### 6.1 统一响应格式（与已有平台一致）

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "request_id": "req_abc123"
}
```

### 6.2 核心端点

```
公开接口:
  GET  /api/v1/trending
  GET  /api/v1/trending/{platform}
  GET  /api/v1/trending/history?topic_id=&range=
  GET  /api/v1/articles
  GET  /api/v1/articles/{id}
  GET  /api/v1/articles/search?q=
  GET  /api/v1/platforms

用户接口 (JWT):
  POST /api/v1/user/register
  POST /api/v1/user/login
  GET  /api/v1/user/profile

管理后台 (Admin JWT):
  GET  /api/v1/admin/dashboard
  ...

第三方 API (X-API-Key):
  GET  /api/v1/partner/trending
  ...

完整定义见 docs/API_SPEC.md
```

## 7. 部署

### 7.1 开发环境

```bash
# 安装 TrendScope（editable install）
cd /srv/projects/trendscope
pip install -e .

# 安装 rpa-common
cd /srv/projects/rpa-common
pip install -e .

# 启动 API
uvicorn trendscope.api.main:app --reload --port 8001

# 启动采集引擎
celery -A trendscope.crawler.scheduler.celery_app worker -l info

# 启动前端
cd frontend && npm run dev
```

### 7.2 生产环境

```bash
# API
uvicorn trendscope.api.main:app --host 0.0.0.0 --port 8001 --workers 4

# Celery Worker
celery -A trendscope.crawler.scheduler.celery_app worker -l info -c 4

# Next.js
cd frontend && npm run build && npm start
```

Nginx 路由规则：
```
/trending/*  → Next.js :3000 (SEO关键，SSR渲染)
/api/*       → FastAPI :8001 (API)
/admin/*     → Vue3 SPA (管理后台)
```

## 8. 安全

- JWT HS256（与已有平台共享密钥）
- API Key SHA-256 哈希存储
- 全站 HTTPS + HSTS
- 请求限流（令牌桶）
- SQL 注入防护（参数化查询 / ORM）
- XSS 防护（输出编码 + CSP）
- CORS 白名单
