#!/bin/bash
# TrendScope 生产环境启动脚本
# 部署路径: /srv/projects/trendscope/
set -e

PROJECT_DIR="/srv/projects/trendscope"
cd "$PROJECT_DIR"

# 1. 安装依赖
echo "=== 安装依赖 ==="
pip install -e . 2>/dev/null || echo "trendscope install skipped (may already be installed)"
pip install -e /srv/projects/rpa-common/ 2>/dev/null || echo "rpa-common not found (optional)"

# 2. 初始化数据库（如果不在 Docker 中）
# psql -U trendscope -d trendscope -f scripts/init-db.sql

# 3. 启动 API (后台)
echo "=== 启动 API :8001 ==="
nohup uvicorn trendscope.api.main:app \
    --host 0.0.0.0 --port 8001 --workers 4 \
    --log-level info > /var/log/trendscope/api.log 2>&1 &
echo $! > /var/run/trendscope-api.pid

# 4. 启动采集引擎 (后台)
echo "=== 启动 Celery Worker ==="
nohup celery -A trendscope.crawler.celery_app worker \
    -l info -c 4 --pidfile=/var/run/trendscope-celery.pid \
    > /var/log/trendscope/celery.log 2>&1 &
echo $! > /var/run/trendscope-celery-worker.pid

# 5. 启动 Celery Beat 调度器 (后台)
echo "=== 启动 Celery Beat ==="
nohup celery -A trendscope.crawler.celery_app beat \
    -l info --pidfile=/var/run/trendscope-beat.pid \
    > /var/log/trendscope/beat.log 2>&1 &
echo $! > /var/run/trendscope-beat.pid

# 6. 启动前端 Next.js (后台)
echo "=== 启动前端 :3000 ==="
cd frontend
nohup npm run start > /var/log/trendscope/frontend.log 2>&1 &
echo $! > /var/run/trendscope-frontend.pid
cd ..

echo "=== 全部服务已启动 ==="
echo "  API:       http://localhost:8001/health"
echo "  前端:      http://localhost:3000"
echo "  日志目录:  /var/log/trendscope/"
