.PHONY: help install dev-api dev-crawler dev-crawler-beat dev-frontend dev build deploy stop clean

help: ## 显示帮助信息
	@echo "TrendScope 开发/部署命令:"
	@echo "  make install          安装依赖 (pip install -e)"
	@echo "  make dev-api          启动 FastAPI API (:8001)"
	@echo "  make dev-crawler      启动 Celery Worker"
	@echo "  make dev-crawler-beat 启动 Celery Beat"
	@echo "  make dev-frontend     启动 Next.js 前端 (:3000)"
	@echo "  make dev              显示启动说明"
	@echo "  make deploy           生产环境启动"
	@echo "  make stop             生产环境停止"
	@echo "  make clean            清理"

install: ## 安装 TrendScope 和依赖
	pip install -e .
	pip install -e ../rpa-common 2>/dev/null || echo "rpa-common 未找到（可选）"

dev-api: ## 启动 FastAPI API（开发）
	uvicorn trendscope.api.main:app --reload --port 8001

dev-crawler: ## 启动 Celery Worker
	cd crawler-engine && celery -A scheduler.celery_app worker -l info -c 4

dev-crawler-beat: ## 启动 Celery Beat
	cd crawler-engine && celery -A scheduler.celery_app beat -l info

dev-frontend: ## 启动前端（开发）
	cd frontend && npm run dev

dev: ## 显示启动说明
	@echo "请在不同终端运行:"
	@echo "  make dev-api"
	@echo "  make dev-crawler"
	@echo "  make dev-frontend"

deploy: ## 生产环境启动（需 root）
	bash deploy/start.sh

stop: ## 生产环境停止
	bash deploy/stop.sh

build: ## 构建前端生产版本
	cd frontend && npm run build

clean: ## 清理
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/.next
