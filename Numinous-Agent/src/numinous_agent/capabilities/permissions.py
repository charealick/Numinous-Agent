"""权限控制：细粒度的权限校验与访问控制。"""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Set


class PermissionError(RuntimeError):
    """权限校验失败时抛出。"""


class PermissionManager:
    """基于角色-权限模型的访问控制。"""

    def __init__(self) -> None:
        self._roles: Dict[str, Set[str]] = {}
        self._user_roles: Dict[str, Set[str]] = {}

    def add_role(self, role: str, permissions: Iterable[str]) -> None:
        """定义角色及其权限。"""
        self._roles.setdefault(role, set()).update(permissions)

    def assign_role(self, user: str, role: str) -> None:
        """将角色授予用户。"""
        if role not in self._roles:
            raise PermissionError(f"未定义的角色: {role}")
        self._user_roles.setdefault(user, set()).add(role)

    def user_permissions(self, user: str) -> Set[str]:
        """返回用户拥有的全部权限。"""
        perms: Set[str] = set()
        for role in self._user_roles.get(user, set()):
            perms.update(self._roles.get(role, set()))
        return perms

    def check(self, user: str, permission: str) -> bool:
        """校验用户是否拥有某权限。"""
        return permission in self.user_permissions(user)

    def require(self, user: str, permission: str) -> None:
        """校验权限，失败抛出 PermissionError。"""
        if not self.check(user, permission):
            raise PermissionError(f"用户 {user!r} 缺少权限 {permission!r}")
