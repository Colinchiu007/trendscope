"""Pytest 配置"""
import os
import sys

# 将项目根目录加入 Python 路径
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 将 crawler-engine 加入路径
_crawler_path = os.path.join(_project_root, "crawler-engine")
if _crawler_path not in sys.path:
    sys.path.insert(0, _crawler_path)
