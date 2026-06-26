# TrendScope - Push to GitHub
# Usage: $env:GH_TOKEN = "your_token"; .\scripts\push-to-github.ps1

param(
    [string]$Token = $env:GH_TOKEN
)

if (-not $Token) {
    Write-Host "Please set GH_TOKEN first:" -ForegroundColor Red
    Write-Host '  $env:GH_TOKEN = "github_pat_xxx"' -ForegroundColor Yellow
    Write-Host "  .\scripts\push-to-github.ps1" -ForegroundColor Yellow
    exit 1
}

Set-Location "D:\Data\projects\tendscope"

# 1. Init git
Write-Host "[1/6] Init git..." -ForegroundColor Cyan
git init 2>$null
git config user.name "TrendScope"
git config user.email "dev@trendscope.cn"

# 2. Get GitHub username
Write-Host "[2/6] Get GitHub user..." -ForegroundColor Cyan
$headers = @{ Authorization = "Bearer $Token"; Accept = "application/vnd.github+json" }
$userResponse = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers
$username = $userResponse.login
Write-Host "  Username: $username" -ForegroundColor Green

# 3. Create repo
Write-Host "[3/6] Create repo..." -ForegroundColor Cyan
$body = @{
    name = "trendscope"
    description = "TrendScope - Multi-platform trending aggregation engine (12 platforms)"
    private = $false
    has_issues = $true
    has_wiki = $true
} | ConvertTo-Json

try {
    Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method Post -Headers $headers -Body $body -ContentType "application/json" | Out-Null
    Write-Host "  Repo created: $username/trendscope" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "  Repo already exists, skip creation" -ForegroundColor Yellow
    } else {
        throw $_
    }
}

# 4. Clean up deprecated Go code
Write-Host "[4/6] Clean up..." -ForegroundColor Cyan
if (Test-Path "api-gateway") {
    Remove-Item -Recurse -Force "api-gateway"
    Write-Host "  Removed deprecated api-gateway/" -ForegroundColor Yellow
}

# 5. Add and commit
Write-Host "[5/6] Commit..." -ForegroundColor Cyan
git add -A
$commitMsg = @"
Initial commit: TrendScope v0.1 - Multi-platform trending aggregation engine

Features:
- 12 platform spiders (Weibo/Baidu/Zhihu/Bilibili/Toutiao/Douyin/Xiaohongshu/YouTube/X/WeChat/Shipinhao/TikTok)
- Python/FastAPI backend API (30+ endpoints)
- Next.js 14 frontend (9 pages)
- Vue3 admin dashboard (5 pages)
- Redis 4-level cache + PostgreSQL 9 tables
- Pipeline integration with content-aggregator
- SEO (sitemap/robots/JSON-LD/OG)
- Security (CSP/HSTS/JWT/rate-limit)
- 56 unit/integration tests + k6 load test + smoke test

Tech Stack: Python 3.12 + FastAPI + Next.js 14 + Vue 3 + PostgreSQL + Redis + Celery
"@
git commit -m $commitMsg

# 6. Push
Write-Host "[6/6] Push to GitHub..." -ForegroundColor Cyan
$remoteUrl = "https://oauth2:${Token}@github.com/${username}/trendscope.git"
git remote add origin $remoteUrl 2>$null
git remote set-url origin $remoteUrl
git branch -M main
git push -u origin main

Write-Host ""
Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "Repo: https://github.com/$username/trendscope" -ForegroundColor Cyan

# Clean up token from remote URL
git remote set-url origin "https://github.com/${username}/trendscope.git"
Write-Host "Token removed from remote URL" -ForegroundColor Yellow
