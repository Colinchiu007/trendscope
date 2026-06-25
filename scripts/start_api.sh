#!/bin/bash
# TrendScope API 启动脚本
# 确保加载 .env 环境变量后再启动
set -e

cd /srv/projects/trendscope

# 从 .env 文件加载数据库配置
export TS_DB_USER=tendscope
export TS_DB_PASSWORD=tendscope_dev
export TS_DB_NAME=tendscope
export TS_DB_HOST=localhost
export TS_DB_PORT=5432
export TS_REDIS_HOST=localhost
export TS_REDIS_PORT=6379
export TS_REDIS_DB=3

# 共享模块（shared-models）在 venv 中
export PYTHONPATH=/srv/projects/.venv/lib/python3.11/site-packages:$PYTHONPATH

LOG_FILE=/var/log/trendscope/api.log
mkdir -p /var/log/trendscope

echo "=== TrendScope API starting at $(date) ===" >> "$LOG_FILE"
exec /usr/local/bin/uvicorn trendscope.api.main:app \
    --host 0.0.0.0 --port 8001 \
    >> "$LOG_FILE" 2>&1
