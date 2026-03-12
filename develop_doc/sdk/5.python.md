# Agent SDK 参考 - Python

Python Agent SDK 的完整 API 参考，包括所有函数、类型和类。

---

## 安装

```bash
pip install claude-agent-sdk
```

## 在 `query()` 和 `ClaudeSDKClient` 之间选择

Python SDK 提供了两种与 Claude Code 交互的方式：

### 快速对比

| 特性             | `query()`                     | `ClaudeSDKClient`                  |
| :------------------ | :---------------------------- | :--------------------------------- |
| **会话**         | 每次创建新会话 | 复用同一会话                |
| **对话**    | 单次交互               | 在同一上下文中进行多次交互 |
| **连接**      | 自动管理         | 手动控制                     |
| **流式输入** | ✅ 支持                  | ✅ 支持                       |
| **中断**      | ❌ 不支持              | ✅ 支持                       |
| **钩子**           | ❌ 不支持              | ✅ 支持                       |
| **自定义工具**    | ❌ 不支持              | ✅ 支持                       |
| **继续聊天**   | ❌ 每次新会话      | ✅ 保持对话          |
| **使用场景**        | 一次性任务                 | 持续对话           |

### 何时使用 `query()`（每次新会话）

**最适合：**

- 不需要对话历史的一次性问题
- 不需要先前交互上下文的独立任务
- 简单的自动化脚本
- 当你希望每次都从头开始时

### 何时使用 `ClaudeSDKClient`（持续对话）

**最适合：**

- **继续对话** - 当你需要 Claude 记住上下文时
- **后续问题** - 基于先前的回复进行扩展
- **交互式应用** - 聊天界面、REPL
- **响应驱动逻辑** - 当下一步操作取决于 Claude 的回复时
- **会话控制** - 显式管理对话生命周期

## 函数

### `query()`

为每次与 Claude Code 的交互创建一个新会话。返回一个异步迭代器，在消息到达时逐个产出。每次调用 `query()` 都会从头开始，不保留先前交互的记忆。

```python
async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: ClaudeAgentOptions | None = None
) -> AsyncIterator[Message]
```

#### 参数

| 参数 | 类型                         | 描述                                                                |
| :-------- | :--------------------------- | :------------------------------------------------------------------------- |
| `prompt`  | `str \| AsyncIterable[dict]` | 输入提示，可以是字符串或用于流式模式的异步可迭代对象          |
| `options` | `ClaudeAgentOptions \| None` | 可选的配置对象（如果为 None 则默认使用 `ClaudeAgentOptions()`） |

#### 返回值

返回一个 `AsyncIterator[Message]`，从对话中逐个产出消息。

#### 示例 - 使用选项

```python

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        system_prompt="You are an expert Python developer",
        permission_mode='acceptEdits',
        cwd="/home/user/project"
    )

    async for message in query(
        prompt="Create a Python web server",
        options=options
    ):
        print(message)


asyncio.run(main())
```

### `tool()`

用于定义具有类型安全的 MCP 工具的装饰器。

```python
def tool(
    name: str,
    description: str,
    input_schema: type | dict[str, Any]
) -> Callable[[Callable[[Any], Awaitable[dict[str, Any]]]], SdkMcpTool[Any]]
```

#### 参数

| 参数      | 类型                     | 描述                                             |
| :------------- | :----------------------- | :------------------------------------------------------ |
| `name`         | `str`                    | 工具的唯一标识符                          |
| `description`  | `str`                    | 工具功能的人类可读描述        |
| `input_schema` | `type \| dict[str, Any]` | 定义工具输入参数的模式（见下文） |

#### 输入模式选项

1. **简单类型映射**（推荐）：

   ```python
   {"text": str, "count": int, "enabled": bool}
   ```

2. **JSON Schema 格式**（用于复杂验证）：
   ```python
   {
       "type": "object",
       "properties": {
           "text": {"type": "string"},
           "count": {"type": "integer", "minimum": 0}
       },
       "required": ["text"]
   }
   ```

#### 返回值

一个装饰器函数，包装工具实现并返回一个 `SdkMcpTool` 实例。

#### 示例

```python
from claude_agent_sdk import tool
from typing import Any

@tool("greet", "Greet a user", {"name": str})
async def greet(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{
            "type": "text",
            "text": f"Hello, {args['name']}!"
        }]
    }
```

### `create_sdk_mcp_server()`

创建一个在 Python 应用程序内运行的进程内 MCP 服务器。

```python
def create_sdk_mcp_server(
    name: str,
    version: str = "1.0.0",
    tools: list[SdkMcpTool[Any]] | None = None
) -> McpSdkServerConfig
```

#### 参数

| 参数 | 类型                            | 默认值   | 描述                                           |
| :-------- | :------------------------------ | :-------- | :---------------------------------------------------- |
| `name`    | `str`                           | -         | 服务器的唯一标识符                      |
| `version` | `str`                           | `"1.0.0"` | 服务器版本字符串                                 |
| `tools`   | `list[SdkMcpTool[Any]] \| None` | `None`    | 使用 `@tool` 装饰器创建的工具函数列表 |

#### 返回值

返回一个 `McpSdkServerConfig` 对象，可以传递给 `ClaudeAgentOptions.mcp_servers`。

#### 示例

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    return {
        "content": [{
            "type": "text",
            "text": f"Sum: {args['a'] + args['b']}"
        }]
    }

@tool("multiply", "Multiply two numbers", {"a": float, "b": float})
async def multiply(args):
    return {
        "content": [{
            "type": "text",
            "text": f"Product: {args['a'] * args['b']}"
        }]
    }

calculator = create_sdk_mcp_server(
    name="calculator",
    version="2.0.0",
    tools=[add, multiply]  # Pass decorated functions
)

# Use with Claude
options = ClaudeAgentOptions(
    mcp_servers={"calc": calculator},
    allowed_tools=["mcp__calc__add", "mcp__calc__multiply"]
)
```

## 类

### `ClaudeSDKClient`

**在多次交互中维护对话会话。** 这是 TypeScript SDK 的 `query()` 函数内部工作方式的 Python 等价物——它创建一个可以继续对话的客户端对象。

#### 主要特性

- **会话连续性**：在多次 `query()` 调用之间维护对话上下文
- **同一对话**：Claude 记住会话中之前的消息
- **中断支持**：可以在执行过程中停止 Claude
- **显式生命周期**：你控制会话的开始和结束时间
- **响应驱动流程**：可以对响应做出反应并发送后续消息
- **自定义工具和钩子**：支持自定义工具（使用 `@tool` 装饰器创建）和钩子

```python
class ClaudeSDKClient:
    def __init__(self, options: ClaudeAgentOptions | None = None)
    async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None
    async def query(self, prompt: str | AsyncIterable[dict], session_id: str = "default") -> None
    async def receive_messages(self) -> AsyncIterator[Message]
    async def receive_response(self) -> AsyncIterator[Message]
    async def interrupt(self) -> None
    async def rewind_files(self, user_message_uuid: str) -> None
    async def disconnect(self) -> None
```

#### 方法

| 方法                      | 描述                                                         |
| :-------------------------- | :------------------------------------------------------------------ |
| `__init__(options)`         | 使用可选配置初始化客户端                   |
| `connect(prompt)`           | 使用可选的初始提示或消息流连接到 Claude |
| `query(prompt, session_id)` | 在流式模式下发送新请求                                |
| `receive_messages()`        | 以异步迭代器形式接收来自 Claude 的所有消息               |
| `receive_response()`        | 接收消息直到并包括 ResultMessage                |
| `interrupt()`               | 发送中断信号（仅在流式模式下有效）                |
| `rewind_files(user_message_uuid)` | 将文件恢复到指定用户消息时的状态。需要 `enable_file_checkpointing=True`。参见[文件检查点](/docs/zh-CN/agent-sdk/file-checkpointing) |
| `disconnect()`              | 断开与 Claude 的连接                                              |

#### 上下文管理器支持

客户端可以用作异步上下文管理器，实现自动连接管理：

```python
async with ClaudeSDKClient() as client:
    await client.query("Hello Claude")
    async for message in client.receive_response():
        print(message)
```

> **重要提示：** 在迭代消息时，避免使用 `break` 提前退出，因为这可能导致 asyncio 清理问题。相反，让迭代自然完成，或使用标志来跟踪何时找到所需内容。

#### 示例 - 继续对话

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

async def main():
    async with ClaudeSDKClient() as client:
        # First question
        await client.query("What's the capital of France?")

        # Process response
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # Follow-up question - Claude remembers the previous context
        await client.query("What's the population of that city?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # Another follow-up - still in the same conversation
        await client.query("What are some famous landmarks there?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

asyncio.run(main())
```

#### 示例 - 使用 ClaudeSDKClient 进行流式输入

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient

async def message_stream():
    """Generate messages dynamically."""
    yield {"type": "text", "text": "Analyze the following data:"}
    await asyncio.sleep(0.5)
    yield {"type": "text", "text": "Temperature: 25°C"}
    await asyncio.sleep(0.5)
    yield {"type": "text", "text": "Humidity: 60%"}
    await asyncio.sleep(0.5)
    yield {"type": "text", "text": "What patterns do you see?"}

async def main():
    async with ClaudeSDKClient() as client:
        # Stream input to Claude
        await client.query(message_stream())

        # Process response
        async for message in client.receive_response():
            print(message)

        # Follow-up in same session
        await client.query("Should we be concerned about these readings?")

        async for message in client.receive_response():
            print(message)

asyncio.run(main())
```

#### 示例 - 使用中断

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def interruptible_task():
    options = ClaudeAgentOptions(
        allowed_tools=["Bash"],
        permission_mode="acceptEdits"
    )

    async with ClaudeSDKClient(options=options) as client:
        # Start a long-running task
        await client.query("Count from 1 to 100 slowly")

        # Let it run for a bit
        await asyncio.sleep(2)

        # Interrupt the task
        await client.interrupt()
        print("Task interrupted!")

        # Send a new command
        await client.query("Just say hello instead")

        async for message in client.receive_response():
            # Process the new response
            pass

asyncio.run(interruptible_task())
```

#### 示例 - 高级权限控制

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions
)
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

async def custom_permission_handler(
    tool_name: str,
    input_data: dict,
    context: dict
) -> PermissionResultAllow | PermissionResultDeny:
    """Custom logic for tool permissions."""

    # Block writes to system directories
    if tool_name == "Write" and input_data.get("file_path", "").startswith("/system/"):
        return PermissionResultDeny(
            message="System directory write not allowed",
            interrupt=True
        )

    # Redirect sensitive file operations
    if tool_name in ["Write", "Edit"] and "config" in input_data.get("file_path", ""):
        safe_path = f"./sandbox/{input_data['file_path']}"
        return PermissionResultAllow(
            updated_input={**input_data, "file_path": safe_path}
        )

    # Allow everything else
    return PermissionResultAllow(updated_input=input_data)

async def main():
    options = ClaudeAgentOptions(
        can_use_tool=custom_permission_handler,
        allowed_tools=["Read", "Write", "Edit"]
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Update the system config file")

        async for message in client.receive_response():
            # Will use sandbox path instead
            print(message)

asyncio.run(main())
```

## 类型

### `SdkMcpTool`

使用 `@tool` 装饰器创建的 SDK MCP 工具的定义。

```python
@dataclass
class SdkMcpTool(Generic[T]):
    name: str
    description: str
    input_schema: type[T] | dict[str, Any]
    handler: Callable[[T], Awaitable[dict[str, Any]]]
```

| 属性       | 类型                                       | 描述                                |
| :------------- | :----------------------------------------- | :----------------------------------------- |
| `name`         | `str`                                      | 工具的唯一标识符             |
| `description`  | `str`                                      | 人类可读的描述                 |
| `input_schema` | `type[T] \| dict[str, Any]`                | 用于输入验证的模式                |
| `handler`      | `Callable[[T], Awaitable[dict[str, Any]]]` | 处理工具执行的异步函数 |

### `ClaudeAgentOptions`

Claude Code 查询的配置数据类。

```python
@dataclass
class ClaudeAgentOptions:
    tools: list[str] | ToolsPreset | None = None
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    max_budget_usd: float | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    fallback_model: str | None = None
    betas: list[SdkBeta] = field(default_factory=list)
    output_format: OutputFormat | None = None
    permission_prompt_tool_name: str | None = None
    cwd: str | Path | None = None
    cli_path: str | Path | None = None
    settings: str | None = None
    add_dirs: list[str | Path] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    extra_args: dict[str, str | None] = field(default_factory=dict)
    max_buffer_size: int | None = None
    debug_stderr: Any = sys.stderr  # Deprecated
    stderr: Callable[[str], None] | None = None
    can_use_tool: CanUseTool | None = None
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    user: str | None = None
    include_partial_messages: bool = False
    fork_session: bool = False
    agents: dict[str, AgentDefinition] | None = None
    setting_sources: list[SettingSource] | None = None
    max_thinking_tokens: int | None = None
```

| 属性                      | 类型                                         | 默认值              | 描述                                                                                                                                                                             |
| :---------------------------- | :------------------------------------------- | :------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tools`                       | `list[str] \| ToolsPreset \| None`           | `None`               | 工具配置。使用 `{"type": "preset", "preset": "claude_code"}` 获取 Claude Code 的默认工具                                                                                  |
| `allowed_tools`               | `list[str]`                                  | `[]`                 | 允许的工具名称列表                                                                                                                                                              |
| `system_prompt`               | `str \| SystemPromptPreset \| None`          | `None`               | 系统提示配置。传递字符串作为自定义提示，或使用 `{"type": "preset", "preset": "claude_code"}` 获取 Claude Code 的系统提示。添加 `"append"` 以扩展预设 |
| `mcp_servers`                 | `dict[str, McpServerConfig] \| str \| Path`  | `{}`                 | MCP 服务器配置或配置文件路径                                                                                                                                        |
| `permission_mode`             | `PermissionMode \| None`                     | `None`               | 工具使用的权限模式                                                                                                                                                          |
| `continue_conversation`       | `bool`                                       | `False`              | 继续最近的对话                                                                                                                                                   |
| `resume`                      | `str \| None`                                | `None`               | 要恢复的会话 ID                                                                                                                                                    |
| `max_turns`                   | `int \| None`                                | `None`               | 最大对话轮次                                                                                                                                                              |
| `max_budget_usd`              | `float \| None`                              | `None`               | 会话的最大预算（美元）                                                                                                                                                   |
| `disallowed_tools`            | `list[str]`                                  | `[]`                 | 不允许的工具名称列表                                                                                                                                                           |
| `enable_file_checkpointing`   | `bool`                                       | `False`              | 启用文件更改跟踪以支持回退。参见[文件检查点](/docs/zh-CN/agent-sdk/file-checkpointing)                                                                              |
| `model`                       | `str \| None`                                | `None`               | 要使用的 Claude 模型                                                                                                                                                     |
| `fallback_model`              | `str \| None`                                | `None`               | 主模型失败时使用的备用模型                                                                                                                        |
| `betas`                       | `list[SdkBeta]`                              | `[]`                 | 要启用的 Beta 功能。参见 [`SdkBeta`](#sdkbeta) 了解可用选项                                                                                                                |
| `output_format`               | [`OutputFormat`](#outputformat) ` \| None`   | `None`               | 定义代理结果的输出格式。参见[结构化输出](/docs/zh-CN/agent-sdk/structured-outputs)了解详情                                                                    |
| `permission_prompt_tool_name` | `str \| None`                                | `None`               | 用于权限提示的 MCP 工具名称                                                                                                                                                    |
| `cwd`                         | `str \| Path \| None`                        | `None`               | 当前工作目录                                                                                                                                               |
| `cli_path`                    | `str \| Path \| None`                        | `None`               | Claude Code CLI 可执行文件的自定义路径                                                                                                                           |
| `settings`                    | `str \| None`                                | `None`               | 设置文件路径                                                                                                                                                   |
| `add_dirs`                    | `list[str \| Path]`                          | `[]`                 | Claude 可以访问的额外目录                                                                                                                                |
| `env`                         | `dict[str, str]`                             | `{}`                 | 环境变量                                                                                                                                                   |
| `extra_args`                  | `dict[str, str \| None]`                     | `{}`                 | 直接传递给 CLI 的额外命令行参数                                                                                                                    |
| `max_buffer_size`             | `int \| None`                                | `None`               | 缓冲 CLI stdout 时的最大字节数                                                                                                                                 |
| `debug_stderr`                | `Any`                                        | `sys.stderr`         | _已弃用_ - 用于调试输出的类文件对象。请改用 `stderr` 回调                                                                                                         |
| `stderr`                      | `Callable[[str], None] \| None`              | `None`               | 用于 CLI stderr 输出的回调函数                                                                                                                            |
| `can_use_tool`                | [`CanUseTool`](#canusertool) ` \| None`      | `None`               | 工具权限回调函数。参见[权限类型](#canusertool)了解详情                                                                                                     |
| `hooks`                       | `dict[HookEvent, list[HookMatcher]] \| None` | `None`               | 用于拦截事件的钩子配置                                                                                                                             |
| `user`                        | `str \| None`                                | `None`               | 用户标识符                                                                                                                                                         |
| `include_partial_messages`    | `bool`                                       | `False`              | 包含部分消息流事件。启用后，会产出 [`StreamEvent`](#streamevent) 消息                                                                              |
| `fork_session`                | `bool`                                       | `False`              | 使用 `resume` 恢复时，分叉到新的会话 ID 而不是继续原始会话                                                                                        |
| `agents`                      | `dict[str, AgentDefinition] \| None`         | `None`               | 以编程方式定义的子代理                                                                                                                                                      |
| `plugins`                     | `list[SdkPluginConfig]`                      | `[]`                 | 从本地路径加载自定义插件。参见[插件](/docs/zh-CN/agent-sdk/plugins)了解详情                                                                                             |
| `sandbox`                     | [`SandboxSettings`](#sandboxsettings) ` \| None` | `None`              | 以编程方式配置沙箱行为。参见[沙箱设置](#sandboxsettings)了解详情                                        |
| `setting_sources`             | `list[SettingSource] \| None`                | `None`（不加载设置） | 控制要加载哪些文件系统设置。省略时不加载任何设置。**注意：** 必须包含 `"project"` 才能加载 CLAUDE.md 文件                                             |
| `max_thinking_tokens`         | `int \| None`                                | `None`               | 思考块的最大令牌数                                                                                                                                                      |

### `OutputFormat`

结构化输出验证的配置。

```python
class OutputFormat(TypedDict):
    type: Literal["json_schema"]
    schema: dict[str, Any]
```

| 字段    | 必需 | 描述                                    |
| :------- | :------- | :--------------------------------------------- |
| `type`   | 是      | 必须为 `"json_schema"` 以进行 JSON Schema 验证 |
| `schema` | 是      | 用于输出验证的 JSON Schema 定义   |

### `SystemPromptPreset`

使用 Claude Code 预设系统提示并可选添加内容的配置。

```python
class SystemPromptPreset(TypedDict):
    type: Literal["preset"]
    preset: Literal["claude_code"]
    append: NotRequired[str]
```

| 字段    | 必需 | 描述                                                   |
| :------- | :------- | :------------------------------------------------------------ |
| `type`   | 是      | 必须为 `"preset"` 以使用预设系统提示              |
| `preset` | 是      | 必须为 `"claude_code"` 以使用 Claude Code 的系统提示    |
| `append` | 否       | 附加到预设系统提示的额外指令 |

### `SettingSource`

控制 SDK 从哪些基于文件系统的配置源加载设置。

```python
SettingSource = Literal["user", "project", "local"]
```

| 值       | 描述                                  | 位置                      |
| :---------- | :------------------------------------------- | :---------------------------- |
| `"user"`    | 全局用户设置                         | `~/.claude/settings.json`     |
| `"project"` | 共享项目设置（版本控制） | `.claude/settings.json`       |
| `"local"`   | 本地项目设置（gitignore 忽略）          | `.claude/settings.local.json` |

#### 默认行为

当 `setting_sources` 被**省略**或为 **`None`** 时，SDK **不会**加载任何文件系统设置。这为 SDK 应用程序提供了隔离性。

#### 为什么使用 setting_sources？

**加载所有文件系统设置（旧版行为）：**

```python
# Load all settings like SDK v0.0.x did
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt="Analyze this code",
    options=ClaudeAgentOptions(
        setting_sources=["user", "project", "local"]  # Load all settings
    )
):
    print(message)
```

**仅加载特定设置源：**

```python
# Load only project settings, ignore user and local
async for message in query(
    prompt="Run CI checks",
    options=ClaudeAgentOptions(
        setting_sources=["project"]  # Only .claude/settings.json
    )
):
    print(message)
```

**测试和 CI 环境：**

```python
# Ensure consistent behavior in CI by excluding local settings
async for message in query(
    prompt="Run tests",
    options=ClaudeAgentOptions(
        setting_sources=["project"],  # Only team-shared settings
        permission_mode="bypassPermissions"
    )
):
    print(message)
```

**纯 SDK 应用程序：**

```python
# Define everything programmatically (default behavior)
# No filesystem dependencies - setting_sources defaults to None
async for message in query(
    prompt="Review this PR",
    options=ClaudeAgentOptions(
        # setting_sources=None is the default, no need to specify
        agents={ /* ... */ },
        mcp_servers={ /* ... */ },
        allowed_tools=["Read", "Grep", "Glob"]
    )
):
    print(message)
```

**加载 CLAUDE.md 项目指令：**

```python
# Load project settings to include CLAUDE.md files
async for message in query(
    prompt="Add a new feature following project conventions",
    options=ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code"  # Use Claude Code's system prompt
        },
        setting_sources=["project"],  # Required to load CLAUDE.md from project
        allowed_tools=["Read", "Write", "Edit"]
    )
):
    print(message)
```

#### 设置优先级

当加载多个源时，设置按以下优先级合并（从高到低）：

1. 本地设置（`.claude/settings.local.json`）
2. 项目设置（`.claude/settings.json`）
3. 用户设置（`~/.claude/settings.json`）

编程选项（如 `agents`、`allowed_tools`）始终覆盖文件系统设置。

### `AgentDefinition`

以编程方式定义的子代理配置。

```python
@dataclass
class AgentDefinition:
    description: str
    prompt: str
    tools: list[str] | None = None
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
```

| 字段         | 必需 | 描述                                                    |
| :------------ | :------- | :------------------------------------------------------------- |
| `description` | 是      | 描述何时使用此代理的自然语言描述         |
| `tools`       | 否       | 允许的工具名称数组。如果省略，则继承所有工具    |
| `prompt`      | 是      | 代理的系统提示                                      |
| `model`       | 否       | 此代理的模型覆盖。如果省略，则使用主模型 |

### `PermissionMode`

控制工具执行的权限模式。

```python
PermissionMode = Literal[
    "default",           # 标准权限行为
    "acceptEdits",       # 自动接受文件编辑
    "plan",              # 规划模式 - 不执行
    "bypassPermissions"  # 绕过所有权限检查（谨慎使用）
]
```

### `CanUseTool`

工具权限回调函数的类型别名。

```python
CanUseTool = Callable[
    [str, dict[str, Any], ToolPermissionContext],
    Awaitable[PermissionResult]
]
```

回调接收以下参数：
- `tool_name`：被调用的工具名称
- `input_data`：工具的输入参数
- `context`：包含附加信息的 `ToolPermissionContext`

返回 `PermissionResult`（`PermissionResultAllow` 或 `PermissionResultDeny`）。

### `ToolPermissionContext`

传递给工具权限回调的上下文信息。

```python
@dataclass
class ToolPermissionContext:
    signal: Any | None = None  # Future: abort signal support
    suggestions: list[PermissionUpdate] = field(default_factory=list)
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `signal` | `Any \| None` | 保留用于未来的中止信号支持 |
| `suggestions` | `list[PermissionUpdate]` | 来自 CLI 的权限更新建议 |

### `PermissionResult`

权限回调结果的联合类型。

```python
PermissionResult = PermissionResultAllow | PermissionResultDeny
```

### `PermissionResultAllow`

表示应允许工具调用的结果。

```python
@dataclass
class PermissionResultAllow:
    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] | None = None
    updated_permissions: list[PermissionUpdate] | None = None
```

| 字段 | 类型 | 默认值 | 描述 |
|:------|:-----|:--------|:------------|
| `behavior` | `Literal["allow"]` | `"allow"` | 必须为 "allow" |
| `updated_input` | `dict[str, Any] \| None` | `None` | 用于替代原始输入的修改后输入 |
| `updated_permissions` | `list[PermissionUpdate] \| None` | `None` | 要应用的权限更新 |

### `PermissionResultDeny`

表示应拒绝工具调用的结果。

```python
@dataclass
class PermissionResultDeny:
    behavior: Literal["deny"] = "deny"
    message: str = ""
    interrupt: bool = False
```

| 字段 | 类型 | 默认值 | 描述 |
|:------|:-----|:--------|:------------|
| `behavior` | `Literal["deny"]` | `"deny"` | 必须为 "deny" |
| `message` | `str` | `""` | 解释工具被拒绝原因的消息 |
| `interrupt` | `bool` | `False` | 是否中断当前执行 |

### `PermissionUpdate`

用于以编程方式更新权限的配置。

```python
@dataclass
class PermissionUpdate:
    type: Literal[
        "addRules",
        "replaceRules",
        "removeRules",
        "setMode",
        "addDirectories",
        "removeDirectories",
    ]
    rules: list[PermissionRuleValue] | None = None
    behavior: Literal["allow", "deny", "ask"] | None = None
    mode: PermissionMode | None = None
    directories: list[str] | None = None
    destination: Literal["userSettings", "projectSettings", "localSettings", "session"] | None = None
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `type` | `Literal[...]` | 权限更新操作的类型 |
| `rules` | `list[PermissionRuleValue] \| None` | 用于添加/替换/删除操作的规则 |
| `behavior` | `Literal["allow", "deny", "ask"] \| None` | 基于规则操作的行为 |
| `mode` | `PermissionMode \| None` | 用于 setMode 操作的模式 |
| `directories` | `list[str] \| None` | 用于添加/删除目录操作的目录 |
| `destination` | `Literal[...] \| None` | 权限更新应用的位置 |

### `SdkBeta`

SDK beta 功能的字面量类型。

```python
SdkBeta = Literal["context-1m-2025-08-07"]
```

与 `ClaudeAgentOptions` 中的 `betas` 字段一起使用以启用 beta 功能。

### `McpSdkServerConfig`

使用 `create_sdk_mcp_server()` 创建的 SDK MCP 服务器的配置。

```python
class McpSdkServerConfig(TypedDict):
    type: Literal["sdk"]
    name: str
    instance: Any  # MCP Server instance
```

### `McpServerConfig`

MCP 服务器配置的联合类型。

```python
McpServerConfig = McpStdioServerConfig | McpSSEServerConfig | McpHttpServerConfig | McpSdkServerConfig
```

#### `McpStdioServerConfig`

```python
class McpStdioServerConfig(TypedDict):
    type: NotRequired[Literal["stdio"]]  # Optional for backwards compatibility
    command: str
    args: NotRequired[list[str]]
    env: NotRequired[dict[str, str]]
```

#### `McpSSEServerConfig`

```python
class McpSSEServerConfig(TypedDict):
    type: Literal["sse"]
    url: str
    headers: NotRequired[dict[str, str]]
```

#### `McpHttpServerConfig`

```python
class McpHttpServerConfig(TypedDict):
    type: Literal["http"]
    url: str
    headers: NotRequired[dict[str, str]]
```

### `SdkPluginConfig`

在 SDK 中加载插件的配置。

```python
class SdkPluginConfig(TypedDict):
    type: Literal["local"]
    path: str
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `type` | `Literal["local"]` | 必须为 `"local"`（目前仅支持本地插件） |
| `path` | `str` | 插件目录的绝对路径或相对路径 |

**示例：**
```python
plugins=[
    {"type": "local", "path": "./my-plugin"},
    {"type": "local", "path": "/absolute/path/to/plugin"}
]
```

有关创建和使用插件的完整信息，请参阅[插件](/docs/zh-CN/agent-sdk/plugins)。

## 消息类型

### `Message`

所有可能消息的联合类型。

```python
Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage | StreamEvent
```

### `UserMessage`

用户输入消息。

```python
@dataclass
class UserMessage:
    content: str | list[ContentBlock]
```

### `AssistantMessage`

包含内容块的助手响应消息。

```python
@dataclass
class AssistantMessage:
    content: list[ContentBlock]
    model: str
```

### `SystemMessage`

包含元数据的系统消息。

```python
@dataclass
class SystemMessage:
    subtype: str
    data: dict[str, Any]
```

### `ResultMessage`

包含成本和使用信息的最终结果消息。

```python
@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
    structured_output: Any = None
```

### `StreamEvent`

流式传输期间部分消息更新的流事件。仅在 `ClaudeAgentOptions` 中设置 `include_partial_messages=True` 时接收。

```python
@dataclass
class StreamEvent:
    uuid: str
    session_id: str
    event: dict[str, Any]  # The raw Anthropic API stream event
    parent_tool_use_id: str | None = None
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `uuid` | `str` | 此事件的唯一标识符 |
| `session_id` | `str` | 会话标识符 |
| `event` | `dict[str, Any]` | 原始 Anthropic API 流事件数据 |
| `parent_tool_use_id` | `str \| None` | 如果此事件来自子代理，则为父工具使用 ID |

## 内容块类型

### `ContentBlock`

所有内容块的联合类型。

```python
ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock
```

### `TextBlock`

文本内容块。

```python
@dataclass
class TextBlock:
    text: str
```

### `ThinkingBlock`

思考内容块（用于具有思考能力的模型）。

```python
@dataclass
class ThinkingBlock:
    thinking: str
    signature: str
```

### `ToolUseBlock`

工具使用请求块。

```python
@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
```

### `ToolResultBlock`

工具执行结果块。

```python
@dataclass
class ToolResultBlock:
    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None
```

## 错误类型

### `ClaudeSDKError`

所有 SDK 错误的基础异常类。

```python
class ClaudeSDKError(Exception):
    """Base error for Claude SDK."""
```

### `CLINotFoundError`

当 Claude Code CLI 未安装或未找到时引发。

```python
class CLINotFoundError(CLIConnectionError):
    def __init__(self, message: str = "Claude Code not found", cli_path: str | None = None):
        """
        Args:
            message: Error message (default: "Claude Code not found")
            cli_path: Optional path to the CLI that was not found
        """
```

### `CLIConnectionError`

当连接 Claude Code 失败时引发。

```python
class CLIConnectionError(ClaudeSDKError):
    """Failed to connect to Claude Code."""
```

### `ProcessError`

当 Claude Code 进程失败时引发。

```python
class ProcessError(ClaudeSDKError):
    def __init__(self, message: str, exit_code: int | None = None, stderr: str | None = None):
        self.exit_code = exit_code
        self.stderr = stderr
```

### `CLIJSONDecodeError`

当 JSON 解析失败时引发。

```python
class CLIJSONDecodeError(ClaudeSDKError):
    def __init__(self, line: str, original_error: Exception):
        """
        Args:
            line: The line that failed to parse
            original_error: The original JSON decode exception
        """
        self.line = line
        self.original_error = original_error
```

## Hook 类型

有关使用 Hook 的综合指南，包括示例和常见模式，请参阅 [Hook 指南](/docs/zh-CN/agent-sdk/hooks)。

### `HookEvent`

支持的 Hook 事件类型。请注意，由于设置限制，Python SDK 不支持 SessionStart、SessionEnd 和 Notification Hook。

```python
HookEvent = Literal[
    "PreToolUse",      # Called before tool execution
    "PostToolUse",     # Called after tool execution
    "UserPromptSubmit", # Called when user submits a prompt
    "Stop",            # Called when stopping execution
    "SubagentStop",    # Called when a subagent stops
    "PreCompact"       # Called before message compaction
]
```

### `HookCallback`

Hook 回调函数的类型定义。

```python
HookCallback = Callable[
    [dict[str, Any], str | None, HookContext],
    Awaitable[dict[str, Any]]
]
```

参数：

- `input_data`：Hook 特定的输入数据（参见 [Hook 指南](/docs/zh-CN/agent-sdk/hooks#input-data)）
- `tool_use_id`：可选的工具使用标识符（用于工具相关的 Hook）
- `context`：包含附加信息的 Hook 上下文

返回一个可能包含以下内容的字典：

- `decision`：`"block"` 以阻止操作
- `systemMessage`：添加到对话记录的系统消息
- `hookSpecificOutput`：Hook 特定的输出数据

### `HookContext`

传递给 Hook 回调的上下文信息。

```python
@dataclass
class HookContext:
    signal: Any | None = None  # Future: abort signal support
```

### `HookMatcher`

用于将 Hook 匹配到特定事件或工具的配置。

```python
@dataclass
class HookMatcher:
    matcher: str | None = None        # Tool name or pattern to match (e.g., "Bash", "Write|Edit")
    hooks: list[HookCallback] = field(default_factory=list)  # List of callbacks to execute
    timeout: float | None = None        # Timeout in seconds for all hooks in this matcher (default: 60)
```

### `HookInput`

所有 Hook 输入类型的联合类型。实际类型取决于 `hook_event_name` 字段。

```python
HookInput = (
    PreToolUseHookInput
    | PostToolUseHookInput
    | UserPromptSubmitHookInput
    | StopHookInput
    | SubagentStopHookInput
    | PreCompactHookInput
)
```

### `BaseHookInput`

所有 Hook 输入类型中存在的基础字段。

```python
class BaseHookInput(TypedDict):
    session_id: str
    transcript_path: str
    cwd: str
    permission_mode: NotRequired[str]
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `session_id` | `str` | 当前会话标识符 |
| `transcript_path` | `str` | 会话对话记录文件的路径 |
| `cwd` | `str` | 当前工作目录 |
| `permission_mode` | `str`（可选） | 当前权限模式 |

### `PreToolUseHookInput`

`PreToolUse` Hook 事件的输入数据。

```python
class PreToolUseHookInput(BaseHookInput):
    hook_event_name: Literal["PreToolUse"]
    tool_name: str
    tool_input: dict[str, Any]
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `hook_event_name` | `Literal["PreToolUse"]` | 始终为 "PreToolUse" |
| `tool_name` | `str` | 即将执行的工具名称 |
| `tool_input` | `dict[str, Any]` | 工具的输入参数 |

### `PostToolUseHookInput`

`PostToolUse` Hook 事件的输入数据。

```python
class PostToolUseHookInput(BaseHookInput):
    hook_event_name: Literal["PostToolUse"]
    tool_name: str
    tool_input: dict[str, Any]
    tool_response: Any
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `hook_event_name` | `Literal["PostToolUse"]` | 始终为 "PostToolUse" |
| `tool_name` | `str` | 已执行的工具名称 |
| `tool_input` | `dict[str, Any]` | 使用的输入参数 |
| `tool_response` | `Any` | 工具执行的响应 |

### `UserPromptSubmitHookInput`

`UserPromptSubmit` Hook 事件的输入数据。

```python
class UserPromptSubmitHookInput(BaseHookInput):
    hook_event_name: Literal["UserPromptSubmit"]
    prompt: str
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `hook_event_name` | `Literal["UserPromptSubmit"]` | 始终为 "UserPromptSubmit" |
| `prompt` | `str` | 用户提交的提示词 |

### `StopHookInput`

`Stop` Hook 事件的输入数据。

```python
class StopHookInput(BaseHookInput):
    hook_event_name: Literal["Stop"]
    stop_hook_active: bool
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `hook_event_name` | `Literal["Stop"]` | 始终为 "Stop" |
| `stop_hook_active` | `bool` | 停止 Hook 是否处于活动状态 |

### `SubagentStopHookInput`

`SubagentStop` Hook 事件的输入数据。

```python
class SubagentStopHookInput(BaseHookInput):
    hook_event_name: Literal["SubagentStop"]
    stop_hook_active: bool
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `hook_event_name` | `Literal["SubagentStop"]` | 始终为 "SubagentStop" |
| `stop_hook_active` | `bool` | 停止 Hook 是否处于活动状态 |

### `PreCompactHookInput`

`PreCompact` Hook 事件的输入数据。

```python
class PreCompactHookInput(BaseHookInput):
    hook_event_name: Literal["PreCompact"]
    trigger: Literal["manual", "auto"]
    custom_instructions: str | None
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `hook_event_name` | `Literal["PreCompact"]` | 始终为 "PreCompact" |
| `trigger` | `Literal["manual", "auto"]` | 触发压缩的原因 |
| `custom_instructions` | `str \| None` | 压缩的自定义指令 |

### `HookJSONOutput`

Hook 回调返回值的联合类型。

```python
HookJSONOutput = AsyncHookJSONOutput | SyncHookJSONOutput
```

#### `SyncHookJSONOutput`

包含控制和决策字段的同步 Hook 输出。

```python
class SyncHookJSONOutput(TypedDict):
    # Control fields
    continue_: NotRequired[bool]      # Whether to proceed (default: True)
    suppressOutput: NotRequired[bool] # Hide stdout from transcript
    stopReason: NotRequired[str]      # Message when continue is False

    # Decision fields
    decision: NotRequired[Literal["block"]]
    systemMessage: NotRequired[str]   # Warning message for user
    reason: NotRequired[str]          # Feedback for Claude

    # Hook-specific output
    hookSpecificOutput: NotRequired[dict[str, Any]]
```

<Note>
在 Python 代码中使用 `continue_`（带下划线）。发送到 CLI 时会自动转换为 `continue`。
</Note>

#### `AsyncHookJSONOutput`

延迟 Hook 执行的异步 Hook 输出。

```python
class AsyncHookJSONOutput(TypedDict):
    async_: Literal[True]             # Set to True to defer execution
    asyncTimeout: NotRequired[int]    # Timeout in milliseconds
```

<Note>
在 Python 代码中使用 `async_`（带下划线）。发送到 CLI 时会自动转换为 `async`。
</Note>

### Hook 使用示例

此示例注册了两个 Hook：一个阻止危险的 bash 命令（如 `rm -rf /`），另一个记录所有工具使用以供审计。安全 Hook 仅在 Bash 命令上运行（通过 `matcher`），而日志 Hook 在所有工具上运行。

```python
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, HookContext
from typing import Any

async def validate_bash_command(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Validate and potentially block dangerous bash commands."""
    if input_data['tool_name'] == 'Bash':
        command = input_data['tool_input'].get('command', '')
        if 'rm -rf /' in command:
            return {
                'hookSpecificOutput': {
                    'hookEventName': 'PreToolUse',
                    'permissionDecision': 'deny',
                    'permissionDecisionReason': 'Dangerous command blocked'
                }
            }
    return {}

async def log_tool_use(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Log all tool usage for auditing."""
    print(f"Tool used: {input_data.get('tool_name')}")
    return {}

options = ClaudeAgentOptions(
    hooks={
        'PreToolUse': [
            HookMatcher(matcher='Bash', hooks=[validate_bash_command], timeout=120),  # 2 min for validation
            HookMatcher(hooks=[log_tool_use])  # Applies to all tools (default 60s timeout)
        ],
        'PostToolUse': [
            HookMatcher(hooks=[log_tool_use])
        ]
    }
)

async for message in query(
    prompt="Analyze this codebase",
    options=options
):
    print(message)
```

## 工具输入/输出类型

所有内置 Claude Code 工具的输入/输出模式文档。虽然 Python SDK 不将这些导出为类型，但它们代表了消息中工具输入和输出的结构。

### Task

**工具名称：** `Task`

**输入：**

```python
{
    "description": str,      # A short (3-5 word) description of the task
    "prompt": str,           # The task for the agent to perform
    "subagent_type": str     # The type of specialized agent to use
}
```

**输出：**

```python
{
    "result": str,                    # Final result from the subagent
    "usage": dict | None,             # Token usage statistics
    "total_cost_usd": float | None,  # Total cost in USD
    "duration_ms": int | None         # Execution duration in milliseconds
}
```

### AskUserQuestion

**工具名称：** `AskUserQuestion`

在执行期间向用户提出澄清问题。有关使用详情，请参阅[处理审批和用户输入](/docs/zh-CN/agent-sdk/user-input#handle-clarifying-questions)。

**输入：**

```python
{
    "questions": [                    # Questions to ask the user (1-4 questions)
        {
            "question": str,          # The complete question to ask the user
            "header": str,            # Very short label displayed as a chip/tag (max 12 chars)
            "options": [              # The available choices (2-4 options)
                {
                    "label": str,         # Display text for this option (1-5 words)
                    "description": str    # Explanation of what this option means
                }
            ],
            "multiSelect": bool       # Set to true to allow multiple selections
        }
    ],
    "answers": dict | None            # User answers populated by the permission system
}
```

**输出：**

```python
{
    "questions": [                    # The questions that were asked
        {
            "question": str,
            "header": str,
            "options": [{"label": str, "description": str}],
            "multiSelect": bool
        }
    ],
    "answers": dict[str, str]         # Maps question text to answer string
                                      # Multi-select answers are comma-separated
}
```

### Bash

**工具名称：** `Bash`

**输入：**

```python
{
    "command": str,                  # The command to execute
    "timeout": int | None,           # Optional timeout in milliseconds (max 600000)
    "description": str | None,       # Clear, concise description (5-10 words)
    "run_in_background": bool | None # Set to true to run in background
}
```

**输出：**

```python
{
    "output": str,              # Combined stdout and stderr output
    "exitCode": int,            # Exit code of the command
    "killed": bool | None,      # Whether command was killed due to timeout
    "shellId": str | None       # Shell ID for background processes
}
```

### Edit

**工具名称：** `Edit`

**输入：**

```python
{
    "file_path": str,           # The absolute path to the file to modify
    "old_string": str,          # The text to replace
    "new_string": str,          # The text to replace it with
    "replace_all": bool | None  # Replace all occurrences (default False)
}
```

**输出：**

```python
{
    "message": str,      # Confirmation message
    "replacements": int, # Number of replacements made
    "file_path": str     # File path that was edited
}
```

### Read

**工具名称：** `Read`

**输入：**

```python
{
    "file_path": str,       # The absolute path to the file to read
    "offset": int | None,   # The line number to start reading from
    "limit": int | None     # The number of lines to read
}
```

**输出（文本文件）：**

```python
{
    "content": str,         # File contents with line numbers
    "total_lines": int,     # Total number of lines in file
    "lines_returned": int   # Lines actually returned
}
```

**输出（图片）：**

```python
{
    "image": str,       # Base64 encoded image data
    "mime_type": str,   # Image MIME type
    "file_size": int    # File size in bytes
}
```

### Write

**工具名称：** `Write`

**输入：**

```python
{
    "file_path": str,  # The absolute path to the file to write
    "content": str     # The content to write to the file
}
```

**输出：**

```python
{
    "message": str,        # Success message
    "bytes_written": int,  # Number of bytes written
    "file_path": str       # File path that was written
}
```

### Glob

**工具名称：** `Glob`

**输入：**

```python
{
    "pattern": str,       # The glob pattern to match files against
    "path": str | None    # The directory to search in (defaults to cwd)
}
```

**输出：**

```python
{
    "matches": list[str],  # Array of matching file paths
    "count": int,          # Number of matches found
    "search_path": str     # Search directory used
}
```

### Grep

**工具名称：** `Grep`

**输入：**

```python
{
    "pattern": str,                    # The regular expression pattern
    "path": str | None,                # File or directory to search in
    "glob": str | None,                # Glob pattern to filter files
    "type": str | None,                # File type to search
    "output_mode": str | None,         # "content", "files_with_matches", or "count"
    "-i": bool | None,                 # Case insensitive search
    "-n": bool | None,                 # Show line numbers
    "-B": int | None,                  # Lines to show before each match
    "-A": int | None,                  # Lines to show after each match
    "-C": int | None,                  # Lines to show before and after
    "head_limit": int | None,          # Limit output to first N lines/entries
    "multiline": bool | None           # Enable multiline mode
}
```

**输出（content 模式）：**

```python
{
    "matches": [
        {
            "file": str,
            "line_number": int | None,
            "line": str,
            "before_context": list[str] | None,
            "after_context": list[str] | None
        }
    ],
    "total_matches": int
}
```

**输出（files_with_matches 模式）：**

```python
{
    "files": list[str],  # Files containing matches
    "count": int         # Number of files with matches
}
```

### NotebookEdit

**工具名称：** `NotebookEdit`

**输入：**

```python
{
    "notebook_path": str,                     # Absolute path to the Jupyter notebook
    "cell_id": str | None,                    # The ID of the cell to edit
    "new_source": str,                        # The new source for the cell
    "cell_type": "code" | "markdown" | None,  # The type of the cell
    "edit_mode": "replace" | "insert" | "delete" | None  # Edit operation type
}
```

**输出：**

```python
{
    "message": str,                              # Success message
    "edit_type": "replaced" | "inserted" | "deleted",  # Type of edit performed
    "cell_id": str | None,                       # Cell ID that was affected
    "total_cells": int                           # Total cells in notebook after edit
}
```

### WebFetch

**工具名称：** `WebFetch`

**输入：**

```python
{
    "url": str,     # The URL to fetch content from
    "prompt": str   # The prompt to run on the fetched content
}
```

**输出：**

```python
{
    "response": str,           # AI model's response to the prompt
    "url": str,                # URL that was fetched
    "final_url": str | None,   # Final URL after redirects
    "status_code": int | None  # HTTP status code
}
```

### WebSearch

**工具名称：** `WebSearch`

**输入：**

```python
{
    "query": str,                        # The search query to use
    "allowed_domains": list[str] | None, # Only include results from these domains
    "blocked_domains": list[str] | None  # Never include results from these domains
}
```

**输出：**

```python
{
    "results": [
        {
            "title": str,
            "url": str,
            "snippet": str,
            "metadata": dict | None
        }
    ],
    "total_results": int,
    "query": str
}
```

### TodoWrite

**工具名称：** `TodoWrite`

**输入：**

```python
{
    "todos": [
        {
            "content": str,                              # The task description
            "status": "pending" | "in_progress" | "completed",  # Task status
            "activeForm": str                            # Active form of the description
        }
    ]
}
```

**输出：**

```python
{
    "message": str,  # Success message
    "stats": {
        "total": int,
        "pending": int,
        "in_progress": int,
        "completed": int
    }
}
```

### BashOutput

**工具名称：** `BashOutput`

**输入：**

```python
{
    "bash_id": str,       # The ID of the background shell
    "filter": str | None  # Optional regex to filter output lines
}
```

**输出：**

```python
{
    "output": str,                                      # New output since last check
    "status": "running" | "completed" | "failed",       # Current shell status
    "exitCode": int | None                              # Exit code when completed
}
```

### KillBash

**工具名称：** `KillBash`

**输入：**

```python
{
    "shell_id": str  # The ID of the background shell to kill
}
```

**输出：**

```python
{
    "message": str,  # Success message
    "shell_id": str  # ID of the killed shell
}
```

### ExitPlanMode

**工具名称：** `ExitPlanMode`

**输入：**

```python
{
    "plan": str  # The plan to run by the user for approval
}
```

**输出：**

```python
{
    "message": str,          # Confirmation message
    "approved": bool | None  # Whether user approved the plan
}
```

### ListMcpResources

**工具名称：** `ListMcpResources`

**输入：**

```python
{
    "server": str | None  # Optional server name to filter resources by
}
```

**输出：**

```python
{
    "resources": [
        {
            "uri": str,
            "name": str,
            "description": str | None,
            "mimeType": str | None,
            "server": str
        }
    ],
    "total": int
}
```

### ReadMcpResource

**工具名称：** `ReadMcpResource`

**输入：**

```python
{
    "server": str,  # The MCP server name
    "uri": str      # The resource URI to read
}
```

**输出：**

```python
{
    "contents": [
        {
            "uri": str,
            "mimeType": str | None,
            "text": str | None,
            "blob": str | None
        }
    ],
    "server": str
}
```

## 使用 ClaudeSDKClient 的高级功能

### 构建连续对话界面

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock
import asyncio

class ConversationSession:
    """Maintains a single conversation session with Claude."""

    def __init__(self, options: ClaudeAgentOptions = None):
        self.client = ClaudeSDKClient(options)
        self.turn_count = 0

    async def start(self):
        await self.client.connect()
        print("Starting conversation session. Claude will remember context.")
        print("Commands: 'exit' to quit, 'interrupt' to stop current task, 'new' for new session")

        while True:
            user_input = input(f"\n[Turn {self.turn_count + 1}] You: ")

            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'interrupt':
                await self.client.interrupt()
                print("Task interrupted!")
                continue
            elif user_input.lower() == 'new':
                # Disconnect and reconnect for a fresh session
                await self.client.disconnect()
                await self.client.connect()
                self.turn_count = 0
                print("Started new conversation session (previous context cleared)")
                continue

            # Send message - Claude remembers all previous messages in this session
            await self.client.query(user_input)
            self.turn_count += 1

            # Process response
            print(f"[Turn {self.turn_count}] Claude: ", end="")
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text, end="")
            print()  # New line after response

        await self.client.disconnect()
        print(f"Conversation ended after {self.turn_count} turns.")

async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits"
    )
    session = ConversationSession(options)
    await session.start()

# Example conversation:
# Turn 1 - You: "Create a file called hello.py"
# Turn 1 - Claude: "I'll create a hello.py file for you..."
# Turn 2 - You: "What's in that file?"
# Turn 2 - Claude: "The hello.py file I just created contains..." (remembers!)
# Turn 3 - You: "Add a main function to it"
# Turn 3 - Claude: "I'll add a main function to hello.py..." (knows which file!)

asyncio.run(main())
```

### 使用 Hook 进行行为修改

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    HookMatcher,
    HookContext
)
import asyncio
from typing import Any

async def pre_tool_logger(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Log all tool usage before execution."""
    tool_name = input_data.get('tool_name', 'unknown')
    print(f"[PRE-TOOL] About to use: {tool_name}")

    # You can modify or block the tool execution here
    if tool_name == "Bash" and "rm -rf" in str(input_data.get('tool_input', {})):
        return {
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': 'Dangerous command blocked'
            }
        }
    return {}

async def post_tool_logger(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Log results after tool execution."""
    tool_name = input_data.get('tool_name', 'unknown')
    print(f"[POST-TOOL] Completed: {tool_name}")
    return {}

async def user_prompt_modifier(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """Add context to user prompts."""
    original_prompt = input_data.get('prompt', '')

    # Add timestamp to all prompts
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        'hookSpecificOutput': {
            'hookEventName': 'UserPromptSubmit',
            'updatedPrompt': f"[{timestamp}] {original_prompt}"
        }
    }

async def main():
    options = ClaudeAgentOptions(
        hooks={
            'PreToolUse': [
                HookMatcher(hooks=[pre_tool_logger]),
                HookMatcher(matcher='Bash', hooks=[pre_tool_logger])
            ],
            'PostToolUse': [
                HookMatcher(hooks=[post_tool_logger])
            ],
            'UserPromptSubmit': [
                HookMatcher(hooks=[user_prompt_modifier])
            ]
        },
        allowed_tools=["Read", "Write", "Bash"]
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("List files in current directory")

        async for message in client.receive_response():
            # Hooks will automatically log tool usage
            pass

asyncio.run(main())
```

### 实时进度监控

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ToolUseBlock,
    ToolResultBlock,
    TextBlock
)
import asyncio

async def monitor_progress():
    options = ClaudeAgentOptions(
        allowed_tools=["Write", "Bash"],
        permission_mode="acceptEdits"
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            "Create 5 Python files with different sorting algorithms"
        )

        # Monitor progress in real-time
        files_created = []
        async for message in client.receive_messages():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        if block.name == "Write":
                            file_path = block.input.get("file_path", "")
                            print(f"🔨 Creating: {file_path}")
                    elif isinstance(block, ToolResultBlock):
                        print(f"✅ Completed tool execution")
                    elif isinstance(block, TextBlock):
                        print(f"💭 Claude says: {block.text[:100]}...")

            # Check if we've received the final result
            if hasattr(message, 'subtype') and message.subtype in ['success', 'error']:
                print(f"\n🎯 Task completed!")
                break

asyncio.run(monitor_progress())
```

## 使用示例

### 基本文件操作（使用 query）

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ToolUseBlock
import asyncio

async def create_project():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode='acceptEdits',
        cwd="/home/user/project"
    )

    async for message in query(
        prompt="Create a Python project structure with setup.py",
        options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"Using tool: {block.name}")

asyncio.run(create_project())
```

### 错误处理

```python
from claude_agent_sdk import (
    query,
    CLINotFoundError,
    ProcessError,
    CLIJSONDecodeError
)

try:
    async for message in query(prompt="Hello"):
        print(message)
except CLINotFoundError:
    print("Please install Claude Code: npm install -g @anthropic-ai/claude-code")
except ProcessError as e:
    print(f"Process failed with exit code: {e.exit_code}")
except CLIJSONDecodeError as e:
    print(f"Failed to parse response: {e}")
```

### 使用客户端的流式模式

```python
from claude_agent_sdk import ClaudeSDKClient
import asyncio

async def interactive_session():
    async with ClaudeSDKClient() as client:
        # Send initial message
        await client.query("What's the weather like?")

        # Process responses
        async for msg in client.receive_response():
            print(msg)

        # Send follow-up
        await client.query("Tell me more about that")

        # Process follow-up response
        async for msg in client.receive_response():
            print(msg)

asyncio.run(interactive_session())
```

### 使用 ClaudeSDKClient 的自定义工具

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock
)
import asyncio
from typing import Any

# Define custom tools with @tool decorator
@tool("calculate", "Perform mathematical calculations", {"expression": str})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = eval(args["expression"], {"__builtins__": {}})
        return {
            "content": [{
                "type": "text",
                "text": f"Result: {result}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            "is_error": True
        }

@tool("get_time", "Get current time", {})
async def get_time(args: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "content": [{
            "type": "text",
            "text": f"Current time: {current_time}"
        }]
    }

async def main():
    # Create SDK MCP server with custom tools
    my_server = create_sdk_mcp_server(
        name="utilities",
        version="1.0.0",
        tools=[calculate, get_time]
    )

    # Configure options with the server
    options = ClaudeAgentOptions(
        mcp_servers={"utils": my_server},
        allowed_tools=[
            "mcp__utils__calculate",
            "mcp__utils__get_time"
        ]
    )

    # Use ClaudeSDKClient for interactive tool usage
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What's 123 * 456?")

        # Process calculation response
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Calculation: {block.text}")

        # Follow up with time query
        await client.query("What time is it now?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Time: {block.text}")

asyncio.run(main())
```

## 沙箱配置

### `SandboxSettings`

沙箱行为的配置。使用此选项以编程方式启用命令沙箱并配置网络限制。

```python
class SandboxSettings(TypedDict, total=False):
    enabled: bool
    autoAllowBashIfSandboxed: bool
    excludedCommands: list[str]
    allowUnsandboxedCommands: bool
    network: SandboxNetworkConfig
    ignoreViolations: SandboxIgnoreViolations
    enableWeakerNestedSandbox: bool
```

| 属性 | 类型 | 默认值 | 描述 |
| :------- | :--- | :------ | :---------- |
| `enabled` | `bool` | `False` | 启用命令执行的沙箱模式 |
| `autoAllowBashIfSandboxed` | `bool` | `False` | 启用沙箱时自动批准 bash 命令 |
| `excludedCommands` | `list[str]` | `[]` | 始终绕过沙箱限制的命令（例如 `["docker"]`）。这些命令会自动在沙箱外运行，无需模型参与 |
| `allowUnsandboxedCommands` | `bool` | `False` | 允许模型请求在沙箱外运行命令。当设置为 `True` 时，模型可以在工具输入中设置 `dangerouslyDisableSandbox`，这将回退到[权限系统](#permissions-fallback-for-unsandboxed-commands) |
| `network` | [`SandboxNetworkConfig`](#sandboxnetworkconfig) | `None` | 网络特定的沙箱配置 |
| `ignoreViolations` | [`SandboxIgnoreViolations`](#sandboxignoreviolations) | `None` | 配置要忽略的沙箱违规 |
| `enableWeakerNestedSandbox` | `bool` | `False` | 启用较弱的嵌套沙箱以提高兼容性 |

<Note>
**文件系统和网络访问限制**不通过沙箱设置进行配置。相反，它们源自[权限规则](https://code.claude.com/docs/zh-CN/settings#permission-settings)：

- **文件系统读取限制**：读取拒绝规则
- **文件系统写入限制**：编辑允许/拒绝规则
- **网络限制**：WebFetch 允许/拒绝规则

使用沙箱设置进行命令执行沙箱化，使用权限规则进行文件系统和网络访问控制。
</Note>

#### 使用示例

```python
from claude_agent_sdk import query, ClaudeAgentOptions, SandboxSettings

sandbox_settings: SandboxSettings = {
    "enabled": True,
    "autoAllowBashIfSandboxed": True,
    "network": {
        "allowLocalBinding": True
    }
}

async for message in query(
    prompt="Build and test my project",
    options=ClaudeAgentOptions(sandbox=sandbox_settings)
):
    print(message)
```

<Warning>
**Unix 套接字安全**：`allowUnixSockets` 选项可以授予对强大系统服务的访问权限。例如，允许 `/var/run/docker.sock` 实际上通过 Docker API 授予了对主机系统的完全访问权限，绕过了沙箱隔离。仅允许严格必要的 Unix 套接字，并了解每个套接字的安全影响。
</Warning>

### `SandboxNetworkConfig`

沙箱模式的网络特定配置。

```python
class SandboxNetworkConfig(TypedDict, total=False):
    allowLocalBinding: bool
    allowUnixSockets: list[str]
    allowAllUnixSockets: bool
    httpProxyPort: int
    socksProxyPort: int
```

| 属性 | 类型 | 默认值 | 描述 |
| :------- | :--- | :------ | :---------- |
| `allowLocalBinding` | `bool` | `False` | 允许进程绑定到本地端口（例如用于开发服务器） |
| `allowUnixSockets` | `list[str]` | `[]` | 进程可以访问的 Unix 套接字路径（例如 Docker 套接字） |
| `allowAllUnixSockets` | `bool` | `False` | 允许访问所有 Unix 套接字 |
| `httpProxyPort` | `int` | `None` | 用于网络请求的 HTTP 代理端口 |
| `socksProxyPort` | `int` | `None` | 用于网络请求的 SOCKS 代理端口 |

### `SandboxIgnoreViolations`

忽略特定沙箱违规的配置。

```python
class SandboxIgnoreViolations(TypedDict, total=False):
    file: list[str]
    network: list[str]
```

| 属性 | 类型 | 默认值 | 描述 |
| :------- | :--- | :------ | :---------- |
| `file` | `list[str]` | `[]` | 要忽略违规的文件路径模式 |
| `network` | `list[str]` | `[]` | 要忽略违规的网络模式 |

### 非沙箱命令的权限回退

当启用 `allowUnsandboxedCommands` 时，模型可以通过在工具输入中设置 `dangerouslyDisableSandbox: True` 来请求在沙箱外运行命令。这些请求会回退到现有的权限系统，这意味着您的 `can_use_tool` 处理程序将被调用，允许您实现自定义授权逻辑。

<Note>
**`excludedCommands` 与 `allowUnsandboxedCommands` 的区别：**
- `excludedCommands`：一个静态命令列表，始终自动绕过沙箱（例如 `["docker"]`）。模型对此没有控制权。
- `allowUnsandboxedCommands`：允许模型在运行时通过在工具输入中设置 `dangerouslyDisableSandbox: True` 来决定是否请求非沙箱执行。
</Note>

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def can_use_tool(tool: str, input: dict) -> bool:
    # Check if the model is requesting to bypass the sandbox
    if tool == "Bash" and input.get("dangerouslyDisableSandbox"):
        # The model wants to run this command outside the sandbox
        print(f"Unsandboxed command requested: {input.get('command')}")

        # Return True to allow, False to deny
        return is_command_authorized(input.get("command"))
    return True

async def main():
    async for message in query(
        prompt="Deploy my application",
        options=ClaudeAgentOptions(
            sandbox={
                "enabled": True,
                "allowUnsandboxedCommands": True  # Model can request unsandboxed execution
            },
            permission_mode="default",
            can_use_tool=can_use_tool
        )
    ):
        print(message)
```

此模式使您能够：

- **审计模型请求**：记录模型何时请求非沙箱执行
- **实现允许列表**：仅允许特定命令在非沙箱环境中运行
- **添加审批工作流**：要求对特权操作进行明确授权

<Warning>
使用 `dangerouslyDisableSandbox: True` 运行的命令具有完全的系统访问权限。请确保您的 `can_use_tool` 处理程序仔细验证这些请求。

如果 `permission_mode` 设置为 `bypassPermissions` 且 `allow_unsandboxed_commands` 已启用，模型可以在没有任何审批提示的情况下自主在沙箱外执行命令。这种组合实际上允许模型静默地逃脱沙箱隔离。
</Warning>

## 另请参阅

- [Python SDK 指南](/docs/zh-CN/agent-sdk/python) - 教程和示例
- [SDK 概述](/docs/zh-CN/agent-sdk/overview) - 通用 SDK 概念
- [TypeScript SDK 参考](/docs/zh-CN/agent-sdk/typescript) - TypeScript SDK 文档
- [CLI 参考](https://code.claude.com/docs/zh-CN/cli-reference) - 命令行界面
- [常见工作流](https://code.claude.com/docs/zh-CN/common-workflows) - 分步指南