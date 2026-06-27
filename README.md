# TrendScope（热榜）

多平台热榜聚合引擎 — 一站式查看微博、知乎、百度、B站、抖音、小红书等12个平台的热门话题和文章。

**整合为"一站式视频生成平台"的子模块** (`/srv/projects/trendscope/`)，共享已有 PostgreSQL、Redis、JWT 认证等基础设施。

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 API | Python 3.12 + FastAPI |
| 采集引擎 | Python + Celery + Playwright |
| C 端前端 | Next.js 14 + TypeScript（SEO关键页） |
| 管理后台 | Vue 3 + Element Plus |
| 数据契约 | Pydantic v2 (shared-models) |
| 数据库 | PostgreSQL 15（共享已有实例） |
| 缓存 | Redis 7（共享已有实例） |
| 反爬设施 | rpa-common（与 Multi-Publish 共享） |

## 项目结构

```
trendscope/
├── api/                # FastAPI 应用
│   ├── main.py
│   ├── config.py
│   ├── routers/        # trending, articles, user, admin, partner
│   ├── services/       # 业务逻辑层
│   ├── middleware/      # JWT, 限流, CORS
│   └── models/         # SQLAlchemy 模型
├── crawler/            # Python 采集引擎
│   ├── spiders/        # 12个平台爬虫（基于 rpa-common）
│   ├── pipeline/       # 数据清洗去重归一化
│   └── scheduler/      # Celery 调度
├── frontend/           # Next.js C端（SEO页面）
├── admin/              # Vue3 管理后台
├── docs/               # 项目文档
├── scripts/            # 数据库脚本
└── setup.py            # pip install -e
```

## 支持的平台

| 平台 | 代码 | 采集方式 | 状态 |
|------|------|---------|------|
| 微博 | weibo | JSON API | ✅ 已实现 |
| 百度 | baidu | Ajax API | ✅ 已实现 |
| 知乎 | zhihu | JSON API | ✅ 已实现 |
| B站 | bilibili | JSON API | ✅ 已实现 |
| 今日头条 | toutiao | RENDER_DATA JSON | ✅ 已实现 |
| 抖音 | douyin | Playwright | ✅ 已实现 |
| 小红书 | xiaohongshu | Playwright + stealth | ✅ 已实现 |
| YouTube | youtube | YouTube API v3 | ✅ 已实现 |
| X | x_twitter | Twitter API v2 | ✅ 已实现 |
| 公众号 | weixin_article | 搜狗微信搜索 | ✅ 已实现 |
| 视频号 | shipinhao | Playwright (微信UA) | ❌ 未实现 |
| TikTok | tiktok | API + Playwright + 境外代理 | ✅ 已实现 |

## 快速开始

### 前置要求

- Python 3.12+
- Node.js 20+
- PostgreSQL 15 + Redis 7（已有平台共享）

### 安装

```bash
cd /srv/projects/trendscope
pip install -e .
cd /srv/projects/rpa-common
pip install -e .
```

### 启动

```bash
# API
uvicorn trendscope.api.main:app --reload --port 8001

# 采集引擎
celery -A trendscope.crawler.scheduler.celery_app worker -l info

# 前端
cd frontend && npm run dev
```

访问 http://localhost:3000 查看前端页面。

## 文档

- [PRD](docs/PRD.md) — 产品需求文档
- [架构文档](docs/ARCHITECTURE.md) — 技术架构
- [项目计划](docs/PROJECT_PLAN.md) — 实施计划
- [测试计划](docs/TEST_PLAN.md) — 测试策略
- [API 规范](docs/API_SPEC.md) — 接口文档

## License

MIT
