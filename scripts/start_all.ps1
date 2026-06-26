"""
一键启动 TrendScope（API + 前端 + 采集）

用法:
  powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1
  powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1 baidu  # 只采集百度
"""

param(
  [string]$Platform = "baidu"
)

$ErrorActionPreference = "Continue"
$ProjectRoot = "D:\Data\projects\trendscope"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TrendScope 一键启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 环境变量
$env:PROXY_MODE = "xiaoxiang"
$env:PROXY_API_URL = "https://api.xiaoxiangdaili.com/ip/get?appKey=1386969754732220416&appSecret=OTatCYNH&cnt=5&wt=text&method=http"
$env:TS_DB_HOST = "localhost"
$env:TS_DB_PORT = "5432"
$env:TS_DB_USER = "tendscope"
$env:TS_DB_PASSWORD = "tendscope_dev"
$env:TS_DB_NAME = "tendscope"
$env:TS_REDIS_HOST = "localhost"
$env:TS_REDIS_PORT = "6379"

Write-Host "[1/4] 采集 $Platform 热榜..." -ForegroundColor Yellow
Set-Location $ProjectRoot
python scripts/crawl_once.py $Platform
Write-Host "[1/4] 采集完成" -ForegroundColor Green

Write-Host "[2/4] 启动 API (port 8001)..." -ForegroundColor Yellow
$apiJob = Start-Job -ScriptBlock {
  param($root, $mode, $url)
  Set-Location $root
  $env:PROXY_MODE = $mode
  $env:PROXY_API_URL = $url
  uvicorn trendscope.api.main:app --reload --port 8001
} -ArgumentList $ProjectRoot, $env:PROXY_MODE, $env:PROXY_API_URL
Start-Sleep -Seconds 3
Write-Host "[2/4] API 已启动" -ForegroundColor Green

Write-Host "[3/4] 启动前端 (port 3000)..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
  param($root)
  Set-Location "$root\frontend"
  npm run dev
} -ArgumentList $ProjectRoot
Start-Sleep -Seconds 5
Write-Host "[3/4] 前端已启动" -ForegroundColor Green

Write-Host "[4/4] 验证..." -ForegroundColor Yellow
try {
  $apiTest = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/trending/$Platform" -UseBasicParsing -TimeoutSec 5
  $data = $apiTest.Content | ConvertFrom-Json
  $count = $data.data.items.Count
  Write-Host "[4/4] API 返回 $count 条数据" -ForegroundColor Green
} catch {
  Write-Host "[4/4] API 验证失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  启动完成!" -ForegroundColor Cyan
Write-Host "  API:      http://localhost:8001" -ForegroundColor White
Write-Host "  Docs:     http://localhost:8001/docs" -ForegroundColor White
Write-Host "  前端:     http://localhost:3000" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan

# 等待用户按任意键退出
Write-Host ""
Write-Host "按 Ctrl+C 停止所有服务" -ForegroundColor Yellow
while ($true) {
  Start-Sleep -Seconds 10
}
