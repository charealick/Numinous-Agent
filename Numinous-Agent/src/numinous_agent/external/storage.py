"""存储适配：提供简单的键值持久化（内存实现）。"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


class InMemoryStore:
    """内存键值存储，可选导出/导入 JSON。"""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def dump(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
