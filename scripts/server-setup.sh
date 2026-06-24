#!/bin/bash
# TrendScope 服务器部署脚本
# 用法: ssh -i D:\Data\Aliyun\Colin01-opencode.pem root@39.105.42.85 'bash -s' < scripts/server-setup.sh
# 或者先 SSH 上去，再执行:
#   ssh -i D:\Data\Aliyun\Colin01-opencode.pem root@39.105.42.85
#   bash /srv/projects/trendscope/scripts/server-setup.sh

set -e

PROJECTS_DIR="/srv/projects"
TRENDSCOPE_DIR="${PROJECTS_DIR}/trendscope"
GITHUB_REPO="https://github.com/Colinchiu007/trendscope.git"

echo "========================================="
echo " TrendScope Server Setup"
echo "========================================="

# ==========================================
# Step 1: Clone project from GitHub
# ==========================================
echo ""
echo "[1/7] Cloning TrendScope from GitHub..."
if [ -d "$TRENDSCOPE_DIR" ]; then
    echo "  Directory already exists, pulling latest..."
    cd "$TRENDSCOPE_DIR"
    git pull origin main
else
    cd "$PROJECTS_DIR"
    git clone "$GITHUB_REPO" trendscope
    cd "$TRENDSCOPE_DIR"
fi
echo "  Done."

# ==========================================
# Step 2: Initialize database tables
# ==========================================
echo ""
echo "[2/7] Initializing PostgreSQL tables..."
if command -v psql &> /dev/null; then
    # Try to find the existing database
    DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='trendscope'" 2>/dev/null || echo "")
    if [ "$DB_EXISTS" = "1" ]; then
        echo "  Database 'trendscope' already exists"
    else
        echo "  Creating database 'trendscope'..."
        sudo -u postgres psql -c "CREATE DATABASE trendscope;" 2>/dev/null || \
            echo "  Database may already exist or need manual creation"
    fi

    # Run init SQL
    if [ -f "scripts/init-db.sql" ]; then
        psql -U trendscope -d trendscope -f scripts/init-db.sql 2>/dev/null && \
            echo "  Tables created OK" || \
            echo "  WARNING: Could not run init-db.sql. Check DB credentials."
    fi
else
    echo "  psql not found, skip DB init. Run scripts/init-db.sql manually."
fi

# ==========================================
# Step 3: Install Python dependencies
# ==========================================
echo ""
echo "[3/7] Installing Python dependencies..."
if [ -d "${PROJECTS_DIR}/.venv" ]; then
    source "${PROJECTS_DIR}/.venv/bin/activate"
    echo "  Using existing virtual env"
else
    python3 -m venv "${PROJECTS_DIR}/.venv"
    source "${PROJECTS_DIR}/.venv/bin/activate"
    echo "  Created new virtual env"
fi

pip install -e . 2>/dev/null || echo "  WARNING: pip install -e . failed (check setup.py)"

# Install crawler extras
pip install "celery[redis]>=5.4" beautifulsoup4 lxml playwright httpx 2>/dev/null || true
pip install fake-useragent tenacity loguru pyyaml 2>/dev/null || true

# Install shared-models (if present)
if [ -d "${PROJECTS_DIR}/shared-models" ]; then
    pip install -e "${PROJECTS_DIR}/shared-models" 2>/dev/null || true
    echo "  shared-models installed"
fi

echo "  Done."

# ==========================================
# Step 4: Set up rpa-common (shared module)
# ==========================================
echo ""
echo "[4/7] Setting up rpa-common..."
RPA_DIR="${PROJECTS_DIR}/rpa-common"
if [ ! -d "$RPA_DIR" ]; then
    mkdir -p "$RPA_DIR/rpa_common"
    cat > "$RPA_DIR/setup.py" << 'SETUPEOF'
from setuptools import setup, find_packages
setup(
    name="rpa-common",
    version="0.1.0",
    description="Shared RPA utilities for TrendScope and Multi-Publish",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=["httpx>=0.27", "playwright>=1.45", "fake-useragent>=1.5", "redis>=5.0"],
)
SETUPEOF

    cat > "$RPA_DIR/rpa_common/__init__.py" << 'INITEOF'
"""rpa-common: Shared RPA infrastructure"""
INITEOF

    # Copy from trendscope's anti_anti_spider as base
    if [ -d "${TRENDSCOPE_DIR}/crawler-engine/anti_anti_spider" ]; then
        cp -r "${TRENDSCOPE_DIR}/crawler-engine/anti_anti_spider/"* "$RPA_DIR/rpa_common/" 2>/dev/null || true
    fi

    pip install -e "$RPA_DIR" 2>/dev/null || echo "  WARNING: rpa-common install failed"
    echo "  rpa-common created at $RPA_DIR"
else
    echo "  rpa-common already exists"
fi

# ==========================================
# Step 5: Add TrendScope to shared-models
# ==========================================
echo ""
echo "[5/7] Setting up shared-models integration..."
SM_DIR="${PROJECTS_DIR}/shared-models"
if [ -d "$SM_DIR" ]; then
    TREND_MODEL_DIR="${SM_DIR}/trendscope"
    if [ ! -d "$TREND_MODEL_DIR" ]; then
        mkdir -p "$TREND_MODEL_DIR"
        cat > "${TREND_MODEL_DIR}/__init__.py" << 'PYEOF'
"""TrendScope shared Pydantic models"""
PYEOF

        cat > "${TREND_MODEL_DIR}/models.py" << 'PYEOF'
"""TrendScope data models for cross-module use"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class PlatformModel(BaseModel):
    code: str
    name: str
    icon_url: str = ""
    category: str = "general"
    is_active: bool = True

class TrendingTopicModel(BaseModel):
    platform_code: str
    rank: int
    title: str
    hot_value: str
    hot_value_norm: float = 0.0
    topic_url: Optional[str] = None
    category: str = "general"
    snapshot_at: datetime

class HotArticleModel(BaseModel):
    platform_code: str
    title: str
    summary: Optional[str] = None
    source_url: str
    author_name: Optional[str] = None
    read_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    images: list[dict] = []
    publish_at: Optional[datetime] = None

class TrendingPipelineItem(BaseModel):
    """Item sent to content-aggregator pipeline"""
    source_url: str
    title: str
    platform_code: str
    summary: Optional[str] = None
    author_name: Optional[str] = None
    read_count: int = 0
    like_count: int = 0
PYEOF
        echo "  shared-models/trendscope/ created"
    else
        echo "  shared-models/trendscope/ already exists"
    fi

    pip install -e "$SM_DIR" 2>/dev/null || true
else
    echo "  shared-models/ not found, skip"
fi

# ==========================================
# Step 6: Add feature gates
# ==========================================
echo ""
echo "[6/7] Adding feature gates..."
GATES_FILE="${PROJECTS_DIR}/feature_gates.yaml"
if [ -f "$GATES_FILE" ]; then
    # Add trending gates if not present
    if ! grep -q "trending_feed" "$GATES_FILE"; then
        cat >> "$GATES_FILE" << 'GATESEOF'

# TrendScope - Multi-platform trending aggregation
trending_feed:           { tier: 1, enabled: true }   # Trending display (C-side)
trending_user_favorites: { tier: 2, enabled: true }   # User favorites
trending_user_subs:      { tier: 2, enabled: true }   # User subscriptions
trending_to_pipeline:    { tier: 2, enabled: false }  # Auto-feed into content pipeline
trending_api_partner:    { tier: 2, enabled: true }   # 3rd-party API access
GATESEOF
        echo "  Added trending gates to feature_gates.yaml"
    else
        echo "  Trending gates already present"
    fi
else
    echo "  feature_gates.yaml not found, skip"
fi

# ==========================================
# Step 7: Register in platform-orchestrator
# ==========================================
echo ""
echo "[7/7] Registering in platform-orchestrator..."
PO_DIR="${PROJECTS_DIR}/platform-orchestrator"
if [ -d "$PO_DIR" ]; then
    PO_MAIN="${PO_DIR}/main.py"
    if [ -f "$PO_MAIN" ]; then
        if ! grep -q "trendscope" "$PO_MAIN"; then
            echo "  NOTE: Add this to ${PO_MAIN}:"
            echo "  ---"
            echo "  from trendscope.api.main import app as trendscope_app"
            echo "  app.mount('/trendscope', trendscope_app)"
            echo "  ---"
        else
            echo "  TrendScope already registered in orchestrator"
        fi
    fi
else
    echo "  platform-orchestrator not found, skip"
fi

# ==========================================
# Done
# ==========================================
echo ""
echo "========================================="
echo " Setup Complete!"
echo "========================================="
echo ""
echo "To start TrendScope:"
echo "  cd ${TRENDSCOPE_DIR}"
echo "  source ${PROJECTS_DIR}/.venv/bin/activate"
echo "  uvicorn trendscope.api.main:app --host 0.0.0.0 --port 8001 &"
echo "  cd frontend && npm run dev &"
echo ""
echo "Verify: curl http://localhost:8001/health"
