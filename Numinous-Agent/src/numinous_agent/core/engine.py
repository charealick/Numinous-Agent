"""执行引擎：核心调度中枢，统一编排各能力组件。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..capabilities import (
    Agent,
    ContextManager,
    MCPClient,
    PermissionManager,
    SkillRegistry,
    ToolRegistry,
)
from .event_bus import EventBus
from .scheduler import Scheduler


@dataclass
class EngineConfig:
    """引擎配置。"""

    default_user: str = "anonymous"
    default_session: str = "default"


@dataclass
class RunResult:
    """一次请求的运行结果。"""

    ok: bool
    reply: str = ""
    error: str = ""
    events: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


class Engine:
    """执行引擎：汇聚调度器、事件总线与各能力组件。

    典型处理流程：
        handle -> 事件(开始) -> 权限校验 -> 读取上下文
                -> Agent 推理 -> 写入上下文 -> 事件(结束)
    """

    def __init__(
        self,
        agent: Optional[Agent] = None,
        config: Optional[EngineConfig] = None,
    ) -> None:
        self.config = config or EngineConfig()
        self.scheduler = Scheduler()
        self.event_bus = EventBus()
        self.context = ContextManager()
        self.permissions = PermissionManager()
        self.tools = ToolRegistry()
        self.skills = SkillRegistry()
        self.mcp = MCPClient()
        self.agent = agent or Agent(
            llm=None,  # type: ignore[arg-type] - 由 Agent 内部提供默认
            tools=self.tools,
            skills=self.skills,
        )

    # ---- 生命周期 ----

    def emit(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.event_bus.emit(event_type, data=data, source="engine")

    def handle(
        self,
        prompt: str,
        user: Optional[str] = None,
        session: Optional[str] = None,
        required_permission: Optional[str] = None,
    ) -> RunResult:
        """处理一条用户输入，返回运行结果。"""
        user = user or self.config.default_user
        session = session or self.config.default_session
        result = RunResult(ok=True)

        self.emit("request.start", {"user": user, "session": session, "prompt": prompt})
        result.events.append("request.start")

        # 权限校验
        if required_permission:
            try:
                self.permissions.require(user, required_permission)
            except Exception as exc:  # noqa: BLE001
                result.ok = False
                result.error = str(exc)
                self.emit("request.denied", {"user": user, "reason": str(exc)})
                result.events.append("request.denied")
                return result

        # 读取上下文
        history = [
            {"role": m.role, "content": m.content}
            for m in self.context.history(session)
        ]
        self.context.add(session, "user", prompt)

        # Agent 推理
        try:
            reply = self.agent.run(prompt, history=history)
        except Exception as exc:  # noqa: BLE001
            result.ok = False
            result.error = str(exc)
            self.emit("request.error", {"reason": str(exc)})
            result.events.append("request.error")
            return result

        self.context.add(session, "assistant", reply)
        result.reply = reply
        self.emit("request.complete", {"user": user, "session": session})
        result.events.append("request.complete")
        return result

    def handle_async(self, prompt: str, **kwargs: Any) -> str:
        """提交任务到调度器异步执行，返回任务 ID。"""
        return self.scheduler.submit(self.handle, prompt, **kwargs)

    def flush(self) -> int:
        """执行调度器中所有待处理任务。"""
        return self.scheduler.run_all()
