# Numinous-Agent

一个模块化、可扩展的智能体（Agent）框架，通过清晰的层次划分与松耦合设计，将接口接入、核心执行、能力组件与外部资源整合为一个统一的智能体运行时。

## 架构概览

系统整体划分为四个层次：**接口层**、**核心层**、**能力层**与**外部依赖层**，各层职责单一、边界清晰，通过统一入口（执行引擎）进行编排与协作。

```
┌─────────────────────────────────────────────────────────────────┐
│                            接口层                               │
│              CLI            API            WebUI                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                            核心层                               │
│        Engine（执行引擎） ─┬─ Scheduler（调度器）                │
│                           └─ EventBus（事件总线）                │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────┘
       │          │          │          │          │
┌──────▼────┐┌────▼────┐┌────▼────┐┌────▼────┐┌────▼────┐┌────────┐
│  Ctx      ││ Perm    ││ Agent   ││ Tools   ││ MCP     ││ Skills │
│  上下文    ││ 权限    ││ Agent   ││ 工具    ││ MCP     ││ 技能   │
│  管理      ││ 控制    ││ 核心    ││ 调用    ││ 客户端  ││ 注册   │
└────┬──────┘└────┬────┘└────┬────┘└────┬────┘└────┬────┘└────┬───┘
     │            │          │          │          │          │
┌────▼────┐┌─────▼─────┐┌───▼────┐┌────▼────┐┌────▼─────┐┌───▼────┐
│   DB    ││    DB     ││  LLM   ││   Ext   ││  MCPSrv  ││   Ext  │
│  存储    ││   存储    ││ 大模型 ││ 外部工具││ MCP服务器││ 外部工具│
└─────────┘└───────────┘└────────┘└─────────┘└──────────┘└────────┘
```

## 分层设计

### 1. 接口层（Interface Layer）

面向用户的统一入口，负责接收交互请求并转发至核心引擎：

| 组件 | 说明 |
|------|------|
| **CLI** | 命令行交互入口，适用于脚本化与开发调试场景 |
| **API** | HTTP/RPC 服务接口，供外部系统集成调用 |
| **WebUI** | 可视化交互界面，提供图形化的对话与任务管理能力 |

### 2. 核心层（Core Layer）

智能体的运行时骨架，负责整体编排与协同：

| 组件 | 说明 |
|------|------|
| **Engine（执行引擎）** | 核心调度中枢，统一编排各能力组件，串联请求处理全流程 |
| **Scheduler（调度器）** | 负责任务的调度、优先级管理与并发控制 |
| **EventBus（事件总线）** | 基于发布/订阅模式的事件通信机制，解耦模块间依赖 |

### 3. 能力层（Capability Layer）

智能体的功能组件集合，均由执行引擎统一驱动：

| 组件 | 说明 |
|------|------|
| **Ctx（上下文管理）** | 管理会话上下文、历史记录与状态持久化 |
| **Perm（权限控制）** | 细粒度的权限校验与访问控制 |
| **Agent（Agent 核心）** | 智能体的核心推理与决策逻辑，负责与大模型交互 |
| **Tools（工具调用）** | 工具的定义、注册与调用管理 |
| **MCP（MCP 客户端）** | 基于 Model Context Protocol 与外部 MCP 服务器通信 |
| **Skills（技能注册）** | 技能（可复用能力单元）的注册与发现 |

### 4. 外部依赖层（External Layer）

与系统交互的外部资源：

| 组件 | 说明 |
|------|------|
| **LLM（大模型 API）** | 底层大语言模型服务 |
| **MCPSrv（MCP 服务器）** | 遵循 MCP 协议的外部服务端 |
| **Ext（外部工具）** | 第三方工具或服务 |
| **DB（存储）** | 持久化存储（会话、配置、状态等） |

## 模块依赖关系

```
CLI / API / WebUI  →  Engine
Engine              →  Scheduler、EventBus、Ctx、Perm、Agent、Tools、MCP、Skills
Ctx / Perm          →  DB
Tools               →  Ext
MCP                 →  MCPSrv
Agent               →  LLM
Skills              →  Ext
```

## 快速开始

### 1. 环境要求

- Python >= 3.9
- （可选）接入真实大模型需安装 `httpx`

### 2. 安装

```bash
cd Numinous-Agent

# 以开发模式安装（含 CLI 命令 numinous）
pip install -e .

# 如需接入真实大模型 API（DeepSeek 等）
pip install -e ".[llm]"
```

### 3. 配置大模型

API Key 通过环境变量注入，配置文件（`config/models.json`）中不存放密钥明文：

```json
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
```

- `active`：启动时默认使用的模型名称
- `base_url`：DeepSeek 的 OpenAI 兼容接口地址（`https://api.deepseek.com/v1`）
- `model`：`deepseek-chat`（对话）或 `deepseek-reasoner`（推理）
- `api_key_env`：API Key 所在的环境变量名（默认回退到 `LLM_API_KEY`）

**推荐方式：使用 `.env` 文件**

复制模板文件并填入真实 Key：

```bash
# Windows / Linux / macOS 通用
cp .env.example .env
```

编辑 `.env` 文件：

```dotenv
DEEPSEEK_API_KEY=sk-你的-api-key
```

程序启动时会自动加载项目根目录的 `.env` 文件，无需手动 `export`。

> `.env` 已加入 `.gitignore`，不会被提交到仓库，可安全存放密钥。

**备选方式：手动设置环境变量**

**Windows（PowerShell）**

```powershell
$env:DEEPSEEK_API_KEY="sk-你的-api-key"
```

**Linux / macOS**

```bash
export DEEPSEEK_API_KEY="sk-你的-api-key"
```

> 提示：也可以不写 `api_key_env`，直接设置通用的 `LLM_API_KEY` 环境变量。

### 4. 启动项目

**方式一：交互式 REPL（推荐）**

```bash
# 使用默认配置文件 config/models.json（当前默认 deepseek 模型）
numinous

# 或显式指定配置文件与模型
numinous --config config/models.json --model deepseek
```

启动后即可直接对话，REPL 内置命令：

| 命令 | 说明 |
|------|------|
| `/model <name>` | 切换当前使用的大模型 |
| `/models` | 列出所有可用模型及当前模型 |
| `/session <id>` | 切换会话 |
| `/tools` / `/skills` | 列出已注册的工具/技能 |
| `/help` | 查看帮助 |
| `/quit` | 退出 |

**方式二：单次对话**

```bash
numinous --config config/models.json --once "你好"
# 或使用模块方式
python -m numinous_agent.interfaces.cli --config config/models.json --once "你好"
```

**方式三：Web 服务（含 UI 界面）**

```bash
# 启动 Web 服务（默认 http://127.0.0.1:8000）
numinous --web

# 自定义地址与端口
numinous --web --host 0.0.0.0 --port 8080
```

启动后浏览器访问 `http://127.0.0.1:8000`，即可看到图形化对话界面。

**方式四：运行端到端示例**

```bash
python examples/demo.py
```

**方式五：以代码方式集成**

```python
from numinous_agent.core import Engine
from numinous_agent.capabilities import Agent, LLMProvider
from numinous_agent.external import ModelManager

manager = ModelManager()
manager.load("config/models.json")  # 加载 DeepSeek 配置

engine = Engine()
engine.agent = Agent(LLMProvider(model_manager=manager), tools=engine.tools, skills=engine.skills)

result = engine.handle("你好", user="alice", session="s1")
print(result.reply)
```

> 提示：若 `numinous` 命令不可用，请确认已执行 `pip install -e .`，或改用
> `python -m numinous_agent.interfaces.cli` 方式启动。

### 大模型选择与配置

通过 `ModelManager` 集中管理多个模型配置，支持按名称选择、运行时切换与 JSON 文件加载：

```python
from numinous_agent.external import LLMConfig, ModelManager
from numinous_agent.capabilities import Agent, LLMProvider

# 注册多个模型（api_key 通过环境变量读取）
manager = ModelManager()
manager.add(LLMConfig(
    name="deepseek",
    provider="http",
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key_env="DEEPSEEK_API_KEY",
))
manager.use("deepseek")  # 选择当前模型

agent = Agent(LLMProvider(model_manager=manager))
agent.llm.switch_model("deepseek")  # 运行时切换
```

从配置文件加载（`config/models.json`）：

```python
manager = ModelManager()
manager.load("config/models.json")
print(manager.active, manager.names())
```

支持的 `provider` 类型：`http`/`openai`（OpenAI 兼容接口）、`custom`（自定义 `factory` 回调）。

### 快速体验代码

```python
from numinous_agent.core import Engine
from numinous_agent.capabilities import Agent, LLMProvider
from numinous_agent.external import ModelManager

# 加载已配置好的 DeepSeek 模型
manager = ModelManager()
manager.load("config/models.json")

engine = Engine()
engine.agent = Agent(LLMProvider(model_manager=manager), tools=engine.tools, skills=engine.skills)

result = engine.handle("你好", user="alice", session="s1")
print(result.reply)
```

> 运行前请先设置 `DEEPSEEK_API_KEY` 环境变量（见上文「配置大模型」）。

## Web API 接口

启动 Web 服务后，可调用以下 RESTful 接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/chat` | 发送消息，返回 Agent 回复 |
| `GET` | `/api/models` | 列出可用模型与当前模型 |
| `POST` | `/api/models/switch` | 切换模型 |
| `GET` | `/api/history?session=xxx` | 获取会话历史 |
| `GET` | `/api/tools` | 列出已注册工具 |
| `GET` | `/api/skills` | 列出已注册技能 |
| `GET` | `/` | Web UI 界面 |

### 调用示例

```bash
# 发送消息
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "你好", "session": "s1"}'

# 响应
# {"ok": true, "reply": "你好！...", "error": "", "events": ["request.start", "request.complete"]}

# 列出模型
curl http://127.0.0.1:8000/api/models

# 切换模型
curl -X POST http://127.0.0.1:8000/api/models/switch \
  -H "Content-Type: application/json" \
  -d '{"name": "deepseek"}'
```

## 目录结构

```
Numinous-Agent/
├── src/numinous_agent/
│   ├── interfaces/        # 接口层
│   │   ├── cli.py         #   CLI 入口
│   │   ├── web.py         #   Web 服务（HTTP API）
│   │   └── static/        #   Web UI 静态资源
│   │       └── index.html
│   ├── core/              # 核心层
│   │   ├── engine.py      #   Engine（执行引擎）
│   │   ├── scheduler.py   #   Scheduler（调度器）
│   │   └── event_bus.py   #   EventBus（事件总线）
│   ├── capabilities/      # 能力层
│   │   ├── context.py     #   Ctx（上下文管理）
│   │   ├── permissions.py #   Perm（权限控制）
│   │   ├── agent.py       #   Agent（Agent 核心 + LLMProvider）
│   │   ├── tools.py       #   Tools（工具调用）
│   │   ├── mcp_client.py  #   MCP（MCP 客户端）
│   │   └── skills.py      #   Skills（技能注册）
│   └── external/          # 外部依赖适配层
│       ├── llm.py         #   LLM（HttpLLM，OpenAI 兼容接口）
│       ├── model_config.py #  大模型选择与配置（LLMConfig / ModelManager）
│       ├── env.py         #   环境变量加载（.env 文件读取）
│       └── storage.py     #   DB（InMemoryStore）
├── config/
│   └── models.json        # 示例模型配置文件（不含密钥）
├── .env.example           # 环境变量模板（复制为 .env 使用）
├── .gitignore             # 忽略 .env、__pycache__ 等
├── examples/
│   └── demo.py            # 端到端示例（含大模型选择步骤）
└── pyproject.toml
```

## 模块说明

| 模块 | 实现 | 说明 |
|------|------|------|
| `Engine` | `core/engine.py` | 编排入口，串联权限校验、上下文读写、Agent 推理，并发布事件 |
| `Scheduler` | `core/scheduler.py` | 基于优先队列的任务调度器，支持 `submit` / `run_all` |
| `EventBus` | `core/event_bus.py` | 发布/订阅事件总线，支持 `subscribe` / `emit` |
| `ContextManager` | `capabilities/context.py` | 会话历史与状态管理 |
| `PermissionManager` | `capabilities/permissions.py` | 角色-权限模型，支持 `require` 校验 |
| `Agent` | `capabilities/agent.py` | 推理核心，绑定 LLM 与工具/技能 |
| `ToolRegistry` | `capabilities/tools.py` | 工具注册与调用，支持装饰器注册 |
| `SkillRegistry` | `capabilities/skills.py` | 技能注册与发现 |
| `MCPClient` | `capabilities/mcp_client.py` | 管理 MCP 服务器连接与工具调用 |
| `HttpLLM` | `external/llm.py` | OpenAI 兼容 HTTP LLM，api_key 支持环境变量注入 |
| `LLMConfig` | `external/model_config.py` | 单个大模型配置（provider、model、base_url、api_key_env 等） |
| `ModelManager` | `external/model_config.py` | 模型选择器：注册、选择、切换、JSON 加载与工厂创建 |
| `load_dotenv` | `external/env.py` | 从 `.env` 文件加载环境变量（轻量实现，无第三方依赖） |
| `InMemoryStore` | `external/storage.py` | 内存键值存储，可导出 JSON |
| `WebApp` / `run_server` | `interfaces/web.py` | 零依赖 HTTP 服务，提供 RESTful API 与静态 UI |

## 当前能力与规划

已实现（MVP）：
- 四层架构骨架与模块边界
- 完整的 `Engine.handle` 处理流程（权限 → 上下文 → 推理 → 回写 → 事件）
- 大模型选择与配置模块（`ModelManager` + `LLMConfig`，支持多模型切换与 JSON 配置）
- CLI 交互入口与端到端示例（含大模型选择步骤）
- Web 服务（RESTful API）+ Web UI 图形化界面（零第三方依赖）

待扩展：
- 真实 MCP 协议传输层（stdio / SSE / HTTP）
- 持久化存储后端（SQLite / Redis）
- 工具/技能的自动调用编排（function calling）
- Web 会话管理与多用户隔离

## 贡献指南

欢迎提交 Issue 与 Pull Request。提交前请确保：

1. 代码风格保持一致
2. 新增功能附带必要的测试与文档
3. 遵循模块边界，避免跨层直接依赖

## License

待补充。
