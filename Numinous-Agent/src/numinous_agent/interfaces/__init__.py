"""接口层包：CLI 与 Web 入口。"""

from .cli import main
from .web import WebApp, run_server

__all__ = ["main", "WebApp", "run_server"]
