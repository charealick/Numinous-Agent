"""CLI 交互入口。"""

from __future__ import annotations

import os
import sys
from typing import Optional

from ..capabilities import Agent, LLMProvider
from ..core import Engine
from ..external import ModelManager
from ..external.env import find_project_root, load_dotenv

# 项目根目录（基于 pyproject.toml 定位，与启动时 cwd 无关）
PROJECT_ROOT = find_project_root(__file__)
DEFAULT_MODELS_CONFIG = str(PROJECT_ROOT / "config" / "models.json")
DEFAULT_ENV_FILE = str(PROJECT_ROOT / ".env")


def build_model_manager(config_path: Optional[str] = None) -> ModelManager:
    """构建模型管理器：加载配置文件。"""
    manager = ModelManager()
    path = config_path or DEFAULT_MODELS_CONFIG
    if os.path.exists(path):
        manager.load(path)
    return manager


def build_engine(
    model_manager: Optional[ModelManager] = None,
    model: Optional[str] = None,
) -> Engine:
    """构建一个配置了基础工具/技能的引擎。"""
    engine = Engine()

    # 绑定大模型（通过 ModelManager 支持选择/切换）
    manager = model_manager or ModelManager()
    if model:
        manager.use(model)

    engine.agent = Agent(LLMProvider(model_manager=manager), tools=engine.tools, skills=engine.skills)

    # 注册示例工具
    @engine.tools.register("add", "计算两数之和")
    def add(a: int, b: int) -> int:
        return a + b

    # 注册示例技能
    @engine.skills.register("greet", "生成问候语")
    def greet(name: str) -> str:
        return f"你好，{name}！"

    return engine


def repl(engine: Engine) -> None:
    """交互式 REPL。"""
    print("Numinous-Agent REPL (输入 /help 查看帮助, /quit 退出)")
    print("当前模型:", engine.agent.llm.model_name, "| 可用模型:", engine.agent.llm.list_models())
    session = "default"
    user = "anonymous"
    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue
        if line in ("/quit", "/exit"):
            break
        if line == "/help":
            print(
                "命令: /quit 退出 | /session <id> 切换会话 | "
                "/model <name> 切换模型 | /models 列出模型 | "
                "/tools 工具 | /skills 技能 | 其他文本发送给 Agent"
            )
            continue
        if line.startswith("/session "):
            session = line.split(maxsplit=1)[1]
            print(f"已切换到会话: {session}")
            continue
        if line == "/models":
            print("可用模型:", ", ".join(engine.agent.llm.list_models()) or "(无)")
            print("当前模型:", engine.agent.llm.model_name)
            continue
        if line.startswith("/model "):
            name = line.split(maxsplit=1)[1]
            try:
                engine.agent.llm.switch_model(name)
                print(f"已切换到模型: {name}")
            except Exception as exc:  # noqa: BLE001
                print(f"[错误] {exc}")
            continue
        if line == "/tools":
            print("可用工具:", ", ".join(engine.tools.names()) or "(无)")
            continue
        if line == "/skills":
            print("可用技能:", ", ".join(engine.skills.names()) or "(无)")
            continue

        result = engine.handle(line, user=user, session=session)
        if result.ok:
            print(result.reply)
        else:
            print(f"[错误] {result.error}")


def main(argv: Optional[list] = None) -> int:
    """CLI 入口。

    参数:
        --config <path>   指定模型配置文件（JSON）
        --model <name>    指定使用的模型名称
        --env <path>      指定 .env 文件路径（默认项目根目录的 .env）
        --once [text]     单次对话模式
        --web             启动 Web 服务（提供 UI 界面）
        --host <host>     Web 服务监听地址（默认 127.0.0.1）
        --port <port>     Web 服务端口（默认 8000）
    """
    # 确保 Windows 控制台使用 UTF-8，避免 emoji 等字符打印报错
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except Exception:  # noqa: BLE001
                pass

    args = list(sys.argv[1:] if argv is None else argv)

    def _arg_value(flag: str) -> Optional[str]:
        if flag in args:
            idx = args.index(flag)
            if idx + 1 < len(args):
                return args[idx + 1]
        return None

    # 加载 .env 文件中的环境变量（如 DEEPSEEK_API_KEY）
    # 优先项目根目录的 .env，若用户显式指定 --env 则使用指定文件
    env_file = _arg_value("--env") or DEFAULT_ENV_FILE
    load_dotenv(env_file)

    config_path = _arg_value("--config")
    model = _arg_value("--model")

    manager = build_model_manager(config_path)
    engine = build_engine(manager, model=model)

    # Web 模式
    if "--web" in args:
        from .web import run_server

        host = _arg_value("--host") or "127.0.0.1"
        port_str = _arg_value("--port") or "8000"
        try:
            port = int(port_str)
        except ValueError:
            print(f"[错误] 无效端口: {port_str}")
            return 1
        run_server(engine, host=host, port=port)
        return 0

    if "--once" in args:
        # 单次模式：从参数或标准输入读取一条消息
        idx = args.index("--once")
        prompt = args[idx + 1] if idx + 1 < len(args) else sys.stdin.read().strip()
        result = engine.handle(prompt)
        print(result.reply if result.ok else f"[错误] {result.error}")
        return 0 if result.ok else 1

    repl(engine)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
