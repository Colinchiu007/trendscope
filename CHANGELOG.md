# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-26

### Changed
- #2 writer.py: 采集写入 PG 后调用 `_invalidate_cache()` 清除 Redis 缓存，解决前端显示旧数据的问题
- #3 cookie_manager.py: TODO 转为详细 NOTE 说明
- #4 auth.py: `verify_api_key()` 改为异步 DB 查询（ApikeyRepo.va