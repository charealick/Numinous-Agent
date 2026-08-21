"""MCP 客户端：基于 Model Context Protocol 与外部 MCP 服务器通信。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class MCPServer:
    """一个 MCP 服务器连接描述。

    MVP 阶段通过 `handler` 提供调用能力；真实实现可替换为
    基于 stdio / SSE / HTTP 的协议传输层。
    """

    name: str
    url: str = ""
    handler: Optional[Callable[..., Any]] = None
    tools: List[str] = field(default_factory=list)


class MCPClient:
    """管理多个 MCP 服务器，并提供统一的工具调用入口。"""

    def __init__(self) -> None:
        self._servers: Dict[str, MCPServer] = {}

    def connect(self, server: MCPServer) -> None:
        """注册（连接）一个 MCP 服务器。"""
        self._servers[server.name] = server

    def disconnect(self, name: str) -> None:
        self._servers.pop(name, None)

    def servers(self) -> List[str]:
        return list(self._servers.keys())

    def list_tools(self, server: Optional[str] = None) -> Dict[str, List[str]]:
        """列出（全部或指定）服务器提供的工具。"""
        if server:
            srv = self._servers.get(server)
            return {server: list(srv.tools)} if srv else {}
        return {name: list(srv.tools) for name, srv in self._servers.items()}

    def call_tool(self, server: str, tool: str, **kwargs: Any) -> Any:
        """调用指定服务器上的工具。"""
        srv = self._servers.get(server)
        if srv is None:
            raise KeyError(f"未连接的 MCP 服务器: {server}")
        if srv.handler is None:
            raise RuntimeError(f"MCP 服务器 {server!r} 未提供处理器")
        return srv.handler(tool, **kwargs)
