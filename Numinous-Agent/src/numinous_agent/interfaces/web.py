"""Web 接口：基于 Python 标准库的零依赖 HTTP 服务。

提供 RESTful API 与静态 UI 文件服务：
- `POST /api/chat`   发送消息，返回 Agent 回复
- `GET  /api/models` 列出可用模型与当前模型
- `POST /api/models/switch` 切换模型
- `GET  /api/history` 获取会话历史
- `GET  /api/tools` / `GET /api/skills` 列出工具/技能
- `GET  /` 及静态资源 提供 Web UI
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from ..core import Engine

# Web UI 静态资源目录（相对本文件）
_STATIC_DIR = __import__("os").path.join(
    __import__("os").path.dirname(__file__), "static"
)


def build_web_engine(model_manager: Any = None, model: Optional[str] = None) -> Engine:
    """构建 Web 服务使用的引擎（复用 CLI 的组装逻辑，避免重复注册工具/技能）。"""
    from .cli import build_engine

    return build_engine(model_manager=model_manager, model=model)


class WebApp:
    """Web 应用：封装 Engine，提供请求处理逻辑。"""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    # ---- 业务处理 ----

    def chat(self, body: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (body.get("prompt") or "").strip()
        if not prompt:
            return {"ok": False, "error": "prompt 不能为空"}
        user = body.get("user") or self.engine.config.default_user
        session = body.get("session") or self.engine.config.default_session
        required = body.get("required_permission")

        result = self.engine.handle(
            prompt, user=user, session=session, required_permission=required
        )
        return {
            "ok": result.ok,
            "reply": result.reply,
            "error": result.error,
            "events": result.events,
        }

    def list_models(self) -> Dict[str, Any]:
        llm = self.engine.agent.llm
        return {
            "ok": True,
            "active": llm.model_name,
            "models": llm.list_models(),
        }

    def switch_model(self, body: Dict[str, Any]) -> Dict[str, Any]:
        name = (body.get("name") or "").strip()
        if not name:
            return {"ok": False, "error": "name 不能为空"}
        try:
            self.engine.agent.llm.switch_model(name)
            return {"ok": True, "active": self.engine.agent.llm.model_name}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

    def history(self, query: Dict[str, str]) -> Dict[str, Any]:
        session = query.get("session") or self.engine.config.default_session
        history = self.engine.context.history(session)
        return {
            "ok": True,
            "session": session,
            "messages": [{"role": m.role, "content": m.content} for m in history],
        }

    def list_tools(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "tools": [
                {"name": t.name, "description": t.description}
                for t in self.engine.tools.list()
            ],
        }

    def list_skills(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "skills": [
                {"name": s.name, "description": s.description}
                for s in self.engine.skills.list()
            ],
        }


class _RequestHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器。"""

    app: WebApp = None  # type: ignore[assignment]

    # 路由表
    _GET_ROUTES = {
        "/api/models": "list_models",
        "/api/history": "history",
        "/api/tools": "list_tools",
        "/api/skills": "list_skills",
    }
    _POST_ROUTES = {
        "/api/chat": "chat",
        "/api/models/switch": "switch_model",
    }

    def log_message(self, fmt: str, *args: Any) -> None:  # 静默默认日志
        pass

    # ---- 辅助 ----

    def _send_json(self, obj: Dict[str, Any], status: int = 200) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _serve_static(self, path: str) -> bool:
        import os

        if path in ("/", "/index.html"):
            path = "/index.html"
        file_path = os.path.normpath(os.path.join(_STATIC_DIR, path.lstrip("/")))
        if not file_path.startswith(_STATIC_DIR) or not os.path.isfile(file_path):
            return False

        content_type = "text/html; charset=utf-8"
        if file_path.endswith(".css"):
            content_type = "text/css; charset=utf-8"
        elif file_path.endswith(".js"):
            content_type = "application/javascript; charset=utf-8"

        with open(file_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        return True

    # ---- 路由分发 ----

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]

        # API 路由
        if path in self._GET_ROUTES:
            method = getattr(self.app, self._GET_ROUTES[path])
            if path == "/api/history":
                query = self._parse_query()
                result = method(query)
            else:
                result = method()
            self._send_json(result)
            return

        # 静态资源
        if self._serve_static(path):
            return

        self._send_json({"ok": False, "error": "Not Found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path not in self._POST_ROUTES:
            self._send_json({"ok": False, "error": "Not Found"}, status=404)
            return
        body = self._read_json_body()
        method = getattr(self.app, self._POST_ROUTES[path])
        result = method(body)
        self._send_json(result)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _parse_query(self) -> Dict[str, str]:
        from urllib.parse import parse_qs, urlparse

        query = urlparse(self.path).query
        params = parse_qs(query)
        return {k: v[0] for k, v in params.items()}


def run_server(
    engine: Engine,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    """启动 Web 服务（阻塞）。"""
    app = WebApp(engine)
    _RequestHandler.app = app

    server = ThreadingHTTPServer((host, port), _RequestHandler)
    print(f"Numinous-Agent Web 服务已启动: http://{host}:{port}")
    print("按 Ctrl+C 停止服务")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        server.server_close()
