"""上下文管理：管理会话上下文、历史记录与状态持久化。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """会话中的一条消息。"""

    role: str  # "user" / "assistant" / "system"
    content: str
    meta: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """会话上下文管理器。"""

    def __init__(self, max_history: int = 100) -> None:
        self._sessions: Dict[str, List[Message]] = {}
        self._state: Dict[str, Dict[str, Any]] = {}
        self.max_history = max_history

    def get_or_create(self, session_id: str) -> List[Message]:
        """获取会话历史，不存在则创建。"""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        return self._sessions[session_id]

    def add(self, session_id: str, role: str, content: str, **meta: Any) -> None:
        """向会话追加一条消息。"""
        history = self.get_or_create(session_id)
        history.append(Message(role=role, content=content, meta=meta))
        if len(history) > self.max_history:
            del history[: len(history) - self.max_history]

    def history(self, session_id: str) -> List[Message]:
        """返回会话历史副本。"""
        return list(self.get_or_create(session_id))

    def set_state(self, session_id: str, key: str, value: Any) -> None:
        """设置会话状态。"""
        self._state.setdefault(session_id, {})[key] = value

    def get_state(self, session_id: str, key: str, default: Any = None) -> Any:
        """获取会话状态。"""
        return self._state.get(session_id, {}).get(key, default)

    def clear(self, session_id: str) -> None:
        """清空指定会话。"""
        self._sessions.pop(session_id, None)
        self._state.pop(session_id, None)
