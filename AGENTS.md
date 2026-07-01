# trendscope — 开发流程规范

> 多平台热榜聚合引擎的开发流程与编码约定。AI 工具启动时自动读取。

---

## 核心原则

1. **Router → Service → Repository**：依赖注入链不能绕过，禁止在 Router 中直接访问数据库
2. **异步优先**：所有数据库操作用异步 SQLAlchemy 2.0（select().where()）
3. **TDD**：新增功能必须有测试覆盖
4. **标准化**：API 响应格式、错误码、爬虫输出格式统一
5. **先文档再代码**：没有 PRD 不动手，没有架构设计不动手

## AI 角色分工

| 角色 | 阶段 | 产出物 |
|------|------|--------|
| **PM** | 需求分析 | PRD、平台接入需求、API 规格 |
| **架构师** | 技术设计 | 爬虫设计、缓存策略、管道联动方案 |
| **开发工程师** | 编码实现 | 爬虫、API、服务层 + 测试（TDD） |
| **QA** | 质量验证 | API 测试、爬虫集成测试、冒烟测试 |
| **CTO** | 代码评审 | 安全审查、反爬策略审查、缓存正确性 |

## 7 阶段开发流程

### 阶段 1：想法澄清
确认：新增平台/API/功能的目标用户、数据来源、采集频率、缓存策略

### 阶段 2：PRD（PM）
产出：PRD 或变更说明，包含：
- 功能描述（P0/P1/P2）
- API 端点清单（如新增）
- 验收标准

**批准后才能进入下一阶段。**

### 阶段 3：技术设计（架构师）
产出：方案对比 + 推荐方案
- 新增爬虫：继承哪个 BaseSpider、采集频率分级
- 新增 API：路由 → Service → Repository 链
- 缓存策略（4 级缓存 TTL）
- 反爬策略（需要 cookie 池/代理池？）

**原则：选最简单的方案，不加新服务、不加重框架。**

### 阶段 4：开发计划（PM）
拆成 ≤4h 的任务，标注依赖关系。

### 阶段 5：编码实现（开发 + TDD）

#### 新增爬虫流程
1. 在 `crawler-engine/spiders/` 下新建爬虫，继承 `BaseSpider`
2. 实现 `fetch_trending_list() → list[dict]`
3. 标准化输出格式：`{rank, title, hot_value, topic_url, snapshot_at, category}`
4. 在 `spiders/__init__.py` 的 `SPIDER_MAP` 中添加映射
5. 编写爬虫集成测试（`scripts/test_*.py`，不纳入 CI）
6. 采集完成后确认调用了 `cache.invalidate(platform_code)`

#### 新增 API 流程
1. Router → Service → Repository 链
2. API 响应格式：`{code, message, data, pagination?}`
3. 错误码：`0/1001/1002/1003/1004/1005/1006`
4. 先写测试，再写路由
5. 手动验证：curl /health, curl /api/v1/trending

### 阶段 6：代码评审（CTO）
必检项：
- 🔴 API Key / Token 是否硬编码（必须环境变量）
- 🔴 SQL 注入：使用参数化查询
- 🟠 Repository 层是否封装了所有 SQL
- 🟠 采集完成后是否清空缓存
- 🟠 爬虫是否正确处理反爬策略
- 🟢 新增 API 是否注册到 Router
- 🟢 文档是否同步更新

CRITICAL 必须修复才能继续。

### 阶段 7：发布
- 更新 CHANGELOG.md
- 冒烟测试通过（`scripts/smoke-test.sh`）
- git 提交并 tag
- 部署后验证 Celery Beat + Worker 正常启动


## 详细规范

本文档只包含开发流程框架。详细规范已拆分到 `references/` 子目录：

- **[references/testing.md](references/testing.md)** — TDD 流程与测试规范
- **[references/quality-gates.md](references/quality-gates.md)** — 质量门禁详细说明
- **[references/commits.md](references/commits.md)** — 提交规范

## 文档清单

| 文件 | 路径 | 说明 |
|------|------|------|
| AGENTS.md | `./AGENTS.md` | 本文件，开发流程规范 |
| CLAUDE.md | `./CLAUDE.md` | 项目上下文和开发命令 |
| .clinerules | `./.clinerules` | 硬约束规则 |
| PRD.md | `./docs/PRD.md` | 产品需求文档 |
| ARCHITECTURE.md | `./docs/ARCHITECTURE.md` | 架构设计文档 |
| API_SPEC.md | `./docs/API_SPEC.md` | API 规格说明 |
| CHANGELOG.md | `./CHANGELOG.md` | 变更日志 |
| TEST_PLAN.md | `./docs/TEST_PLAN.md` | 测试计划 |
| PROJECT_PLAN.md | `./docs/PROJECT_PLAN.md` | 项目计划 |

## 开发命令

```bash
# API 服务
uvicorn trendscope.api.main:app --reload --port 8001

# 采集引擎
celery -A trendscope.crawler.celery_app worker -l info -c 4
celery -A trendscope.crawler.celery_app beat -l info

# 前端
cd frontend && npm run dev

# 测试
pytest tests/ -v --asyncio-mode=auto

# 冒烟
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/trending
```

## 版本

**v0.1.0** — Phase 0：多平台热榜聚合 + API + Celery 采集 + 前端展示
