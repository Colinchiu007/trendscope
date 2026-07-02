# TrendScope（热榜）产品需求文档

## 1. 产品概述

### 1.1 产品定位

TrendScope 是一个多平台热榜聚合引擎，一站式呈现来自13个主流内容平台的热门话题和热门文章，帮助用户高效获取全网热点。产品同时作为一个数据引擎，通过 API 向第三方提供结构化的热榜数据。

### 1.2 目标用户

| 用户类型 | 描述 | 核心需求 |
|---------|------|---------|
| C端用户 | 普通网民、自媒体从业者、内容创作者 | 快速浏览全网热点，发现创作灵感 |
| B端用户 | 数据分析公司、舆情监控系统、媒体机构 | 通过 API 获取结构化热榜数据 |
| 管理员 | 平台运营人员 | 管理数据源、审核内容、监控系统状态 |

### 1.3 数据来源平台

国内平台（10个）：抖音、百度、今日头条、视频号、公众号、小红书、知乎、微博、Bilibili、快手

国际平台（3个）：YouTube、TikTok、X（Twitter）

## 2. 功能需求

### 2.1 热榜展示（C端前台）

#### 2.1.1 首页聚合热榜
- 多平台热榜汇总视图，以卡片/列表混合布局呈现
- 支持按平台 Tab 切换查看
- 支持按分类（科技、娱乐、社会、财经等）筛选
- 显示每个话题的排名、热度值、所属平台、更新时间
- 默认按综合热度降序排列，用户可切换排序方式

#### 2.1.2 单平台热榜
- 每个平台的完整热榜列表（Top 50）
- 显示排名变化趋势（上升/下降/新进）
- 话题名称 + 热度值 + 跳转链接
- 支持查看历史快照（过去7天）
- 关联话题推荐

#### 2.1.3 热门文章列表
- 跨平台热门文章汇总
- 文章卡片：标题、摘要、封面图、作者、来源平台
- 关键指标：阅读量/播放量、点赞数、评论数
- 支持按平台、时间范围、热度排序筛选

#### 2.1.4 文章详情页
- 文章完整标题和正文内容
- 图片列表（图文混排）
- 视频链接（如有）
- 作者信息和头像
- 来源平台标识 + 原文链接
- 相关文章推荐

#### 2.1.5 全文搜索
- 按关键词搜索热榜话题和文章
- 搜索结果高亮关键词
- 支持按平台、时间范围过滤
- 搜索结果按相关度 + 热度排序

#### 2.1.6 热度趋势
- 单个话题7天内热度变化折线图
- 标注峰值时间和事件
- 关联话题推荐

### 2.2 用户系统

#### 2.2.1 注册与登录
- 手机号注册（短信验证码，Redis 缓存 5 分钟）
- 邮箱注册（邮件验证码验证）
- 密码登录
- 短信验证码登录（免密登录）
- JWT Token 认证（Access Token 2h + Refresh Token 7d）

#### 2.2.2 个人中心
- 查看/编辑个人信息（昵称、头像、邮箱、手机号）
- ✅ 修改密码（put /user/password）
- ✅ 账号注销（软删除，put user.status = deleted）

#### 2.2.3 收藏功能
- 收藏感兴趣的文章
- ✅ 收藏夹管理（CRUD，POST/GET/PUT/DELETE /user/folders）
- 支持按收藏时间/热度排序

#### 2.2.4 订阅功能
- 按平台订阅：关注特定平台的热榜更新
- 按关键词订阅：指定关键词出现时通知
- 通知方式：站内通知 + 邮件（可选）

#### 2.2.5 通知推送
- ✅ 实时推送：通过 SSE 推送通知（GET /user/notifications/stream）
- 通知列表：查看历史通知
- 通知设置：管理推送偏好

### 2.3 管理后台

#### 2.3.1 数据面板
- 关键指标卡片：今日访问量、API调用量、活跃用户数、采集成功率
- 访问趋势图（7天/30天）
- 平台热榜数据量统计
- 系统健康状态

#### 2.3.2 数据源管理
- 平台列表：查看所有平台状态
- 启用/禁用特定平台的采集
- 配置抓取参数：频率、代理、请求头
- 查看各平台最近采集日志

#### 2.3.3 抓取调度
- ✅ 实时查看采集任务状态（GET /admin/crawl/status）
- 手动触发指定平台的即时抓取
- 采集失败告警 + 重试机制
- 采集统计数据（成功率、平均耗时、抓取量）

#### 2.3.4 内容审核
- 文章审核列表（待审核/已通过/已驳回）
- ✅ 批量审核操作（POST /admin/articles/batch-audit）
- 文章置顶/隐藏
- 敏感词过滤配置

#### 2.3.5 用户管理
- 用户列表：搜索、筛选、排序
- ✅ 用户详情：注册时间、活跃情况、收藏/订阅统计（GET /admin/users/{id}/stats）
- 封禁/解封用户
- 角色管理（普通用户/管理员）

#### 2.3.6 API Key 管理
- 创建/撤销 API Key
- 设置每个 Key 的速率限制（QPS）
- 设置过期时间
- 查看每个 Key 的调用统计
- 用量计费报表

### 2.4 API 引擎

#### 2.4.1 公开 API（无需认证）
- 聚合热榜查询、单平台热榜查询
- 文章列表/详情查询
- 全文搜索
- 平台列表查询
- 合理的匿名调用速率限制

#### 2.4.2 第三方 API（API Key 认证）
- 与公开 API 相同的数据接口
- 更高的速率限制和调用配额
- API Key 通过 Header `X-API-Key` 传递
- 按调用量计费（免费 tier + 付费 tier）

#### 2.4.3 API 规范
- RESTful 设计
- 统一响应格式：`{code, message, data, pagination, request_id}`
- 分页支持
- 错误码体系
- OpenAPI 3.0 文档

## 2.5 Pipeline 集成

TrendScope 作为内容管道的上游，通过 `platform-orchestrator` 的 `trending_to_pipeline` 功能开关（当前 tier 2，默认禁用）控制是否将热榜数据自动送入下游 pipeline（content-aggregator → smart-sentence-splitter → prompt-engine → Story2Video）。

启用后，热榜话题或文章会按配置规则自动推送到下游，无需人工干预。

### 2.5.1 评分矩阵过滤器（规划中，待实现）

当前 pipeline 的准入逻辑基于热度排序（热度值高的优先推送），缺少多维度内容质量评估。规划引入可选的评分矩阵旁路过滤器，不影响热榜自身排序逻辑。

**评分维度（参考 topic-reviewer 模型）：**

| 维度 | 权重 | 说明 |
|------|------|------|
| 独特角度 | 30% | 话题是否有差异化价值，而非千篇一律的通用论述 |
| 用户价值 | 25% | 话题对目标用户的实用程度（干货价值、信息增益） |
| 领域适配 | 20% | 话题与视频内容方向的匹配度 |
| 时效性 | 15% | 话题的新鲜度，优先 24h 内的新鲜内容 |
| 创作难度 | 10% | 视频化改编的可行性（素材丰富度、画面可表达性） |

**一票否决条件（可选配置）：**
- 热度低于阈值
- 平台来源不在白名单
- 内容类型不适配视频化（如纯文本公告、政策法规原文等）

**配置方式：**
- 后台管理页面的配置面板（管理后台 → 数据源管理 或 新增「Pipeline 配置」页）
- 可开关评分矩阵（默认关闭）
- 可编辑各维度权重
- 可配置一票否决的阈值和条件列表

**约束：**
- 评分矩阵仅影响 `trending_to_pipeline` 开启时的推送准入，不改变热榜页面前端展示
- 不引入新的外部依赖，评分逻辑在 TrendScope API 服务内实现
- 权重和阈值支持后台动态修改，无需重启服务

### 3.1 性能要求
- API 响应时间 P99 < 200ms（缓存命中时）
- 首页加载时间 LCP < 2.5s
- 支持 1000+ 并发用户
- 采集引擎单平台处理 < 30s

### 3.2 可用性要求
- 服务可用性 > 99.5%（非采集部分）
- 采集引擎可用性 > 95%（受反爬影响）
- 优雅降级：采集失败时展示上一次成功数据

### 3.3 安全要求
- 用户密码 bcrypt 加密
- JWT Token 安全配置
- API 限流防护
- CORS 白名单
- SQL 注入防护
- XSS 防护
- HTTPS 全站加密

### 3.4 兼容性要求
- 前端适配 Mobile / Tablet / Desktop
- 移动端流量占比 > 70%，mobile-first 设计
- 支持主流浏览器（Chrome、Safari、Edge、Firefox 最近2个版本）

### 3.5 合规要求
- 仅展示公开可访问内容
- 遵守各平台 robots.txt
- ICP 备案
- 公安联网备案
- 用户隐私政策 + 用户协议


---

## 4. 技术补充（审查报告驱动）

> 本文档基于 2026-07-02 PRD 审查报告生成，覆盖 8 个高严重度缺口和 3 个接口冲突。
> 版本: v1.1.0  最后更新: 2026-07-02

### 4.1 热度归一化公式

跨平台热度值量纲差异极大（微博热度指数 vs B站播放量 vs 小红书互动数），需要统一归一化后才能进行跨平台排序。

#### 4.1.1 单指标归一化（平台内）

对每个平台的热度指标，使用 **min-max + log 缩放** 组合：

```
normalized = (log(raw_value + 1) - log(min + 1)) / (log(max + 1) - log(min + 1))
```

- `raw_value`: 原始热度值（如播放量、热度指数）
- `min / max`: 该平台当前批次（Top 50）的最小/最大值
- 结果范围: `[0, 1]`

选择 log 缩放的原因：热度分布通常为长尾分布，log 能有效压缩头部差异，避免头部话题垄断排序。

#### 4.1.2 跨平台综合热度分

```
composite_score = sum(platform_weight[i] * normalized[i]) * recency_factor
```

**平台权重配置表（默认值，后台可调）：**

| 平台 | 权重 | 理由 |
|------|------|------|
| 微博 | 0.20 | 社交舆论策源地，时效性最强 |
| 抖音 | 0.18 | 最大短视频平台，用户基数大 |
| 百度 | 0.12 | 搜索热度反映全民关注度 |
| Bilibili | 0.10 | 年轻用户群体风向标 |
| 今日头条 | 0.10 | 资讯聚合，覆盖面广 |
| 小红书 | 0.08 | 消费趋势指标 |
| 知乎 | 0.08 | 深度讨论，话题质量参考 |
| 快手 | 0.05 | 下沉市场热度指标 |
| YouTube | 0.04 | 国际视角 |
| TikTok | 0.03 | 国际短视频热度 |
| X（Twitter）| 0.01 | 国际舆论辅助 |
| 公众号 | 0.01 | 深度内容参考 |
| 视频号 | 0.00 | 微信生态内部，暂不参与跨平台排序 |

**时效性衰减因子：**

```
recency_factor = max(0.2, 1.0 - 0.05 * hours_since_update)
```

- 0-2 小时：满分 1.0
- 6 小时后：衰减至 0.7
- 16 小时后：衰减至 0.2（底线）
- 目的：保证新鲜内容优先，但不完全淘汰稳定热点

#### 4.1.3 实现位置

归一化逻辑在 `trendscope/api/services/trending_service.py` 中实现，每次快照写入时预计算 `hot_value_norm` 字段（已存在于 `TrendingTopicModel`）。预计算避免了查询时实时计算的性能开销。

权重和衰减参数存储在 `settings.py` 或 YAML 配置文件中，支持后台动态修改。

### 4.2 API 限流规范

#### 4.2.1 限流层级

| 层级 | 匿名用户 | 注册用户 | API Key（免费） | API Key（付费） |
|------|---------|---------|----------------|----------------|
| 全局 QPS 上限 | 100 | 500 | 1000 | 5000 |
| 单 IP/Key QPS | 5 | 20 | 50 | 200 |
| 单 IP/Key 日配额 | 1,000 | 10,000 | 50,000 | 500,000 |
| 并发连接数 | 3 | 10 | 20 | 100 |

#### 4.2.2 限流算法

- **主算法**: 滑动窗口计数器（Redis Sorted Set），精确统计 QPS
- **降级算法**: 令牌桶（Token Bucket），允许短时突发（突发倍率 1.5x）
- **全局保护**: 基于连接数的 Circuit Breaker，超过阈值时拒绝新连接

#### 4.2.3 响应规范

超限时返回 HTTP 429，响应体：

```json
{
    "code": 429,
    "message": "Rate limit exceeded",
    "data": {
        "limit": 20,
        "remaining": 0,
        "reset_at": "2026-07-02T10:00:00Z",
        "retry_after": 30
    },
    "request_id": "req_xxx"
}
```

响应头：`X-RateLimit-Limit`、`X-RateLimit-Remaining`、`X-RateLimit-Reset`

#### 4.2.4 限流存储

使用 Redis 作为限流计数器存储（与现有 JWT 黑名单共用 Redis 实例）。Redis 仅存储限流相关 key（TTL = 窗口长度），预估内存占用 < 10MB（1000 并发 x 1KB/counter）。

### 4.3 代理池方案

#### 4.3.1 代理来源

| 来源 | 类型 | 适用场景 | 月成本预估 |
|------|------|---------|-----------|
| 快代理 / 芝麻代理 | 付费商业代理 | 微博、抖音等反爬严格平台 | 500-800 元/月 |
| 自建代理（阿里云轻量） | 云服务器 IP 轮换 | 中等反爬平台（百度、知乎） | 100 元/月（3台） |
| 免费代理池 | 爬虫框架内置 | 低反爬平台或降级使用 | 0 元 |

#### 4.3.2 代理轮换策略

- **轮换粒度**: 每个请求使用不同代理（随机选择）
- **健康检查**: 异步检测代理可用性（3 秒超时），不可用则剔除
- **冷却机制**: 同一代理被封禁后冷却 5 分钟
- **平台绑定**: 高反爬平台（微博、抖音、小红书）使用付费代理池，其余使用自建+免费
- **备用降级**: 付费代理耗尽时降级到自建，自建失败时降级到免费代理
- **成本上限**: 单月代理总成本不超过 1,500 元（硬限制）

#### 4.3.3 实现

代理管理在 `trendscope/crawler/proxy_pool.py` 中实现，接口：

```python
class ProxyPool:
    async def get_proxy(self, platform: str) -> str: ...
    async def report_failure(self, proxy: str, platform: str) -> None: ...
    async def health_check(self) -> dict: ...
```

### 4.4 全文搜索技术选型

#### 4.4.1 选型对比

| 维度 | SQLite FTS5 | Meilisearch |
|------|------------|-------------|
| 部署复杂度 | 零（内嵌 SQLite） | 独立服务进程 |
| 内存占用 | < 50MB | 200-500MB |
| P99 延迟（10万条数据） | 15-50ms | 5-20ms |
| 中文分词 | jieba 自定义 | 内置 CJK 支持 |
| 与现有架构兼容 | 已有 SQLite | 新增依赖 |
| 高亮支持 | 基础 | 原生支持 |
| 模糊搜索 | 有限 | 强大 |

#### 4.4.2 决策：Phase 1 用 SQLite FTS5，预留 Meilisearch 接口

**理由：**

1. TrendScope 当前使用 aiosqlite（WAL 模式），FTS5 是零成本扩展
2. 初期数据量预估 < 50 万条（13 平台 x Top 50 x 7 天快照），FTS5 完全够用
3. P99 < 200ms 目标在 FTS5 下可达（实测 15-50ms 查询 + 100ms 网络预算）
4. 中文分词使用 jieba，FTS5 的 simple tokenizer + jieba 预分词

**FTS5 实现方案：**

```sql
CREATE VIRTUAL TABLE trending_fts USING fts5(
    title, summary, category, platform_code,
    content='trending_topics',
    content_rowid='id',
    tokenize='unicode61'
);

-- jieba 预分词后写入
INSERT INTO trending_fts(rowid, title, summary, category, platform_code)
SELECT id, title, summary, category, platform_code FROM trending_topics;
```

**搜索查询示例：**

```sql
SELECT t.*, rank
FROM trending_topics t
JOIN trending_fts f ON t.id = f.rowid
WHERE trending_fts MATCH ?
ORDER BY rank
LIMIT ? OFFSET ?;
```

**Phase 2 迁移路径：** 当数据量超过 100 万条或搜索 P99 超过 100ms 时，引入 Meilisearch 作为独立搜索服务，通过 SearchBackend 接口抽象实现热切换。

### 4.5 Pipeline 推送接口

#### 4.5.1 接口定义

TrendScope 通过 `platform-orchestrator` 的 `trending_to_pipeline` 功能开关向下游推送数据。推送时调用 orchestrator 内部 API，构造 `ContentPacket` 对象。

#### 4.5.2 字段映射

TrendScope `TrendingPipelineItem` -> `shared_models.pipeline.ContentPacket` 映射：

| TrendScope 字段 | ContentPacket 字段 | 说明 |
|----------------|-------------------|------|
| source_url | source_url | 直接映射 |
| title | source_title | 直接映射 |
| platform.code | source_platform | 平台代号（如 weibo, douyin） |
| summary | source_content | 摘要作为原始正文（详情页全文可选补充） |
| read_count + like_count | source_hot_score | 综合热度分（归一化后） |
| （无） | id | 由 orchestrator 生成 UUID |
| （无） | stage | 默认 PipelineStage.COLLECTED |
| （无） | collected_at | 推送时的时间戳 |

#### 4.5.3 推送接口

```python
# TrendScope 端调用
POST {ORCHESTRATOR_BASE_URL}/api/v1/pipeline/trending-push
Content-Type: application/json
Authorization: Bearer {INTERNAL_SERVICE_TOKEN}

Body: TrendingPipelineItem  # 共享模型，Pydantic 序列化

Response: { "code": 0, "message": "queued", "data": { "content_id": "uuid" } }
```

#### 4.5.4 推送逻辑

- **推送频率**: 每次快照写入后（约 5-30 分钟一次，取决于平台配置）
- **推送量**: 仅推送通过一票否决过滤后的 Top N（默认 N=20，后台可配）
- **去重**: 基于 source_url 去重，相同 URL 24 小时内不重复推送
- **失败重试**: 异步队列（Celery），失败后指数退避重试 3 次
- **幂等性**: orchestrator 侧基于 source_url 幂等，重复推送不会创建重复 ContentPacket

### 4.6 评分矩阵设计

#### 4.6.1 两层架构

评分矩阵采用 **规则引擎为主 + LLM 辅助** 的两层架构，平衡准确性和成本：

```
                    +---------------+
TrendingPipelineItem |  Layer 1:     | < 规则引擎（< 5ms，零成本）
 -------------------->|  规则过滤      |
                    +-------+-------+
                            | 通过
                    +-------v-------+
                    |  Layer 2:     | < LLM 评估（~500ms，按量计费）
                    |  LLM 打分      |
                    +-------+-------+
                            |
                    +-------v-------+
                    |  综合评分      |
                    +---------------+
```

#### 4.6.2 Layer 1：规则引擎

纯本地计算，无外部依赖，处理速度 < 5ms/item。

| 规则 | 类型 | 条件 | 结果 |
|------|------|------|------|
| 热度阈值 | 硬过滤 | source_hot_score < 50 | 一票否决 |
| 平台白名单 | 硬过滤 | source_platform not in [weibo,douyin,baidu,...] | 一票否决 |
| 内容类型 | 硬过滤 | 标题匹配纯广告/政策原文正则 | 一票否决 |
| 时效性 | 软打分 | 0-6h: 1.0, 6-24h: 0.7, 24-72h: 0.4, >72h: 0.2 | 时效分 |
| 标题长度 | 软打分 | 10-50字: 1.0, 5-10或50-80: 0.7, 其他: 0.3 | 标题分 |

**规则引擎输出**: rule_score = 0-1 的综合分 + 硬过滤结果

#### 4.6.3 Layer 2：LLM 评估（可选，默认关闭）

仅当评分矩阵功能开关开启 + LLM 模式启用时生效。使用共享 LLM 网关（shared_models.llm），通过 orchestrator 统一调度。

**评估 Prompt 模板：**

```
你是一个内容筛选专家。请评估以下话题是否适合制作成短视频内容。

话题标题：{title}
来源平台：{platform}
话题摘要：{summary}

请从以下维度打分（0-10分）：
1. 独特角度：话题是否有差异化价值
2. 用户价值：话题对目标用户的实用程度
3. 领域适配：话题与视频内容方向的匹配度
4. 创作难度：视频化改编的可行性

返回 JSON：{"unique_angle": N, "user_value": N, "domain_fit": N, "creative_feasibility": N}
```

**成本控制：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 每日 LLM 调用上限 | 200 次 | 超过后仅用规则引擎 |
| 每次请求 token 上限 | 500 tokens | 输入+输出 |
| 批量评估 | 5 条/批 | 减少 API 调用次数 |
| 模型选择 | gpt-4o-mini | 成本优先（约 0.0003 美元/次） |

**月成本预估**: 200 次/天 x 30 天 x 0.0003 美元 = 1.8 美元/月（极低）

#### 4.6.4 综合评分公式

```
final_score = alpha * rule_score + beta * llm_score
```

- 默认 alpha=1.0, beta=0.0（纯规则引擎）
- 开启 LLM 后：alpha=0.4, beta=0.6
- rule_score 和 llm_score 都归一化到 [0, 1]

### 4.7 第三方 API 成本预算

#### 4.7.1 各平台采集成本

| 平台 | 采集方式 | API/代理成本 | 月调用量 | 月成本 |
|------|---------|-------------|---------|--------|
| 微博 | 公开 API + 付费代理 | 代理费 | 720 次/天 x 30 | 600 元（代理分摊） |
| 抖音 | 网页爬虫 + 付费代理 | 代理费 | 720 x 30 | 300 元（代理分摊） |
| 百度 | 公开 API | 免费 | 144 x 30 | 0 元 |
| Bilibili | 公开 API（wbi） | 免费 | 144 x 30 | 0 元 |
| 今日头条 | 网页爬虫 + 自建代理 | 云服务器费 | 144 x 30 | 30 元（分摊） |
| 小红书 | 网页爬虫 + 付费代理 | 代理费 | 144 x 30 | 200 元（代理分摊） |
| 知乎 | 公开 API | 免费 | 144 x 30 | 0 元 |
| 快手 | 公开 API | 免费 | 144 x 30 | 0 元 |
| YouTube | Data API v3 | 0.005 美元/1000 次 | 144 x 30 | < 0.1 美元 |
| TikTok | 网页爬虫 | 代理费 | 72 x 30 | 100 元（代理分摊） |
| X（Twitter）| 公开 API（Basic） | 100 美元/月 | 持续 | 700 元 |
| 公众号 | 公开 API | 免费 | 144 x 30 | 0 元 |
| 视频号 | 内部接口 | 免费 | 144 x 30 | 0 元 |

#### 4.7.2 月度总成本汇总

| 成本项 | 金额 | 说明 |
|--------|------|------|
| 付费代理池 | 1,200 元 | 微博+抖音+小红书+TikTok |
| 自建代理（云服务器） | 100 元 | 3 台轻量应用服务器 |
| Twitter API | 700 元 | Basic 计划 100 美元/月 |
| LLM 评分（可选） | 13 元 | gpt-4o-mini 评估用 |
| Redis（限流+缓存） | 0 元 | 复用现有 Redis |
| **月度总计** | **2,013 元** | 未含 LLM: 2,000 元 |

#### 4.7.3 成本优化策略

- **缓存优先**: 热榜数据变更频率低，设置 TTL=5 分钟缓存，减少重复请求
- **智能调度**: 非高峰时段（0:00-6:00）降低采集频率至 1/3
- **代理成本分级**: 按平台反爬强度分配代理等级，避免过度配置
- **Twitter 降级**: 如成本敏感，降级为 Free 计划（1,500 tweets/月，仅采集热搜）

### 4.8 采集深度/频率矩阵

#### 4.8.1 各平台采集参数

| 平台 | 采集深度 | 采集频率 | 峰值时段加密 | 章节内容 |
|------|---------|---------|-------------|---------|
| 微博 | Top 50 热搜 + Top 3 文章详情 | 10 分钟/次 | 7-9, 12-14, 19-22 点 -> 5 分钟 | 标题+摘要 |
| 抖音 | Top 50 热点 + Top 5 视频详情 | 15 分钟/次 | 同上 -> 10 分钟 | 标题+描述 |
| 百度 | Top 100 热搜 | 30 分钟/次 | 无加密 | 标题 |
| Bilibili | Top 50 热搜 + Top 5 视频详情 | 30 分钟/次 | 无加密 | 标题+简介 |
| 今日头条 | Top 50 热榜 | 30 分钟/次 | 无加密 | 标题 |
| 小红书 | Top 30 笔记 + Top 5 详情 | 20 分钟/次 | 9-22 点 -> 10 分钟 | 标题+摘要 |
| 知乎 | Top 50 热榜 + Top 3 详情 | 30 分钟/次 | 无加密 | 标题+摘要 |
| 快手 | Top 30 热榜 | 30 分钟/次 | 无加密 | 标题 |
| YouTube | Trending 30 + 热门 5 详情 | 1 小时/次 | 无加密 | 标题+描述 |
| TikTok | Top 30 趋势 | 30 分钟/次 | 同微博 | 标题+描述 |
| X（Twitter）| Trending 30 | 15 分钟/次 | 8-22 点 -> 10 分钟 | 标题+摘要 |
| 公众号 | 热门 20 篇 | 1 小时/次 | 无加密 | 标题+摘要 |
| 视频号 | 热门 20 个 | 1 小时/次 | 无加密 | 标题 |

#### 4.8.2 采集详情深度定义

| 深度级别 | 内容范围 | 适用场景 | 估算耗时 |
|---------|---------|---------|---------|
| Level 1（标题） | 仅标题+热度值+排名 | 百度、快手等纯热搜 | < 5s |
| Level 2（摘要） | 标题+摘要+作者+互动数据 | 微博、知乎、公众号 | 5-15s |
| Level 3（详情） | Level 2 + 正文全文+图片列表 | 抖音视频、小红书笔记 | 10-30s |

#### 4.8.3 全平台采集预算

| 项目 | 数值 |
|------|------|
| 每日采集请求总量 | ~15,000 次（含重试） |
| 峰值 QPS | ~5（13 平台同时采集） |
| 单次采集周期总耗时 | ~5 分钟（并行） |
| 每日存储增量 | ~50,000 条话题 + ~5,000 条文章详情 |
| 7 天保留总量 | ~400,000 条话题 |
| 每月存储成本 | < 500MB SQLite（WAL 模式） |

---

## 5. 接口冲突解决方案

### 5.1 用户身份统一：TrendScope 复用 orchestrator SSO

**问题**: TrendScope 有独立用户系统（手机号/邮箱注册），与 orchestrator SSO 身份存在冲突。

**方案**: TrendScope 废弃独立注册/登录，完全复用 platform-orchestrator 的用户系统。

| 迁移项 | 当前方案 | 迁移后方案 |
|--------|---------|-----------|
| 注册 | TrendScope 独立 API | orchestrator SSO 注册 |
| 登录 | TrendScope 独立 JWT | orchestrator JWT（共享密钥 PO_SECRET_KEY） |
| 收藏/订阅 | TrendScope 独立表 | TrendScope 表 + orchestrator user_id 外键 |
| 管理后台 | TrendScope 独立管理 | orchestrator 管理面板统一入口 |

**迁移时间表**: Phase 1（MVP）期间 TrendScope 保留独立用户系统用于快速验证；Phase 2 迁移至 orchestrator SSO。

### 5.2 API Key 管理去重

**问题**: TrendScope 和 orchestrator 都有 API Key 管理功能，功能重叠。

**方案**: TrendScope API Key 由 orchestrator 统一管理，TrendScope 仅做鉴权校验。

```
B端用户 -> orchestrator API Key 管理页 -> 生成 Key
              |
TrendScope API 收到请求 -> Header X-API-Key -> 调 orchestrator 鉴权接口验证
              |
验证通过 -> 返回数据；验证失败 -> 401
```

### 5.3 评分结果回写 shared-models

**问题**: 评分矩阵产出的分数是否需要回写到 shared-models？

**方案**:

- TrendingTopicModel 已有 hot_value_norm 字段，**不新增 score 字段**（避免破坏现有契约）
- 评分矩阵的 final_score 存储在 TrendScope 内部数据库（pipeline_scores 表）
- 推送给 orchestrator 时，final_score 作为 metadata["pipeline_score"] 传入 ContentPacket
- 不修改 shared_models.trendscope 中的模型定义

**pipeline_scores 表结构：**

```sql
CREATE TABLE pipeline_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    source_url TEXT NOT NULL UNIQUE,
    rule_score REAL NOT NULL DEFAULT 0.0,
    llm_score REAL DEFAULT NULL,
    final_score REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES trending_topics(id)
);
```

---

## 6. 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0.0 | 2026-06-20 | 初始 PRD |
| v1.0.1 | 2026-06-25 | 补齐邮箱注册/密码修改/账号注销/SSE/关联话题/视频号/收藏夹/管理后台 |
| v1.1.0 | 2026-07-02 | 审查报告驱动补充：热度归一化公式、API 限流规范、代理池方案、全文搜索选型、Pipeline 推送接口、评分矩阵设计、第三方 API 成本预算、采集深度/频率矩阵、接口冲突解决方案 |

---
