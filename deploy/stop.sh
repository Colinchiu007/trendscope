#!/bin/bash
# TrendScope 停止脚本
set -e

echo "=== 停止 TrendScope 服务 ==="

for service in api celery-worker beat frontend; do
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
