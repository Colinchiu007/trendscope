FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Playwright 浏览器
RUN pip install playwright && playwright install --with-deps chromium

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Celery Worker
CMD ["celery", "-A", "scheduler.celery_app", "worker", "-l", "info", "-c", "4"]
