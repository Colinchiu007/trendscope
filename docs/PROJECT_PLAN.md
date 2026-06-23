# TrendScope（热榜）项目计划 v2（整合版）

## 项目概述

- **项目名称**: TrendScope（热榜）
- **项目代号**: trendscope
- **整合位置**: `/srv/projects/trendscope/`（一站式视频生成平台子模块）
- **项目周期**: ~11 周（整合后比独立开发节省 ~30%）
- **团队规模**: 2-3 人（后端全栈×1、前端×1、PM×1）

## 里程碑

```
Week 1     ██ Phase 0: 基础设施
Week 2-4   ██████ Phase 1: MVP 热榜展示
Week 5-6   ████ Phase 2: 用户系统 + 扩展平台
Week 7-8   ████ Phase 3: 管理后台 + API 商业化
Week 9-11  ██████ Phase 4: 优化与上线
```

---

## Phase 0: 基础设施调整（第 1 周）

### 目标
废弃 Go 代码，建立 Python/FastAPI 骨架，接入已有基础设施。

### 任务列表

| 编号 | 任务 | 工期 | 输出 |
|------|------|------|------|
| P0-1 | 废弃 api-gateway/ Go 代码，创建 trendscope/ Python 包 | 0.5天 | setup.py + pyproject.toml |
| P0-2 | 在 shared-models 中定义 TrendScope Pydantic v2 模型 | 1天 | shared-models/trendscope/ |
| P0-3 | 已有 PostgreSQL 中执行 init-db.sql | 0.5天 | 表结构 |
| P0-4 | 创建 rpa-common 共享模块骨架 | 1天 | 代理/指纹/浏览器池 |
| P0-5 | 在 feature_gates.yaml 添加 trending 开关 | 0.5天 | 配置 |
| P0-6 | FastAPI 应用骨架（routers + middleware + config） | 1天 | 可启动 |
| P0-7 | 更新架构文档、项目计划、README | 0.5天 | 文档 |

### 验收标准
- [ ] `pip install -e /srv/projects/trendscope/` 成功
- [ ] `uvicorn trendscope.api.main:app --port 8001` 可启动
- [ ] `from shared_models.trendscope import TrendingTopicModel` 可导入
- [ ] `/health` 端点返回 200

---

## Phase 1: MVP 热榜展示（第 2-4 周）

### W1-2: 采集引擎 + API

| 编号 | 任务 | 工期 | 输出 |
|------|------|------|------|
| P1-1 | BaseSpider 基类（基于 rpa-common） | 0.5天 | base.py |
| P1-2 | 微博热搜爬虫 | 1.5天 | weibo.py |
| P1-3 | 百度热搜爬虫 | 1天 | baidu.py |
| P1-4 | 知乎热榜爬虫 | 1.5天 | zhihu.py |
| P1-5 | B站热门爬虫 | 1天 | bilibili.py |
| P1-6 | 今日头条爬虫（Playwright） | 1.5天 | toutiao.py |
| P1-7 | 数据管道 + Celery 调度 | 1.5天 | pipeline/ + scheduler/ |
| P1-8 | /trending + /articles API + Redis 缓存 | 2天 | routers + services |

### W3: 前端 + 联调

| 编号 | 任务 | 工期 | 输出 |
|------|------|------|------|
| P1-9 | Next.js 首页聚合热榜 + 单平台页 + 文章列表 | 3天 | page.tsx |
| P1-10 | 移动端适配 | 1天 | responsive |
| P1-11 | 前后端联调 + 采集稳定性 72h | 2天 | staging |

### MVP 验收标准
- [ ] 5 个平台热榜数据正常展示
- [ ] 采集引擎连续运行 72h，成功率 > 90%
- [ ] API P99 < 200ms（缓存命中）
- [ ] 与 platform-orchestrator 同机无冲突

---

## Phase 2: 用户系统 + 扩展平台（第 5-6 周）

| 编号 | 任务 | 工期 |
|------|------|------|
| P2-1 | 用户注册/登录 API（复用 python-jose） | 1.5天 |
| P2-2 | 登录/注册页面 + 个人中心 | 1天 |
| P2-3 | 收藏 API + 页面 | 1.5天 |
| P2-4 | 订阅 API + 通知推送 | 1.5天 |
| P2-5 | 抖音 + 小红书爬虫 | 2.5天 |
| P2-6 | 全文搜索（PG 内置） | 1天 |

---

## Phase 3: 管理后台 + API 商业化（第 7-8 周）

| 编号 | 任务 | 工期 |
|------|------|------|
| P3-1 | Vue3 管理后台（Dashboard + 数据源 + 审核） | 2天 |
| P3-2 | 内容审核 + 用户管理 | 1.5天 |
| P3-3 | API Key 管理 + 第三方 API + 限流 | 1.5天 |
| P3-4 | 公众号 + YouTube + TikTok + X 爬虫 | 2.5天 |
| P3-5 | 管道联动（trending_to_pipeline） | 1天 |

---

## Phase 4: 优化与上线（第 9-11 周）

| 编号 | 任务 | 工期 |
|------|------|------|
| P4-1 | SEO 优化 + Core Web Vitals | 2天 |
| P4-2 | CDN + 性能调优 | 1.5天 |
| P4-3 | k6 压力测试 | 1天 |
| P4-4 | 安全扫描 + 依赖审计 | 1天 |
| P4-5 | 生产部署 + 监控 + 灰度 | 2天 |

---

## 成本预算（整合后）

| 项目 | 费用 |
|------|------|
| ECS 升级（4G→8G） | ~400 元/月 |
| 代理IP池 | 共享已有 |
| PostgreSQL / Redis | 共享已有 |
| 域名 + SSL | 共享已有 |
| **月费合计** | **~400 元** |

比独立部署节省 ~1600-2600 元/月

## 人员分工（整合后）

| 角色 | 负责模块 | 人数 |
|------|---------|------|
| 后端全栈 | trendscope/api + trendscope/crawler + rpa-common | 1 |
| 前端 | Next.js C端 + Vue3管理后台 | 1 |
| 项目经理 | 需求、进度、文档 | 1（可兼任） |
