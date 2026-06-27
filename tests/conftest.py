"""Pytest 配置"""
import os
import sys

# 必须在导入 trendscope 模块前设置 JWT 密钥，否则 config.py 启动时抛出 RuntimeError
os.environ.setdefault("PO_SECRET_KEY", "test-secret-key-for-trendscope-tests")

# 将项目根目录加入 Python 路径
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 将 crawler-engine 加入路径
_crawler_path = os.path.join(_project_root, "crawler-engine")
if _crawler_path not in sys.path:
    sys.path.insert(0, _crawler_path)
