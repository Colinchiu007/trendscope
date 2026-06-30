---
name: trendscope-design
description: trendscope DESIGN.md — 爬虫引擎与 API 设计
---

# TrendScope — 设计文档

> **版本**: v0.3.0 | **更新**: 2026-07-01
> **关联**: docs/PRD.md, docs/ARCHITECTURE.md

## 一、爬虫框架设计

### 1.1 BaseSpider 抽象

```python
class BaseSpider(ABC):
    platform_code: str  # 唯一标识，如 "weibo"
    platform_name: str  # 显示名
    fetch_interval: int  # 采集间隔(秒)

    @abstractmethod
    async def fetch_trending_list(self) -> list[dict]:
        """返回标准化 dict 列表"""
        pass
```

标准化 dict 格式：
```json
{"rank": 1, "title": "...", "hot_value": 100000,
 "topic_url": "...", "snapshot_at": "ISO8601",
 "category": "tech", "_article": {...}?}
```

### 1.2 12 平台注册

在 `spiders/__init__.py` 的 `SPIDER_MAP` 中注册：

```python
SPIDER_MAP = {
    "weibo": WeiboSpider, "baidu": BaiduSpider,
    "douyin": DouyinSpider, "zhihu": ZhihuSpider,
    "bilibili": BilibiliSpider, "tieba": TiebaSpider,
    "toutiao": ToutiaoSpider, "kuaishou": KuaishouSpider,
    "youtube": YouTubeSpider, "twitter": TwitterSpider,
    "tiktok": TikTokSpider, "xiaohongshu": XiaohongshuSpider,
}
```

### 1.3 反爬透明层

| 模块 | 功能 | 配置方式 |
|------|------|---------|
| ProxyPool | 代理 IP 池 | 环境变量 / Redis |
| CookieManager | Cookie 注入/轮换 | Redis 持久化 |
| Fingerprint | 浏览器指纹混淆 | 随机 UA + Headers |
| RequestThrottle | 请求频率控制 | 基于 token bucket |

### 1.4 采集频率分级

| 等级 | 间隔 | 适用平台 |
|------|------|---------|
| T0 | 60s | 微博 |
| T1 | 3-5min | 百度/抖音/知乎 |
| T2 | 15min | B站/贴吧/头条/快手 |
| T3 | 30min-1h | YouTube/Twitter/TikTok/小红书 |

---

## 二、Pipeline 设计

```
Spider.fetch_trending_list()
   │
   ▼
Cleaner → 字段清洗/空值填充/格式标准化
   │
   ▼
Deduplicator → URL hash 去重 / 标题相似度(阈值0.85)
   │
   ▼
Normalizer → 热度值归一化/时间戳统一/分类映射
   │
   ▼
Writer → PostgreSQL 写入 / Redis 缓存刷新
```

---

## 三、缓存设计

Redis 4 级缓存：

| 缓存 | Key 模式 | TTL | 失效时机 |
|------|---------|-----|---------|
| 聚合热榜 | `trendscope:trending:agg:{cat}:{page}:{size}` | 60s | 任意平台采集完成 |
| 单平台热榜 | `trendscope:trending:plat:{plat}:{page}:{size}` | 120s | 该平台采集完成 |
| 文章详情 | `trendscope:article:{id}` | 600s | 文章更新/删除 |
| 平台列表 | `trendscope:platforms` | 3600s | 手动刷新 |

---

## 四、管道联动

### 4.1 TrendScope → content-aggregator 桥接

在 Celery task 采集完成后触发：

```python
# bridge.py
async def push_to_pipeline(topic: TrendingTopic):
    if not feature_gates.is_enabled("trending_to_pipeline"):
        return
    try:
        from content_aggregator import collect_and_rewrite
        await collect_and_rewrite(topic.url)
    except ImportError:
        # 降级 HTTP
        await httpx.post(f"{CA_URL}/api/collect", json={...})
```

受 `trending_to_pipeline` 功能开关控制（tier 2, 默认 disabled）。

---

## 五、依赖注入链

```
Router → Depends(get_trending_service) → TrendingService(Repo, Cache)
Router → Depends(get_article_service)  → ArticleService(Repo, Cache)
Router → Depends(get_user_service)     → UserService(Repo, Cache)
```

禁止绕过此链直接访问数据库。

---

## 六、API 响应格式

```json
{"code": 0, "message": "success", "data": {...},
 "pagination": {"page": 1, "page_size": 20, "total": 100, "total_pages": 5}}
```

错误码: `0=成功, 1001=参数错误, 1002=资源不存在, 1003=未认证, 1004=无权限, 1005=频率限制, 1006=重复操作`
