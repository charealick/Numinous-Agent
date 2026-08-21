"""大模型 API 适配：提供可用的 LLM 实现。"""

from __future__ import annotations

import os
from typing import Any, Dict


class HttpLLM:
    """基于 HTTP 的 LLM 客户端（OpenAI 兼容接口）。

    需要安装可选依赖：`pip install httpx`。
    api_key 可通过环境变量注入：优先使用显式传入的 api_key，
    否则读取 `LLM_API_KEY` 环境变量。
    """

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        model: str = "deepseek-chat",
        timeout: float = 30.0,
        api_key_env: str = "LLM_API_KEY",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.api_key = api_key or os.environ.get(api_key_env, "")
        self.model = model
        self.timeout = timeout

    def __call__(self, prompt: str) -> str:
        try:
            import httpx  # noqa: PLC0415 - 延迟导入可选依赖
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("HttpLLM 需要安装可选依赖: pip install httpx") from exc

        if not self.api_key:
            raise RuntimeError(
                f"未配置 API Key：请设置环境变量 {self.api_key_env} 或传入 api_key"
            )

        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data: Dict[str, Any] = resp.json()
        return data["choices"][0]["message"]["content"]
