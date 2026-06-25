#!/bin/bash
# TrendScope 定时采集脚本 - 被 crontab 调用
# 覆盖 12 个平台，分三层避免超时阻塞
set -e
cd /srv/projects/trendscope

LOG_DIR=/var/log/trendscope
mkdir -p $LOG_DIR
LOG_FILE=$LOG_DIR/crawl-$(date +%Y%m%d-%H%M).log
CRED_SCRIPT=/srv/projects/.venv/bin/python3

echo "===== TrendScope 定时采集 $(date) =====" > $LOG_FILE

# 加载平台凭证（从 DB 读取）—— 知乎 Cookie、YouTube/TikTok/X API Key
echo "[$(date +%H:%M:%S)] 加载平台凭证..." >> $LOG_FILE
eval "$($CRED_SCRIPT scripts/load_credentials.py)" >> $LOG_FILE 2>&1
echo "[$(date +%H:%M:%S)] 凭证加载完成" >> $LOG_FILE

# 统计
TOTAL_OK=0
TOTAL_FAIL=0

crawl_platform() {
    local platform=$1
    local timeout=${2:-30}
    echo "[$(date +%H:%M:%S)] 开始采集: $platform" >> $LOG_FILE
    timeout $timeout $CRED_SCRIPT scripts/crawl_once.py $platform >> $LOG_FILE 2>&1
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        TOTAL_OK=$((TOTAL_OK + 1))
    else
        TOTAL_FAIL=$((TOTAL_FAIL + 1))
    fi
    echo "[$(date +%H:%M:%S)] 完成: $platform (exit $exit_code)" >> $LOG_FILE
    sleep 1
}

# 第一层：HTTP 快速平台（通常 <5s/个）
for platform in baidu bilibili; do
    crawl_platform $platform 30
done

# 第二层：Playwright 平台（启动浏览器较慢，给更多时间）
for platform in weibo zhihu toutiao douyin xiaohongshu kuaishou; do
    crawl_platform $platform 60
done

# 第三层：较慢 / 可能超时的平台
crawl_platform weixin_article 60

# 第五层：需要 API Key 的平台（未配置则快速失败）
crawl_