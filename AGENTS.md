# trendscope — 开发规范

> 语言: Python  |  文件数: ~162  |  生成: /init-deep

## 项目概述

trendscope: CLAUDE.md

## 源目录结构

- `frontend/` — 主源码目录
  - `src/`
  - `src.bak.1782311046/`
- `trendscope/` — 主源码目录
  - `api/`
  - `crawler/`

## 硬约束（来自 .clinerules）

- Router → Service → Repository 依赖注入链不能绕过，禁止在 Router 中直接访问数据库
- Repository 层封装所有查询，Router 和 Service 中不能出现 SQL
- 所有数据库操作用异步 SQLAlchemy 2.0（select().where()）
- crawler-engine/spiders/ 下每个爬虫必须继承 BaseSpider 并实现 fetch_trending_list()
- API 响应格式统一为 {code, message, data, pagination?}
- 错误码统一使用 0/1001/1002/1003/1004/1005/1006
- 采集完成后必须调用 cache.invalidate(platform_code) 刷新缓存
- 标准化 dict 格式为 {rank, title, hot_value, topic_url, snapshot_at, category}
- ... 及 3 条其他约束

## PRD 参考

- PRD: `docs/PRD.md` — TrendScope（热榜）产品需求文档

## 入口文件

- `CLAUDE.md` — 开发指南和命令
- `.clinerules` — 项目特定硬约束
- `docs/PRD.md` — 产品需求文档
- `frontend/` — 源码入口
- `AGENTS.md` — 本文件，AI 行为规范

## 管道位置

- 当前: `trendscope/`
- 下游: `content-aggregator/` — 数据去向
