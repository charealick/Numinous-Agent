"""事件总线：基于发布/订阅模式的事件通信机制。"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Set

EventHandler = Callable[["Event"], None]


@dataclass
class Event:
    """事件对象。"""

    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""

    def __repr__(self) -> str:  # pragma: no cover
        return f"Event(type={self.type!r}, source={self.source!r})"


class EventBus:
    """简单的事件总线，支持订阅、退订与广播。"""

    def __init__(self) -> None:
        self._subscribers: Dict[str, Set[EventHandler]] = defaultdict(set)
        self._history: List[Event] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """订阅某类事件。"""
        self._subscribers[event_type].add(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """退订某类事件。"""
        self._subscribers[event_type].discard(handler)

    def emit(self, event_type: str, data: Dict[str, Any] | None = None, source: str = "") -> None:
        """发布事件并同步通知所有订阅者。"""
        event = Event(type=event_type, data=data or {}, source=source)
        self._history.append(event)
        for handler in list(self._subscribers[event_type]):
            handler(event)

    def history(self) -> List[Event]:
        """返回历史事件列表（用于调试）。"""
        return list(self._history)
