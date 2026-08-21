"""调度器：负责任务的调度、优先级管理与简单并发控制。"""

from __future__ import annotations

import heapq
import threading
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Dict, Optional


class TaskPriority(IntEnum):
    """任务优先级（数值越小越优先）。"""

    LOW = 30
    NORMAL = 20
    HIGH = 10
    CRITICAL = 0


@dataclass(order=True)
class _Task:
    """内部任务包装，用于优先队列排序。"""

    priority: int
    seq: int
    task_id: str = field(compare=False)
    func: Callable[..., Any] = field(compare=False)
    args: tuple = field(compare=False)
    kwargs: Dict[str, Any] = field(compare=False)


class Scheduler:
    """基于优先级队列的单线程任务调度器。"""

    def __init__(self) -> None:
        self._heap: list[_Task] = []
        self._seq = 0
        self._lock = threading.Lock()
        self._running = False

    def submit(
        self,
        func: Callable[..., Any],
        *args: Any,
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs: Any,
    ) -> str:
        """提交任务，返回任务 ID。"""
        task_id = uuid.uuid4().hex
        with self._lock:
            self._seq += 1
            task = _Task(
                priority=int(priority),
                seq=self._seq,
                task_id=task_id,
                func=func,
                args=args,
                kwargs=kwargs,
            )
            heapq.heappush(self._heap, task)
        return task_id

    def run_all(self) -> int:
        """同步执行队列中的所有任务，返回执行的任务数量。"""
        self._running = True
        executed = 0
        while True:
            with self._lock:
                if not self._heap:
                    break
                task = heapq.heappop(self._heap)
            try:
                task.func(*task.args, **task.kwargs)
            except Exception as exc:  # noqa: BLE001 - 调度器不中断其他任务
                print(f"[Scheduler] 任务 {task.task_id} 执行失败: {exc}")
            executed += 1
        self._running = False
        return executed

    @property
    def pending(self) -> int:
        with self._lock:
            return len(self._heap)

    @property
    def running(self) -> bool:
        return self._running
