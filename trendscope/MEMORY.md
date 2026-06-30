
## 2026-06-30: PRD 差距补齐 (auto-exec)

完成 22 个任务中的 22 个：
- **用户系统**: 邮箱验证码注册、密码修改(PUT)、账号注销(DELETE)、SSE通知流
- **热榜增强**: 关联话题推荐 API (GET /trending/{id}/related)
- **爬虫**: 新增视频号爬虫 (weixin_channel, 占位)
- **收藏夹**: FavoriteFolder CRUD (独立表)
- **订阅触发**: 采集完成时关键词匹配自动创建通知
- **管理后台**: 采集状态(GET /admin/crawl/status)、批量审核(POST /admin/articles/batch-audit)、用户统计(GET /admin/users/{id}/stats)
- **测试**: 新增 18 条测试 (user_auth + admin_api)，累计 82 passed
- **PRD**: 平台数 12→13，新功能标记
