#!/usr/bin/env python3
"""
TrendScope 凭证加载工具
从数据库中读取平台凭证，输出为 shell 环境变量 export 语句。

用法:
    eval "$(/srv/projects/.venv/bin/python3 scripts/load_credentials.py)"

输出格式:
    export ZHIHU_COOKIE='xxx'
    export YOUTUBE_API_KEY='xxx'
    export TIKTOK_PROXY_URL='xxx'
    export TWITTER_BEARER_TOKEN='xxx'
"""
import json
import os
import sys


# 字段到环境变量的映射
FIELD_ENV_MAP = {
    "zhihu": {"cookie": "ZHIHU_COOKIE"},
    "youtube": {"api_key": "YOUTUBE_API_KEY"},
    "tiktok": {"proxy_url": "TIKTOK_PROXY_URL"},
    "x_twitter": {"bearer_token": "TWITTER_BEARER_TOKEN"},
}


def load_config() -> dict:
    """读取配置文件确定数据库连接"""
    # 优先从环境变量读取
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return _load_from_db(db_url)

    # 尝试从 common 配置读取
    config_paths = [
        "config/common.yaml",
        "trendscope/config/common.yaml",
        "/srv/projects/trendscope/config/common.yaml",
        "/srv/projects/trendscope/trendscope/config/common.yaml",
    ]
    for cp in config_paths:
        if os.path.exists(cp):
            try:
                import yaml
                with open(cp) as f:
                    cfg = yaml.safe_load(f)
                db_cfg = cfg.get("database", {})
                user = db_cfg.get("user", "trendscope")
                password = db_cfg.get("password", "")
                host = db_cfg.get("host", "localhost")
                port = db_cfg.get("port", 5432)
                database = db_cfg.get("database", "trendscope")
                db_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
                return _load_from_db(db_url)
            except Exception as e:
                print(f"# 警告: 读取配置文件失败 {cp}: {e}", file=sys.stderr)
                continue

    print("# 错误: 无法确定数据库连接", file=sys.stderr)
    sys.exit(1)


def _load_from_db(db_url: str) -> dict:
    """从数据库加载凭证"""
    try:
        import asyncio
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        async def _fetch():
            engine = create_async_engine(db_url)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT code, crawl_config FROM platforms WHERE is_active = true")
                )
                rows = result.all()
            await engine.dispose()
            return rows

        rows = asyncio.run(_fetch())
    except Exception as e:
        print(f"# 错误: 数据库查询失败: {e}", file=sys.stderr)
        # 降级：检查环境变量是否已设置（本地开发场景）
        return _check_existing_env()

    env_map = {}
    for code, crawl_config in rows:
        if code not in FIELD_ENV_MAP:
            continue
        config = crawl_config or {}
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = {}
        field_map = FIELD_ENV_MAP[code]
        for field_key, env_var in field_map.items():
            value = config.get(field_key, "")
            if value:
                env_map[env_var] = value
    return env_map


def _check_existing_env() -> dict:
    """降级：检查环境变量是否已设置"""
    env_map = {}
    for code, field_map in FIELD_ENV_MAP.items():
        for field_key, env_var in field_map.items():
            value = os.environ.get(env_var, "")
            if value:
                env_map[env_var] = value
    return env_map


def main():
    env_map = load_config()
    for var, val in env_map.items():
        # 转义单引号
        escaped = val.replace("'", "'\\''")
        print(f"export {var}='{escaped}'")

    if not env_map:
        print("# 未找到任何凭证", file=sys.stderr)


if __name__ == "__main__":
    main()
