# TrendScope API 规范

## 基础信息

- Base URL: `https://api.trendscope.cn/v1`
- 认证方式: JWT Bearer Token（用户接口）/ `X-API-Key` Header（第三方接口）
- 请求格式: `application/json`
- 响应格式: `application/json`
- 字符编码: UTF-8

## 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 156,
    "total_pages": 8
  },
  "request_id": "req_a1b2c3d4e5f6"
}
```

## 通用查询参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码，最小 1 |
| page_size | int | 20 | 每页条数，最小 1，最大 100 |
| platforms | string | - | 平台代码，逗号分隔（如 weibo,zhihu） |
| sort_by | string | hot_value_norm | 排序字段：hot_value_norm / publish_at / rank |
| order | string | desc | 排序方向：asc / desc |

## 公开接口

### GET /trending - 聚合热榜

获取跨平台聚合热榜列表。

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platforms | string | 否 | 平台代码，逗号分隔。不传返回全部 |
| category | string | 否 | 话题分类：tech / entertainment / social / finance / sports / all |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 12345,
        "platform": {
          "code": "weibo",
          "name": "微博",
          "icon_url": "https://cdn.trendscope.cn/icons/weibo.png"
        },
        "rank": 1,
        "title": "高考成绩陆续公布",
        "hot_value": "397.6万",
        "hot_value_norm": 98.5,
        "rank_change": "up",
        "topic_url": "https://s.weibo.com/weibo?q=%23...",
        "snapshot_at": "2025-06-23T10:00:00Z"
      }
    ]
  },
  "pagination": { "page": 1, "page_size": 20, "total": 500, "total_pages": 25 },
  "request_id": "req_abc123"
}
```

### GET /trending/{platform} - 单平台热榜

获取指定平台的完整热榜列表。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| platform | string | 平台代码，如 weibo / zhihu / bilibili |

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数（最大 100） |

### GET /trending/history - 热度趋势

获取话题的历史热度趋势数据。

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| topic_id | int | 是 | 话题 ID |
| range | string | 否 | 时间范围：24h / 3d / 7d（默认 24h） |
| interval | string | 否 | 数据间隔：5min / 1h / 1d（根据 range 自动选择） |

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "topic_id": 12345,
    "title": "高考成绩陆续公布",
    "platform": "weibo",
    "history": [
      { "timestamp": "2025-06-23T09:00:00Z", "hot_value": 92.0, "rank": 3 },
      { "timestamp": "2025-06-23T09:05:00Z", "hot_value": 95.3, "rank": 1 }
    ]
  },
  "request_id": "req_abc123"
}
```

### GET /articles - 热门文章列表

获取热门文章列表。

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platforms | string | 否 | 平台代码 |
| category | string | 否 | 分类 |
| time_range | string | 否 | 时间范围：1h / 6h / 24h / 7d（默认 24h） |
| source | string | 否 | hot / trending（默认 hot） |

### GET /articles/{id} - 文章详情

获取文章详细信息。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 文章 ID |

**响应**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 67890,
    "title": "2025高考分数线预测出炉",
    "platform": {
      "code": "zhihu",
      "name": "知乎",
      "icon_url": "https://cdn.trendscope.cn/icons/zhihu.png"
    },
    "summary": "随着各地高考成绩陆续公布...",
    "content_text": "完整文章内容...",
    "images": [
      { "url": "https://cdn.trendscope.cn/img/xxx.jpg", "width": 1200, "height": 630 }
    ],
    "video_url": null,
    "author": { "name": "教育观察者", "avatar": "https://..." },
    "source_url": "https://zhuanlan.zhihu.com/p/xxx",
    "read_count": 1500000,
    "like_count": 32000,
    "comment_count": 5600,
    "share_count": 8900,
    "publish_at": "2025-06-23T08:00:00Z"
  },
  "request_id": "req_abc123"
}
```

### GET /articles/search - 全文搜索

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |
| platforms | string | 否 | 平台筛选 |
| time_range | string | 否 | 时间范围 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页条数 |

### GET /platforms - 平台列表

**响应**:
```json
{
  "code": 0,
  "data": {
    "platforms": [
      { "code": "weibo", "name": "微博", "icon_url": "...", "is_active": true, "category": "social" },
      { "code": "zhihu", "name": "知乎", "icon_url": "...", "is_active": true, "category": "knowledge" }
    ]
  }
}
```

---

## 用户接口（需 JWT）

### POST /user/register - 注册

**请求体**:
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "phone": "13800138000",
  "password": "SecurePass123!",
  "verify_code": "123456"
}
```

**说明**: email 和 phone 至少提供一个。

### POST /user/login - 登录

**请求体**:
```json
{
  "account": "testuser",           // 用户名/邮箱/手机号
  "password": "SecurePass123!",
  "login_method": "password"       // password / sms
}
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "expires_in": 7200,
    "user": { "id": 1, "username": "testuser", "role": "user" }
  }
}
```

### POST /user/login/sms - 短信验证码登录

**请求体**:
```json
{
  "phone": "13800138000",
  "verify_code": "123456"
}
```

### POST /user/refresh - 刷新 Token

**请求体**:
```json
{
  "refresh_token": "eyJhbG..."
}
```

### GET /user/profile - 获取个人信息

### PUT /user/profile - 更新个人信息

**请求体**:
```json
{
  "nickname": "新昵称",
  "avatar_url": "https://...",
  "email": "newemail@example.com"
}
```

### GET /user/favorites - 收藏列表

### POST /user/favorites - 添加收藏

**请求体**:
```json
{
  "article_id": 67890,
  "folder_id": 1
}
```

### DELETE /user/favorites/{id} - 取消收藏

### GET /user/subscriptions - 订阅列表

### POST /user/subscriptions - 创建订阅

**请求体**:
```json
{
  "platform_id": 1,
  "keywords": ["AI", "大模型"],
  "notify_email": false,
  "notify_webpush": true
}
```

### DELETE /user/subscriptions/{id} - 删除订阅

### GET /user/notifications - 通知列表

### GET /user/notifications/stream - SSE 通知流

实时推送订阅匹配的新内容。

---

## 管理接口（需 Admin JWT）

### GET /admin/dashboard - 数据面板

**响应**:
```json
{
  "code": 0,
  "data": {
    "stats": {
      "today_visits": 152000,
      "today_api_calls": 45000,
      "active_users": 3200,
      "crawl_success_rate": 0.95,
      "total_articles": 1200000
    },
    "visit_trend": [
      { "date": "2025-06-17", "visits": 100000 },
      { "date": "2025-06-18", "visits": 120000 }
    ],
    "platform_distribution": [
      { "platform": "weibo", "count": 50000 },
      { "platform": "zhihu", "count": 35000 }
    ]
  }
}
```

### GET /admin/platforms - 平台管理列表

### PUT /admin/platforms/{id} - 更新平台配置

### POST /admin/crawl/trigger - 手动触发抓取

**请求体**:
```json
{
  "platform_id": 1,
  "force": false
}
```

### GET /admin/crawl/logs - 采集日志

**请求参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| platform_id | int | 平台 ID |
| status | string | success / failed / partial |
| page | int | 页码 |

### PATCH /admin/articles/{id} - 审核文章

**请求体**:
```json
{
  "status": "approved",      // approved / rejected / pinned
  "remark": "内容合规"
}
```

### GET /admin/articles - 文章管理列表

### GET /admin/users - 用户管理列表

### PATCH /admin/users/{id} - 更新用户状态

**请求体**:
```json
{
  "status": "banned",
  "role": "user"
}
```

### GET /admin/apikeys - API Key 列表

### POST /admin/apikeys - 创建 API Key

**请求体**:
```json
{
  "user_id": 1,
  "name": "数据分析平台对接",
  "rate_limit": 100,
  "expires_at": "2026-06-23T00:00:00Z"
}
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "id": 1,
    "key": "ts_live_a1b2c3d4e5f6g7h8i9j0",    // 仅创建时返回完整 Key
    "key_prefix": "ts_live_a1b2",
    "name": "数据分析平台对接",
    "rate_limit": 100,
    "expires_at": "2026-06-23T00:00:00Z"
  }
}
```

### DELETE /admin/apikeys/{id} - 撤销 API Key

### GET /admin/stats - API 调用统计

---

## 第三方 API（需 X-API-Key Header）

### GET /partner/trending - 聚合热榜

同公开接口 `GET /trending`，需在 Header 中携带 `X-API-Key: ts_live_xxx`

### GET /partner/trending/{platform} - 单平台热榜

同公开接口 `GET /trending/{platform}`

### GET /partner/articles - 文章列表

同公开接口 `GET /articles`

### GET /partner/articles/{id} - 文章详情

同公开接口 `GET /articles/{id}`

### GET /partner/usage - 查询用量

**响应**:
```json
{
  "code": 0,
  "data": {
    "today_calls": 4500,
    "daily_limit": 10000,
    "monthly_calls": 120000,
    "rate_limit_rpm": 100
  }
}
```

---

## 错误码

| code | 说明 |
|------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 资源不存在 |
| 1003 | 未认证（Token 缺失或无效） |
| 1004 | 无权限（角色不足） |
| 1005 | 请求频率超限 |
| 1006 | 重复操作 |
| 2001 | 数据库错误 |
| 2002 | 缓存服务错误 |
| 2003 | 第三方服务错误 |
| 3001 | 平台采集失败 |
| 3002 | 平台暂不可用 |
