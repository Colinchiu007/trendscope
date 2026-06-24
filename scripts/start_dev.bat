@echo off
REM TrendScope 开发环境启动脚本
REM 用法: start_dev.bat [weibo]
REM       先启动 API, 再采集指定平台数据

echo ========================================
echo  TrendScope 开发环境启动
echo ========================================

REM 设置环境变量（使用 Docker 的 PG + Redis）
set TS_DB_HOST=localhost
set TS_DB_PORT=5432
set TS_DB_USER=tendscope
set TS_DB_PASSWORD=tendscope_dev
set TS_DB_NAME=tendscope
set TS_REDIS_HOST=localhost
set TS_REDIS_PORT=6379
set FEATURE_GATES_PATH=..\feature_gates.yaml

REM 1. 初始化数据库（首次需要）
echo [1/3] 初始化数据库表...
python scripts\init_db.py
if %ERRORLEVEL% neq 0 (
    echo 数据库初始化失败！请确认 Docker 是否已启动。
    pause
    exit /b 1
)

REM 2. 启动 API
echo [2/3] 启动 TrendScope API (port 8001)...
start "TrendScope API" cmd /c "uvicorn trendscope.api.main:app --reload --port 8001"

REM 等待 API 就绪
timeout /t 3 /nobreak >nul

REM 3. 采集数据
set PLATFORM=%1
if "%PLATFORM%"=="" set PLATFORM=weibo

echo [3/3] 采集 %PLATFORM% 热榜数据...
python scripts\crawl_once.py %PLATFORM%

echo.
echo ========================================
echo  启动完成！
echo  API:      http://localhost:8001
echo  Docs:     http://localhost:8001/docs
echo  热榜:     http://localhost:8001/api/v1/trending
echo  采集:     %PLATFORM%
echo ========================================
pause
