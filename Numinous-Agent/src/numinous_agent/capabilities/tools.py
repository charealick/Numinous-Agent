"""工具调用：工具的定义、注册与调用管理。"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    """工具描述对象。"""

    name: str
    description: str
    func: Callable[..., Any]
    parameters: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    """工具注册表。"""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """装饰器形式注册工具。

        用法:
            @registry.register("add", "两数相加")
            def add(a: int, b: int) -> int:
                return a + b
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            params = dict(parameters or {})
            if not params:
                params = self._infer_params(func)
            self._tools[name] = Tool(
                name=name,
                description=description or (func.__doc__ or "").strip(),
                func=func,
                parameters=params,
            )
            return func

        return decorator

    def add(self, tool: Tool) -> None:
        """直接注册一个工具对象。"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def call(self, name: str, **kwargs: Any) -> Any:
        """按名称调用工具。"""
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(f"未知工具: {name}")
        return tool.func(**kwargs)

    def list(self) -> List[Tool]:
        return list(self._tools.values())

    def names(self) -> List[str]:
        return list(self._tools.keys())

    @staticmethod
    def _infer_params(func: Callable[..., Any]) -> Dict[str, Any]:
        """从函数签名推断参数 schema（简易版）。"""
        schema: Dict[str, Any] = {}
        for pname, param in inspect.signature(func).parameters.items():
            if pname in ("self", "cls"):
                continue
            annotation = param.annotation
            ptype = "string"
            if annotation is not inspect.Parameter.empty:
                ptype = {
                    int: "integer",
                    float: "number",
                    bool: "boolean",
                    str: "string",
                }.get(annotation, "string")
            schema[pname] = {
                "type": ptype,
                "required": param.default is inspect.Parameter.empty,
            }
        return schema
