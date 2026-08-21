"""环境变量加载：支持从 .env 文件读取配置（轻量实现，无第三方依赖）。"""

from __future__ import annotations

import os
from pathlib import Path


def find_project_root(start: str | Path | None = None) -> Path:
    """向上查找项目根目录（含 pyproject.toml 或 .git 的目录）。

    若找不到标记文件，则回退到当前工作目录。
    """
    current = Path(start or os.getcwd()).resolve()
    if current.is_file():
        current = current.parent
    for directory in (current, *current.parents):
        if (directory / "pyproject.toml").is_file() or (directory / ".git").exists():
            return directory
    return Path.cwd().resolve()


def load_dotenv(path: str | Path = ".env", override: bool = False) -> bool:
    """从 .env 文件加载环境变量到 os.environ。

    - 每一行形如 `KEY=VALUE` 或 `export KEY=VALUE`
    - 支持 `#` 注释与空行
    - 若 `override=False`（默认），已存在的环境变量不会被覆盖

    返回是否成功读取到文件。
    """
    env_path = Path(path)
    if not env_path.is_file():
        return False

    with open(env_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # 去除首尾引号
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if not key:
                continue
            if override or key not in os.environ:
                os.environ[key] = value

    return True
