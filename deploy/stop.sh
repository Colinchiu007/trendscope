#!/bin/bash
# TrendScope 停止脚本
set -e

echo "=== 停止 TrendScope 服务 ==="

# API + 前端用 systemd 管理
echo "  停止 API"
systemctl stop trendscope-api 2>/dev/null || echo "  API 未运行"

echo "  停止前端"
systemctl stop trendscope-frontend 2>/dev/null || echo "  前端未运行"

# Celery Worker + Beat 用 pidfile 停止
for service in celery-worker beat; do
  pidfile="/var/run/trendscope-${service}.pid"
  if [ -f "$pidfile" ]; then
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      echo "  停止 $service (PID: $pid)"
      kill "$pid" && rm "$pidfile"
    else
      rm "$pidfile"
    fi
  fi
done

# 确保所有 celery 进程已停止
pkill -f "trendscope.crawler.celery_app" 2>/dev/null || true

echo "=== 全部服务已停止 ==="
