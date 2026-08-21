"""端到端示例：演示如何组装并运行整个 MVP，含大模型选择与配置。"""

from numinous_agent.capabilities import Agent, LLMProvider, MCPServer
from numinous_agent.core import Engine
from numinous_agent.external import LLMConfig, ModelManager


def build_demo_engine() -> Engine:
    engine = Engine()

    # 1. 配置大模型：通过 ModelManager 加载配置文件（api_key 从环境变量读取）
    model_manager = ModelManager()
    model_manager.load("config/models.json")

    # 2. 通过 LLMProvider 绑定 ModelManager，支持运行时切换模型
    engine.agent = Agent(
        LLMProvider(model_manager=model_manager), tools=engine.tools, skills=engine.skills
    )

    # 3. 注册工具
    @engine.tools.register("add", "两数相加")
    def add(a: int, b: int) -> int:
        return a + b

    # 4. 注册技能
    @engine.skills.register("greet", "生成问候语")
    def greet(name: str) -> str:
        return f"你好，{name}！"

    # 5. 连接一个 MCP 服务器（演示处理器）
    def fake_mcp_handler(tool: str, **kwargs):
        return {"server": "demo", "tool": tool, "args": kwargs}

    engine.mcp.connect(MCPServer(name="demo", handler=fake_mcp_handler, tools=["search"]))

    # 6. 配置权限
    engine.permissions.add_role("admin", ["tool.use", "skill.use"])
    engine.permissions.assign_role("alice", "admin")

    # 7. 订阅事件
    engine.event_bus.subscribe("request.complete", lambda e: print(f"  [事件] 完成: {e.data}"))

    return engine


def main() -> None:
    engine = build_demo_engine()

    print("=== 0. 大模型选择与配置 ===")
    print("可用模型:", engine.agent.llm.list_models())
    print("当前模型:", engine.agent.llm.model_name)

    print("\n=== 1. 普通对话（deepseek 模型） ===")
    result = engine.handle("你好", user="alice", session="s1")
    print("回复:", result.reply)

    print("\n=== 2. 调用工具 ===")
    print("add(3, 4) =", engine.tools.call("add", a=3, b=4))

    print("\n=== 3. 调用技能 ===")
    print(engine.skills.invoke("greet", "世界"))

    print("\n=== 4. 调用 MCP 工具 ===")
    print(engine.mcp.call_tool("demo", "search", query="agent"))

    print("\n=== 5. 权限校验 ===")
    result = engine.handle("受限操作", user="bob", session="s1", required_permission="tool.use")
    print("ok =", result.ok, "| error =", result.error)

    print("\n=== 6. 上下文历史 ===")
    for m in engine.context.history("s1"):
        print(f"  {m.role}: {m.content}")

    print("\n=== 7. 调度器（异步） ===")
    task_id = engine.handle_async("异步任务", user="alice")
    print("已提交任务:", task_id, "| 待处理:", engine.scheduler.pending)
    print("执行任务数:", engine.flush())


if __name__ == "__main__":
    main()
