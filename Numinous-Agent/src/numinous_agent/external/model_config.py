"""大模型选择与配置模块。

提供统一的模型配置、注册与工厂创建能力：
- `LLMConfig`：单个模型配置（provider、model、base_url、api_key 等）
- `ModelManager`：管理多个模型配置，支持按名称选择与切换
- 支持从 JSON 配置文件加载；api_key 支持从环境变量读取
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class LLMConfig:
    """单个大模型配置。

    `api_key` 支持环境变量注入：
    - 若配置中填写了 `api_key_env`，则从该环境变量读取
    - 否则若 `api_key` 为空，回退到 `LLM_API_KEY` 环境变量
    """

    name: str
    provider: str = "http"  # http / openai / custom
    model: str = ""
    base_url: str = ""
    api_key: str = ""
    api_key_env: str = ""
    timeout: float = 30.0
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMConfig":
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        known.setdefault("extra", {k: v for k, v in data.items() if k not in cls.__dataclass_fields__})
        return cls(**known)

    def resolve_api_key(self) -> str:
        """解析最终的 api_key：优先显式配置，其次环境变量。"""
        if self.api_key:
            return self.api_key
        env_name = self.api_key_env or "LLM_API_KEY"
        return os.environ.get(env_name, "")


class ModelManager:
    """大模型选择器：集中管理模型配置，支持按名称选用与切换。"""

    def __init__(self, configs: Optional[Dict[str, LLMConfig]] = None) -> None:
        self._configs: Dict[str, LLMConfig] = {}
        self._active: str = ""
        if configs:
            for cfg in configs.values():
                self.add(cfg)

    # ---- 配置管理 ----

    def add(self, config: LLMConfig) -> None:
        """添加一个模型配置；若为第一个，则自动设为当前模型。"""
        self._configs[config.name] = config
        if not self._active:
            self._active = config.name

    def remove(self, name: str) -> None:
        self._configs.pop(name, None)
        if self._active == name:
            self._active = next(iter(self._configs), "")

    def get(self, name: str) -> Optional[LLMConfig]:
        return self._configs.get(name)

    def names(self) -> list:
        return list(self._configs.keys())

    # ---- 选择/切换 ----

    @property
    def active(self) -> str:
        return self._active

    @property
    def active_config(self) -> Optional[LLMConfig]:
        return self._configs.get(self._active)

    def use(self, name: str) -> LLMConfig:
        """切换到指定模型，返回其配置。"""
        if name not in self._configs:
            raise KeyError(f"未配置的模型: {name}")
        self._active = name
        return self._configs[name]

    # ---- 工厂创建 ----

    def build(self, name: Optional[str] = None) -> Callable[[str], str]:
        """根据配置创建可调用的 LLM 处理器。"""
        config = self._configs.get(name or self._active)
        if config is None:
            raise ValueError("未选择任何模型")
        return build_llm(config)

    def build_active(self) -> Callable[[str], str]:
        return self.build(self._active)

    # ---- 持久化 ----

    def load(self, path: str) -> None:
        """从 JSON 配置文件加载模型配置。

        文件格式:
        {
            "active": "deepseek",
            "models": {
                "deepseek": {
                    "provider": "http",
                    "model": "deepseek-chat",
                    "base_url": "https://api.deepseek.com/v1",
                    "api_key_env": "DEEPSEEK_API_KEY"
                }
            }
        }
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for name, cfg in data.get("models", {}).items():
            cfg_dict = dict(cfg)
            cfg_dict["name"] = name
            self.add(LLMConfig.from_dict(cfg_dict))
        if data.get("active"):
            self.use(data["active"])

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典（api_key 会脱敏显示）。"""
        return {
            "active": self._active,
            "models": {
                name: {k: ("***" if k == "api_key" else v) for k, v in cfg.__dict__.items()}
                for name, cfg in self._configs.items()
            },
        }


def build_llm(config: LLMConfig) -> Callable[[str], str]:
    """根据配置创建 LLM 处理器。"""
    from .llm import HttpLLM

    provider = config.provider.lower()
    if provider in ("http", "openai"):
        return HttpLLM(
            base_url=config.base_url,
            api_key=config.resolve_api_key(),
            model=config.model,
            timeout=config.timeout,
            api_key_env=config.api_key_env or "LLM_API_KEY",
        )
    # 自定义处理器：从 extra 中读取 factory 回调
    if provider == "custom":
        factory = config.extra.get("factory")
        if not callable(factory):
            raise ValueError("custom provider 需要在 extra['factory'] 提供可调用对象")
        return factory(config)
    raise ValueError(f"未知的 provider: {config.provider}")
