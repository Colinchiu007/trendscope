# TrendScope（热榜）测试计划

## 1. 测试策略

### 1.1 测试金字塔

```
         ┌──────────────┐
         │  E2E 测试     │  关键用户路径 (Playwright)
         │  ~5%          │
         ├──────────────┤
         │  集成测试      │  API 接口 + 数据库一致性
         │  ~20%         │
         ├──────────────┤
         │  单元测试      │  覆盖率 > 80%
         │  ~75%         │  Go: service 层 + Python: pipeline 层
         └──────────────┘
```

### 1.2 测试环境

| 环境 | 用途 | 部署 | 触发 |
|------|------|------|------|
| dev | 本地开发自测 | Docker Compose | pre-commit / 手动 |
| staging | 集成测试 + QA | 阿里云 ECS | PR 合并后自动部署 |
| canary | 灰度验证 | K8s 金丝雀 | 生产发布前 (后期) |
| prod | 生产监控 | 阿里云 ACK | 持续监控 |

### 1.3 测试工具

| 类型 | 工具 |
|------|------|
| Go 单元测试 | go test + testify + mockery |
| Python 单元测试 | pytest + pytest-cov + responses |
| 前端单元测试 | Vitest + React Testing Library |
| API 集成测试 | pytest + httpx / Go httptest |
| E2E 测试 | Playwright |
| 性能测试 | k6 / wrk |
| 安全扫描 | OWASP ZAP / trivy |
| 依赖漏洞 | npm audit / go mod tidy / pip-audit |
| 代码质量 | golangci-lint / eslint / ruff |

## 2. 测试范围

### 2.1 采集引擎测试

#### 单元测试
- **BaseSpider 基类**: 测试公共方法（clean, deduplicate, normalize）
- **单平台爬虫**: Mock HTTP 响应，验证解析逻辑正确性
  - 正常数据解析
  - 空数据响应
  - 格式变化响应
  - 请求超时处理
- **反反爬模块**: 代理轮换、Cookie 管理、请求频率控制
- **数据管道**: 清洗→去重→归一化→写入 各环节独立测试

#### 集成测试
- 全链路测试：爬虫 → Pipeline → 数据库写入 → 缓存更新
- 跨平台去重：模拟相同话题在不同平台的合并逻辑
- 热度归一化：验证不同格式热度值的归一化结果

#### 稳定性测试
- 每个爬虫单独运行 24h，记录：
  - 采集成功率
  - 平均响应时间
  - 错误类型分布
  - 代理IP消耗量
- 目标：成功率 > 90%（T1平台）/ > 70%（高难度平台）

### 2.2 API 接口测试

#### 功能测试（所有端点）
| 接口分组 | 测试项 |
|---------|--------|
| /trending | 聚合查询、单平台查询、分页、筛选、历史趋势 |
| /articles | 列表查询、详情、搜索、分页 |
| /platforms | 平台列表、状态 |
| /user | 注册、登录、个人信息 CRUD、Token 刷新 |
| /user/favorites | 添加、列表、删除、重复添加 |
| /user/subscriptions | 创建、更新、删除、列表 |
| /admin/* | 数据面板、平台管理、用户管理、审核 |
| /partner/* | API Key 认证、限流、用量统计 |

#### 参数校验测试
- 边界值测试：空值、超长字符串、负数 page、0 page_size
- 类型校验：字符串传数字、必填字段缺失
- SQL 注入：`' OR '1'='1`、`; DROP TABLE--`
- XSS：`<script>alert(1)</script>`

#### 认证与授权测试
- 无 Token 访问受保护接口 → 401
- 过期 Token 访问 → 401
- 普通用户访问管理接口 → 403
- 伪造 Token → 401
- API Key 无效/过期/超限 → 401/429

#### 限流测试
- 连续请求超过限制 → 429
- 限流计数器重置验证
- 不同 Key 独立限流

#### 性能测试
| 接口 | 目标 QPS | P99 延迟 |
|------|---------|---------|
| GET /trending | > 500 | < 200ms |
| GET /trending/:platform | > 1000 | < 100ms |
| GET /articles | > 300 | < 200ms |
| GET /articles/:id | > 1000 | < 50ms |
| GET /articles/search | > 200 | < 300ms |

### 2.3 前端测试

#### 组件测试
- TrendingCard：数据渲染、空状态、加载中、错误状态
- HotList：空列表、单条、多条、滚动加载
- PlatformTabs：切换、高亮、滚动
- SearchBar：输入、清空、提交
- ArticleCard：封面图加载失败兜底、长标题截断

#### 页面测试
- 首页：SSR 渲染、数据加载、骨架屏
- 文章详情：内容渲染、图片懒加载、原文链接
- 搜索页：空结果、加载更多、筛选
- 登录/注册页：表单校验、错误提示、成功跳转

#### 响应式测试
- Mobile (375px)：布局、触摸交互、底部导航
- Tablet (768px)：侧边栏、网格布局
- Desktop (1280px+)：多栏布局、悬停效果

#### 可访问性测试 (axe-core)
- 目标：0 critical issues, 0 serious issues
- 检查项：色彩对比度、键盘导航、ARIA 标签、焦点管理

### 2.4 安全测试

| 测试项 | 方法 | 目标 |
|--------|------|------|
| OWASP Top 10 | ZAP 全量扫描 | 无高危漏洞 |
| JWT 安全 | 手动测试 | 无伪造/篡改可能 |
| API Key 防护 | 手动测试 | Key 不泄露于日志/响应 |
| XSS | 输入测试用例扫描 | 输出正确转义 |
| SQL 注入 | sqlmap | 无注入点 |
| CORS | 跨域请求测试 | 白名单正确限制 |
| CSP | 策略头检查 | 正确配置 |
| 依赖漏洞 | npm audit / pip-audit / govulncheck | 无已知高危漏洞 |

### 2.5 性能测试

#### 压测场景 (k6)

```javascript
// 场景1: 首页流量
// 500 VUs, 持续 5min, 爬坡 1min
GET /api/v1/trending
GET /api/v1/platforms

// 场景2: 文章浏览
// 300 VUs, 持续 5min
GET /api/v1/articles?page=1&page_size=20
GET /api/v1/articles/:id (随机)

// 场景3: 搜索
// 100 VUs, 持续 3min
GET /api/v1/articles/search?q={keyword}
```

#### 目标指标
- API P99 < 200ms（缓存命中）
- API P99 < 500ms（缓存未命中）
- 错误率 < 0.1%
- 首页 LCP < 2.5s, FID < 100ms, CLS < 0.1

## 3. 测试自动化

### 3.1 Pre-commit Hook

```
提交前自动执行:
- golangci-lint (Go)
- ruff + mypy (Python)
- eslint + prettier (Frontend)
- 相关的单元测试
```

### 3.2 CI/CD 流水线

```
PR 创建:
  ├── Go: go test ./... + golangci-lint
  ├── Python: pytest + ruff
  ├── Frontend: vitest + eslint + tsc --noEmit
  └── 构建 Docker 镜像

PR 合并到 main:
  ├── 全量单元测试 + 集成测试
  ├── 构建 + 推送镜像到 ACR
  ├── 自动部署 staging
  └── E2E Smoke Test (Playwright)
```

### 3.3 上线前 Checklist

- [ ] 全量单元测试通过
- [ ] 集成测试通过
- [ ] E2E 关键路径测试通过
- [ ] 安全扫描无高危漏洞
- [ ] 性能压测达标
- [ ] 依赖漏洞扫描通过
- [ ] 采集引擎稳定性验证（24h）
- [ ] 移动端/桌面端兼容性验证

## 4. 缺陷管理

### 4.1 严重级别

| 级别 | 定义 | 响应时间 | 修复时间 |
|------|------|---------|---------|
| P0 致命 | 服务宕机 / 数据丢失 / 安全漏洞 | 1h | 4h |
| P1 严重 | 核心功能不可用 / 采集全平台失败 | 4h | 24h |
| P2 一般 | 部分功能异常 / 单平台采集失败 | 24h | 1周 |
| P3 轻微 | UI 显示问题 / 文案错误 | 1周 | 下个迭代 |
| P4 建议 | 体验优化 / 性能优化 | - | 排期处理 |
