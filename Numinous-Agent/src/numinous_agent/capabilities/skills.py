"""技能注册：技能（可复用能力单元）的注册与发现。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Skill:
    """技能定义：由多个步骤/工具组合而成的可复用能力。"""

    name: str
    description: str
    handler: Callable[..., Any]
    required_tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SkillRegistry:
    """技能注册表。"""

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    def register(
        self,
        name: str,
        description: str = "",
        required_tools: Optional[List[str]] = None,
        **metadata: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """装饰器形式注册技能。"""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._skills[name] = Skill(
                name=name,
                description=description or (func.__doc__ or "").strip(),
                handler=func,
                required_tools=required_tools or [],
                metadata=metadata,
            )
            return func

        return decorator

    def add(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def invoke(self, name: str, *args: Any, **kwargs: Any) -> Any:
        skill = self._skills.get(name)
        if skill is None:
            raise KeyError(f"未知技能: {name}")
        return skill.handler(*args, **kwargs)

    def list(self) -> List[Skill]:
        return list(self._skills.values())

    def names(self) -> List[str]:
        return list(self._skills.keys())
