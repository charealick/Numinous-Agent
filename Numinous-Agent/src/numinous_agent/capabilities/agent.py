"""Agent 核心：智能体的核心推理与决策逻辑。"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class LLMProvider:
    """大模型接口抽象（MVP 默认使用可插拔的回调实现）。

    支持两种绑定方式：
    1. 传入一个固定 handler（callable）
    2. 传入一个 ModelManager，运行时可按名称切换模型
    """

    def __init__(
        self,
        handler: Optional[Callable[[str], str]] = None,
        model_manager: Any = None,
    ) -> None:
        self._handler = handler
        self._manager = model_manager
        self._model_name: Optional[str] = None

    @property
    def model_name(self) -> Optional[str]:
        """当前使用的模型名称（若通过 ModelManager 管理）。"""
        if self._manager is not None:
            return self._model_name or self._manager.active
        return self._model_name

    def switch_model(self, name: str) -> None:
        """切换到指定模型（需绑定 ModelManager）。"""
        if self._manager is None:
            raise RuntimeError("LLMProvider 未绑定 ModelManager")
        self._manager.use(name)
        self._model_name = name

    def list_models(self) -> list:
        """列出可用模型名称。"""
        if self._manager is not None:
            return self._manager.names()
        return []

    def generate(self, prompt: str) -> str:
        """生成回复。若未绑定任何处理器，抛出异常。"""
        if self._manager is not None:
            return self._manager.build_active()(prompt)
        if self._handler is not None:
            return self._handler(prompt)
        raise RuntimeError("LLMProvider 未绑定任何模型或处理器")


class Agent:
    """Agent 核心：编排大模型、工具与技能完成一轮对话。"""

    def __init__(
        self,
        llm: Optional[LLMProvider] = None,
        tools: Any = None,
        skills: Any = None,
    ) -> None:
        self.llm = llm or LLMProvider()
        self.tools = tools
        self.skills = skills

    def run(self, prompt: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """执行一轮推理，返回文本回复。

        MVP 阶段直接将用户输入交给 LLM；工具/技能调用留待扩展。
        """
        history = history or []
        context = "\n".join(f"{m['role']}: {m['content']}" for m in history[-10:])
        full_prompt = f"{context}\nuser: {prompt}".strip() if context else prompt
        return self.llm.generate(full_prompt)

    def use_tool(self, name: str, **kwargs: Any) -> Any:
        """调用已注册工具。"""
        if self.tools is None:
            raise RuntimeError("Agent 未绑定工具注册表")
        return self.tools.call(name, **kwargs)

    def use_skill(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """调用已注册技能。"""
        if self.skills is None:
            raise RuntimeError("Agent 未绑定技能注册表")
        return self.skills.invoke(name, *args, **kwargs)
