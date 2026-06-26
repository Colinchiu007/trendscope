#!/bin/bash
# TrendScope 生产环境启动脚本
# 部署路径: /srv/projects/trendscope/
set -e

PROJECT_DIR="/srv/projects/trendscope"
cd "$PROJECT_DIR"

# 1. 安装依赖
echo "=== 安装依赖 ==="
pip install -e . 2>/dev/null || echo "trendscope install skipped (may already be installed)"
pip install -e /srv/projects/content-aggregator/backend/ 2>/dev/null || echo "content-aggregator not installed (optional)"
pip install -e /srv/projects/rpa-common/ 2>/dev/null || echo "rpa-common not found (optional)"

# 2. 启动 API (systemd 管理)
echo "=== 启动 API :8001 ==="
systemctl start trendscope-api

# 3. 启动采集引擎 (后台)
echo "=== 启动 Celery Worker ==="
# --include=app.tasks 加载 content-aggregator 的异步任务（如已安装）
nohup celery -A trendscope.crawler.celery_app worker \
    --include=app.tasks -l info -c 4 --pidfile=/var/run/trendscope-celery.pid \
    > /var/log/trendscope/celery.log 2>&1 &
echo $! > /var/run/trendscope-celery-worker.pid

# 4. 启动 Celery Beat 调度器 (后台)
echo "=== 启动 Celery Beat ==="
nohup celery -A trendscope.crawler.celery_app beat \
    -l info --pidfile=/var/run/trendscope-beat.pid \
    > /var/log/trendscope/beat.log 2>&1 &
echo $! > /var/run/trendscope-beat.pid

# 5. 启动前端 (systemd 管理)
echo "=== 启动前端 :3000 ==="
systemctl start trendscope-frontend

echo "=== 全部服务已启动 ==="
echo "  API:       http://localhost:8001/health"
echo "  前端:      http://localhost:3000"
echo "  日志目录:  /var/log/trendscope/"
