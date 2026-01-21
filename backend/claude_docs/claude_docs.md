# Agent SDK 参考 - Python

Python Agent SDK 的完整 API 参考，包括所有函数、类型和类。

---

## 安装

```bash
pip install claude-agent-sdk
```

## 在 `query()` 和 `ClaudeSDKClient` 之间选择

Python SDK 提供了两种与 Claude Code 交互的方式：

### 快速比较

| 功能             | `query()`                     | `ClaudeSDKClient`                  |
| :------------------ | :---------------------------- | :--------------------------------- |
| **会话**         | 每次创建新会话 | 重用同一会话                |
| **对话**    | 单次交换               | 同一上下文中的多次交换 |
| **连接**      | 自动管理         | 手动控制                     |
| **流式输入** | ✅ 支持                  | ✅ 支持                       |
| **中断**      | ❌ 不支持              | ✅ 支持                       |
| **钩子**           | ❌ 不支持              | ✅ 支持                       |
| **自定义工具**    | ❌ 不支持              | ✅ 支持                       |
| **继续聊天**   | ❌ 每次新会话      | ✅ 保持对话          |
| **用例**        | 一次性任务                 | 持续对话           |

### 何时使用 `query()`（每次新建会话）

**最适合：**

- 一次性问题，不需要对话历史
- 不需要来自之前交换的上下文的独立任务
- 简单的自动化脚本
- 当你想每次都重新开始时

### 何时使用 `ClaudeSDKClient`（持续对话）

**最适合：**

- **继续对话** - 当你需要 Claude 记住上下文时
- **后续问题** - 基于之前的响应进行构建
- **交互式应用程序** - 聊天界面、REPL
- **响应驱动的逻辑** - 当下一步操作取决于 Claude 的响应时
- **会话控制** - 显式管理对话生命周期

## 函数

### `query()`

为每次与 Claude Code 的交互创建一个新会话。返回一个异步迭代器，当消息到达时产生消息。每次调用 `query()` 都会重新开始，不记得之前的交互。

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
| `options` | `ClaudeAgentOptions \| None` | 可选配置对象（如果为 None，默认为 `ClaudeAgentOptions()`） |

#### 返回

返回一个 `AsyncIterator[Message]`，从对话中产生消息。

#### 示例 - 带选项

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

#### 返回

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

创建一个在你的 Python 应用程序内运行的进程内 MCP 服务器。

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

#### 返回

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

**在多次交换中维持对话会话。** 这是 TypeScript SDK 的 `query()` 函数内部工作方式的 Python 等价物 - 它创建一个可以继续对话的客户端对象。

#### 关键特性

- **会话连续性**：在多个 `query()` 调用中维持对话上下文
- **同一对话**：Claude 记住会话中的之前消息
- **中断支持**：可以在 Claude 执行中途停止
- **显式生命周期**：你控制会话何时开始和结束
- **响应驱动流**：可以对响应做出反应并发送后续消息
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
| `receive_messages()`        | 以异步迭代器的形式接收来自 Claude 的所有消息               |
| `receive_response()`        | 接收消息直到并包括 ResultMessage                |
| `interrupt()`               | 发送中断信号（仅在流式模式下有效）                |
| `rewind_files(user_message_uuid)` | 将文件恢复到指定用户消息时的状态。需要 `enable_file_checkpointing=True`。参见 [文件检查点](/docs/zh-CN/agent-sdk/file-checkpointing) |
| `disconnect()`              | 从 Claude 断开连接                                              |

#### 上下文管理器支持

客户端可以用作异步上下文管理器以自动管理连接：

```python
async with ClaudeSDKClient() as client:
    await client.query("Hello Claude")
    async for message in client.receive_response():
        print(message)
```

> **重要：** 在迭代消息时，避免使用 `break` 提前退出，因为这可能会导致 asyncio 清理问题。相反，让迭代自然完成或使用标志来跟踪何时找到了你需要的内容。

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

async def custom_permission_handler(
    tool_name: str,
    input_data: dict,
    context: dict
):
    """Custom logic for tool permissions."""

    # Block writes to system directories
    if tool_name == "Write" and input_data.get("file_path", "").startswith("/system/"):
        return {
            "behavior": "deny",
            "message": "System directory write not allowed",
            "interrupt": True
        }

    # Redirect sensitive file operations
    if tool_name in ["Write", "Edit"] and "config" in input_data.get("file_path", ""):
        safe_path = f"./sandbox/{input_data['file_path']}"
        return {
            "behavior": "allow",
            "updatedInput": {**input_data, "file_path": safe_path}
        }

    # Allow everything else
    return {
        "behavior": "allow",
        "updatedInput": input_data
    }

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
| `input_schema` | `type[T] \| dict[str, Any]`                | 输入验证的模式                |
| `handler`      | `Callable[[T], Awaitable[dict[str, Any]]]` | 处理工具执行的异步函数 |

### `ClaudeAgentOptions`

Claude Code 查询的配置数据类。

```python
@dataclass
class ClaudeAgentOptions:
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    output_format: OutputFormat | None = None
    permission_prompt_tool_name: str | None = None
    cwd: str | Path | None = None
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
```

| 属性                      | 类型                                         | 默认值              | 描述                                                                                                                                                                             |
| :---------------------------- | :------------------------------------------- | :------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `allowed_tools`               | `list[str]`                                  | `[]`                 | 允许的工具名称列表                                                                                                                                                              |
| `system_prompt`               | `str \| SystemPromptPreset \| None`          | `None`               | 系统提示配置。传递字符串以获得自定义提示，或使用 `{"type": "preset", "preset": "claude_code"}` 以获得 Claude Code 的系统提示。添加 `"append"` 以扩展预设 |
| `mcp_servers`                 | `dict[str, McpServerConfig] \| str \| Path`  | `{}`                 | MCP 服务器配置或配置文件路径                                                                                                                                        |
| `permission_mode`             | `PermissionMode \| None`                     | `None`               | 工具使用的权限模式                                                                                                                                                          |
| `continue_conversation`       | `bool`                                       | `False`              | 继续最近的对话                                                                                                                                                   |
| `resume`                      | `str \| None`                                | `None`               | 要恢复的会话 ID                                                                                                                                                                    |
| `max_turns`                   | `int \| None`                                | `None`               | 最大对话轮数                                                                                                                                                              |
| `disallowed_tools`            | `list[str]`                                  | `[]`                 | 不允许的工具名称列表                                                                                                                                                           |
| `enable_file_checkpointing`   | `bool`                                       | `False`              | 启用文件更改跟踪以进行回退。参见 [文件检查点](/docs/zh-CN/agent-sdk/file-checkpointing)                                                                              |
| `model`                       | `str \| None`                                | `None`               | 要使用的 Claude 模型                                                                                                                                                                     |
| `output_format`               | [`OutputFormat`](#outputformat) ` \| None`   | `None`               | 定义代理结果的输出格式。详见 [结构化输出](/docs/zh-CN/agent-sdk/structured-outputs)                                                                    |
| `permission_prompt_tool_name` | `str \| None`                                | `None`               | 权限提示的 MCP 工具名称                                                                                                                                                    |
| `cwd`                         | `str \| Path \| None`                        | `None`               | 当前工作目录                                                                                                                                                               |
| `settings`                    | `str \| None`                                | `None`               | 设置文件的路径                                                                                                                                                                   |
| `add_dirs`                    | `list[str \| Path]`                          | `[]`                 | Claude 可以访问的其他目录                                                                                                                                                |
| `env`                         | `dict[str, str]`                             | `{}`                 | 环境变量                                                                                                                                                                   |
| `extra_args`                  | `dict[str, str \| None]`                     | `{}`                 | 直接传递给 CLI 的其他 CLI 参数                                                                                    |
| `max_buffer_size`             | `int \| None`                                | `None`               | 缓冲 CLI stdout 时的最大字节数                                                                                                                                                 |
| `debug_stderr`                | `Any`                                        | `sys.stderr`         | _已弃用_ - 用于调试输出的类文件对象。改用 `stderr` 回调                                                                                         |
| `stderr`                      | `Callable[[str], None] \| None`              | `None`               | CLI 中 stderr 输出的回调函数                                                                                                                            |
| `can_use_tool`                | `CanUseTool \| None`                         | `None`               | 工具权限回调函数                                                                                                                                                       |
| `hooks`                       | `dict[HookEvent, list[HookMatcher]] \| None` | `None`               | 用于拦截事件的钩子配置                                                                                                                             |
| `user`                        | `str \| None`                                | `None`               | 用户标识符                                                                                                                                                                         |
| `include_partial_messages`    | `bool`                                       | `False`              | 包括部分消息流式事件                                                                                                                                                |
| `fork_session`                | `bool`                                       | `False`              | 当使用 `resume` 恢复时，分叉到新的会话 ID 而不是继续原始会话                                                                        |
| `agents`                      | `dict[str, AgentDefinition] \| None`         | `None`               | 以编程方式定义的子代理                                                                                                                                      |
| `plugins`                     | `list[SdkPluginConfig]`                      | `[]`                 | 从本地路径加载自定义插件。详见 [插件](/docs/zh-CN/agent-sdk/plugins)                                             |
| `sandbox`                     | [`SandboxSettings`](#sandboxsettings) ` \| None` | `None`              | 以编程方式配置沙箱行为。详见 [沙箱设置](#sandboxsettings)                                        |
| `setting_sources`             | `list[SettingSource] \| None`                | `None`（无设置） | 控制加载哪些文件系统设置。省略时，不加载任何设置。**注意：** 必须包含 `"project"` 以加载 CLAUDE.md 文件                                             |

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

使用 Claude Code 的预设系统提示和可选添加的配置。

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
| `append` | 否       | 要附加到预设系统提示的其他指令 |

### `SettingSource`

控制 SDK 加载设置的文件系统配置源。

```python
SettingSource = Literal["user", "project", "local"]
```

| 值       | 描述                                  | 位置                      |
| :---------- | :------------------------------------------- | :---------------------------- |
| `"user"`    | 全局用户设置                         | `~/.claude/settings.json`     |
| `"project"` | 共享项目设置（版本控制）       | `.claude/settings.json`       |
| `"local"`   | 本地项目设置（gitignored）          | `.claude/settings.local.json` |

#### 默认行为

当 `setting_sources` **省略**或**为 `None`** 时，SDK **不会**加载任何文件系统设置。这为 SDK 应用程序提供了隔离。

#### 为什么使用 setting_sources？

**加载所有文件系统设置（旧版行为）：**

```python
# 像 SDK v0.0.x 那样加载所有设置
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
# 仅加载项目设置，忽略用户和本地设置
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
# 通过排除本地设置确保 CI 中的一致行为
async for message in query(
    prompt="Run tests",
    options=ClaudeAgentOptions(
        setting_sources=["project"],  # Only team-shared settings
        permission_mode="bypassPermissions"
    )
):
    print(message)
```

**仅 SDK 应用程序：**

```python
# 以编程方式定义所有内容（默认行为）
# 无文件系统依赖 - setting_sources 默认为 None
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
# 加载项目设置以包含 CLAUDE.md 文件
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

加载多个源时，设置按以下优先级（从高到低）合并：

1. 本地设置（`.claude/settings.local.json`）
2. 项目设置（`.claude/settings.json`）
3. 用户设置（`~/.claude/settings.json`）

编程选项（如 `agents`、`allowed_tools`）始终覆盖文件系统设置。

### `AgentDefinition`

以编程方式定义的子代理的配置。

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
| `description` | 是      | 何时使用此代理的自然语言描述         |
| `tools`       | 否       | 允许的工具名称数组。如果省略，继承所有工具    |
| `prompt`      | 是      | 代理的系统提示                                      |
| `model`       | 否       | 此代理的模型覆盖。如果省略，使用主模型 |

### `PermissionMode`

用于控制工具执行的权限模式。

```python
PermissionMode = Literal[
    "default",           # Standard permission behavior
    "acceptEdits",       # Auto-accept file edits
    "plan",              # Planning mode - no execution
    "bypassPermissions"  # Bypass all permission checks (use with caution)
]
```

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

SDK 中加载插件的配置。

```python
class SdkPluginConfig(TypedDict):
    type: Literal["local"]
    path: str
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `type` | `Literal["local"]` | 必须为 `"local"`（目前仅支持本地插件） |
| `path` | `str` | 插件目录的绝对或相对路径 |

**示例：**
```python
plugins=[
    {"type": "local", "path": "./my-plugin"},
    {"type": "local", "path": "/absolute/path/to/plugin"}
]
```

有关创建和使用插件的完整信息，请参见 [插件](/docs/zh-CN/agent-sdk/plugins)。

## 消息类型

### `Message`

所有可能消息的联合类型。

```python
Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage
```

### `UserMessage`

用户输入消息。

```python
@dataclass
class UserMessage:
    content: str | list[ContentBlock]
```

### `AssistantMessage`

带有内容块的助手响应消息。

```python
@dataclass
class AssistantMessage:
    content: list[ContentBlock]
    model: str
```

### `SystemMessage`

带有元数据的系统消息。

```python
@dataclass
class SystemMessage:
    subtype: str
    data: dict[str, Any]
```

### `ResultMessage`

包含成本和使用情况信息的最终结果消息。

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
```

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
    """Claude SDK 的基础错误。"""
```

### `CLINotFoundError`

当 Claude Code CLI 未安装或未找到时引发。

```python
class CLINotFoundError(CLIConnectionError):
    def __init__(self, message: str = "Claude Code not found", cli_path: str | None = None):
        """
        Args:
            message: 错误消息（默认值："Claude Code not found"）
            cli_path: 未找到的 CLI 的可选路径
        """
```

### `CLIConnectionError`

当连接到 Claude Code 失败时引发。

```python
class CLIConnectionError(ClaudeSDKError):
    """无法连接到 Claude Code。"""
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
            line: 解析失败的行
            original_error: 原始 JSON 解码异常
        """
        self.line = line
        self.original_error = original_error
```

## 钩子类型

有关使用钩子的综合指南、示例和常见模式，请参阅[钩子指南](/docs/zh-CN/agent-sdk/hooks)。

### `HookEvent`

支持的钩子事件类型。请注意，由于设置限制，Python SDK 不支持 SessionStart、SessionEnd 和 Notification 钩子。

```python
HookEvent = Literal[
    "PreToolUse",      # 在工具执行前调用
    "PostToolUse",     # 在工具执行后调用
    "UserPromptSubmit", # 当用户提交提示时调用
    "Stop",            # 当停止执行时调用
    "SubagentStop",    # 当子代理停止时调用
    "PreCompact"       # 在消息压缩前调用
]
```

### `HookCallback`

钩子回调函数的类型定义。

```python
HookCallback = Callable[
    [dict[str, Any], str | None, HookContext],
    Awaitable[dict[str, Any]]
]
```

参数：

- `input_data`: 钩子特定的输入数据（参见[钩子指南](/docs/zh-CN/agent-sdk/hooks#input-data)）
- `tool_use_id`: 可选的工具使用标识符（用于工具相关的钩子）
- `context`: 包含附加信息的钩子上下文

返回一个可能包含以下内容的字典：

- `decision`: `"block"` 以阻止该操作
- `systemMessage`: 要添加到记录的系统消息
- `hookSpecificOutput`: 钩子特定的输出数据

### `HookContext`

传递给钩子回调的上下文信息。

```python
@dataclass
class HookContext:
    signal: Any | None = None  # 未来：中止信号支持
```

### `HookMatcher`

用于将钩子匹配到特定事件或工具的配置。

```python
@dataclass
class HookMatcher:
    matcher: str | None = None        # 要匹配的工具名称或模式（例如，"Bash"、"Write|Edit"）
    hooks: list[HookCallback] = field(default_factory=list)  # 要执行的回调列表
    timeout: float | None = None        # 此匹配器中所有钩子的超时时间（秒）（默认值：60）
```

### 钩子使用示例

此示例注册两个钩子：一个阻止危险的 bash 命令（如 `rm -rf /`），另一个记录所有工具使用情况以进行审计。安全钩子仅在 Bash 命令上运行（通过 `matcher`），而日志钩子在所有工具上运行。

```python
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, HookContext
from typing import Any

async def validate_bash_command(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """验证并可能阻止危险的 bash 命令。"""
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
    """记录所有工具使用情况以进行审计。"""
    print(f"Tool used: {input_data.get('tool_name')}")
    return {}

options = ClaudeAgentOptions(
    hooks={
        'PreToolUse': [
            HookMatcher(matcher='Bash', hooks=[validate_bash_command], timeout=120),  # 验证 2 分钟
            HookMatcher(hooks=[log_tool_use])  # 适用于所有工具（默认 60 秒超时）
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

所有内置 Claude Code 工具的输入/输出架构文档。虽然 Python SDK 不将这些导出为类型，但它们代表消息中工具输入和输出的结构。

### Task

**工具名称：** `Task`

**输入：**

```python
{
    "description": str,      # 任务的简短（3-5 个单词）描述
    "prompt": str,           # 代理要执行的任务
    "subagent_type": str     # 要使用的专门代理的类型
}
```

**输出：**

```python
{
    "result": str,                    # 来自子代理的最终结果
    "usage": dict | None,             # 令牌使用统计
    "total_cost_usd": float | None,  # 美元总成本
    "duration_ms": int | None         # 执行持续时间（毫秒）
}
```

### Bash

**工具名称：** `Bash`

**输入：**

```python
{
    "command": str,                  # 要执行的命令
    "timeout": int | None,           # 可选的超时时间（毫秒）（最大 600000）
    "description": str | None,       # 清晰、简洁的描述（5-10 个单词）
    "run_in_background": bool | None # 设置为 true 以在后台运行
}
```

**输出：**

```python
{
    "output": str,              # 合并的 stdout 和 stderr 输出
    "exitCode": int,            # 命令的退出代码
    "killed": bool | None,      # 命令是否因超时而被杀死
    "shellId": str | None       # 后台进程的 Shell ID
}
```

### Edit

**工具名称：** `Edit`

**输入：**

```python
{
    "file_path": str,           # 要修改的文件的绝对路径
    "old_string": str,          # 要替换的文本
    "new_string": str,          # 替换为的文本
    "replace_all": bool | None  # 替换所有出现次数（默认 False）
}
```

**输出：**

```python
{
    "message": str,      # 确认消息
    "replacements": int, # 进行的替换次数
    "file_path": str     # 被编辑的文件路径
}
```

### Read

**工具名称：** `Read`

**输入：**

```python
{
    "file_path": str,       # 要读取的文件的绝对路径
    "offset": int | None,   # 开始读取的行号
    "limit": int | None     # 要读取的行数
}
```

**输出（文本文件）：**

```python
{
    "content": str,         # 带行号的文件内容
    "total_lines": int,     # 文件中的总行数
    "lines_returned": int   # 实际返回的行数
}
```

**输出（图像）：**

```python
{
    "image": str,       # Base64 编码的图像数据
    "mime_type": str,   # 图像 MIME 类型
    "file_size": int    # 文件大小（字节）
}
```

### Write

**工具名称：** `Write`

**输入：**

```python
{
    "file_path": str,  # 要写入的文件的绝对路径
    "content": str     # 要写入文件的内容
}
```

**输出：**

```python
{
    "message": str,        # 成功消息
    "bytes_written": int,  # 写入的字节数
    "file_path": str       # 被写入的文件路径
}
```

### Glob

**工具名称：** `Glob`

**输入：**

```python
{
    "pattern": str,       # 用于匹配文件的 glob 模式
    "path": str | None    # 要搜索的目录（默认为 cwd）
}
```

**输出：**

```python
{
    "matches": list[str],  # 匹配文件路径的数组
    "count": int,          # 找到的匹配数
    "search_path": str     # 使用的搜索目录
}
```

### Grep

**工具名称：** `Grep`

**输入：**

```python
{
    "pattern": str,                    # 正则表达式模式
    "path": str | None,                # 要搜索的文件或目录
    "glob": str | None,                # 用于过滤文件的 glob 模式
    "type": str | None,                # 要搜索的文件类型
    "output_mode": str | None,         # "content"、"files_with_matches" 或 "count"
    "-i": bool | None,                 # 不区分大小写搜索
    "-n": bool | None,                 # 显示行号
    "-B": int | None,                  # 每个匹配前显示的行数
    "-A": int | None,                  # 每个匹配后显示的行数
    "-C": int | None,                  # 每个匹配前后显示的行数
    "head_limit": int | None,          # 将输出限制为前 N 行/条目
    "multiline": bool | None           # 启用多行模式
}
```

**输出（内容模式）：**

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
    "files": list[str],  # 包含匹配的文件
    "count": int         # 包含匹配的文件数
}
```

### NotebookEdit

**工具名称：** `NotebookEdit`

**输入：**

```python
{
    "notebook_path": str,                     # Jupyter 笔记本的绝对路径
    "cell_id": str | None,                    # 要编辑的单元格的 ID
    "new_source": str,                        # 单元格的新源代码
    "cell_type": "code" | "markdown" | None,  # 单元格的类型
    "edit_mode": "replace" | "insert" | "delete" | None  # 编辑操作类型
}
```

**输出：**

```python
{
    "message": str,                              # 成功消息
    "edit_type": "replaced" | "inserted" | "deleted",  # 执行的编辑类型
    "cell_id": str | None,                       # 受影响的单元格 ID
    "total_cells": int                           # 编辑后笔记本中的总单元格数
}
```

### WebFetch

**工具名称：** `WebFetch`

**输入：**

```python
{
    "url": str,     # 要从中获取内容的 URL
    "prompt": str   # 在获取的内容上运行的提示
}
```

**输出：**

```python
{
    "response": str,           # AI 模型对提示的响应
    "url": str,                # 被获取的 URL
    "final_url": str | None,   # 重定向后的最终 URL
    "status_code": int | None  # HTTP 状态代码
}
```

### WebSearch

**工具名称：** `WebSearch`

**输入：**

```python
{
    "query": str,                        # 要使用的搜索查询
    "allowed_domains": list[str] | None, # 仅包含来自这些域的结果
    "blocked_domains": list[str] | None  # 永远不包含来自这些域的结果
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
            "content": str,                              # 任务描述
            "status": "pending" | "in_progress" | "completed",  # 任务状态
            "activeForm": str                            # 描述的活跃形式
        }
    ]
}
```

**输出：**

```python
{
    "message": str,  # 成功消息
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
    "bash_id": str,       # 后台 shell 的 ID
    "filter": str | None  # 可选的正则表达式以过滤输出行
}
```

**输出：**

```python
{
    "output": str,                                      # 自上次检查以来的新输出
    "status": "running" | "completed" | "failed",       # 当前 shell 状态
    "exitCode": int | None                              # 完成时的退出代码
}
```

### KillBash

**工具名称：** `KillBash`

**输入：**

```python
{
    "shell_id": str  # 要杀死的后台 shell 的 ID
}
```

**输出：**

```python
{
    "message": str,  # 成功消息
    "shell_id": str  # 被杀死的 shell 的 ID
}
```

### ExitPlanMode

**工具名称：** `ExitPlanMode`

**输入：**

```python
{
    "plan": str  # 用户批准运行的计划
}
```

**输出：**

```python
{
    "message": str,          # 确认消息
    "approved": bool | None  # 用户是否批准了计划
}
```

### ListMcpResources

**工具名称：** `ListMcpResources`

**输入：**

```python
{
    "server": str | None  # 可选的服务器名称以按其过滤资源
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
    "server": str,  # MCP 服务器名称
    "uri": str      # 要读取的资源 URI
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
    """维护与 Claude 的单个对话会话。"""

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
                # 断开连接并重新连接以获得新会话
                await self.client.disconnect()
                await self.client.connect()
                self.turn_count = 0
                print("Started new conversation session (previous context cleared)")
                continue

            # 发送消息 - Claude 记住此会话中的所有先前消息
            await self.client.query(user_input)
            self.turn_count += 1

            # 处理响应
            print(f"[Turn {self.turn_count}] Claude: ", end="")
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text, end="")
            print()  # 响应后的新行

        await self.client.disconnect()
        print(f"Conversation ended after {self.turn_count} turns.")

async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits"
    )
    session = ConversationSession(options)
    await session.start()

# 示例对话：
# Turn 1 - You: "Create a file called hello.py"
# Turn 1 - Claude: "I'll create a hello.py file for you..."
# Turn 2 - You: "What's in that file?"
# Turn 2 - Claude: "The hello.py file I just created contains..." (记住了！)
# Turn 3 - You: "Add a main function to it"
# Turn 3 - Claude: "I'll add a main function to hello.py..." (知道是哪个文件！)

asyncio.run(main())
```

### 使用钩子进行行为修改

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
    """在执行前记录所有工具使用情况。"""
    tool_name = input_data.get('tool_name', 'unknown')
    print(f"[PRE-TOOL] About to use: {tool_name}")

    # 您可以在此处修改或阻止工具执行
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
    """在工具执行后记录结果。"""
    tool_name = input_data.get('tool_name', 'unknown')
    print(f"[POST-TOOL] Completed: {tool_name}")
    return {}

async def user_prompt_modifier(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """向用户提示添加上下文。"""
    original_prompt = input_data.get('prompt', '')

    # 向所有提示添加时间戳
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
            # 钩子将自动记录工具使用情况
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

        # 实时监控进度
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

            # 检查是否收到了最终结果
            if hasattr(message, 'subtype') and message.subtype in ['success', 'error']:
                print(f"\n🎯 Task completed!")
                break

asyncio.run(monitor_progress())
```

## 示例用法

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
        # 发送初始消息
        await client.query("What's the weather like?")

        # 处理响应
        async for msg in client.receive_response():
            print(msg)

        # 发送后续消息
        await client.query("Tell me more about that")

        # 处理后续响应
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

# 使用 @tool 装饰器定义自定义工具
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
    # 使用自定义工具创建 SDK MCP 服务器
    my_server = create_sdk_mcp_server(
        name="utilities",
        version="1.0.0",
        tools=[calculate, get_time]
    )

    # 使用服务器配置选项
    options = ClaudeAgentOptions(
        mcp_servers={"utils": my_server},
        allowed_tools=[
            "mcp__utils__calculate",
            "mcp__utils__get_time"
        ]
    )

    # 使用 ClaudeSDKClient 进行交互式工具使用
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What's 123 * 456?")

        # 处理计算响应
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Calculation: {block.text}")

        # 后续时间查询
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
| `enabled` | `bool` | `False` | 为命令执行启用沙箱模式 |
| `autoAllowBashIfSandboxed` | `bool` | `False` | 启用沙箱时自动批准 bash 命令 |
| `excludedCommands` | `list[str]` | `[]` | 始终绕过沙箱限制的命令（例如，`["docker"]`）。这些命令自动在沙箱外运行，无需模型参与 |
| `allowUnsandboxedCommands` | `bool` | `False` | 允许模型请求在沙箱外运行命令。当为 `True` 时，模型可以在工具输入中设置 `dangerouslyDisableSandbox`，这会回退到[权限系统](#permissions-fallback-for-unsandboxed-commands) |
| `network` | [`SandboxNetworkConfig`](#sandboxnetworkconfig) | `None` | 网络特定的沙箱配置 |
| `ignoreViolations` | [`SandboxIgnoreViolations`](#sandboxignoreviolations) | `None` | 配置要忽略的沙箱违规 |
| `enableWeakerNestedSandbox` | `bool` | `False` | 启用较弱的嵌套沙箱以实现兼容性 |

<Note>
**文件系统和网络访问限制**不通过沙箱设置配置。相反，它们来自[权限规则](https://code.claude.com/docs/zh-CN/settings#permission-settings)：

- **文件系统读取限制**：读取拒绝规则
- **文件系统写入限制**：编辑允许/拒绝规则
- **网络限制**：WebFetch 允许/拒绝规则

使用沙箱设置进行命令执行沙箱，使用权限规则进行文件系统和网络访问控制。
</Note>

#### 示例用法

```python
from claude_agent_sdk import query, ClaudeAgentOptions, SandboxSettings

sandbox_settings: SandboxSettings = {
    "enabled": True,
    "autoAllowBashIfSandboxed": True,
    "excludedCommands": ["docker"],
    "network": {
        "allowLocalBinding": True,
        "allowUnixSockets": ["/var/run/docker.sock"]
    }
}

async for message in query(
    prompt="Build and test my project",
    options=ClaudeAgentOptions(sandbox=sandbox_settings)
):
    print(message)
```

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
| `allowLocalBinding` | `bool` | `False` | 允许进程绑定到本地端口（例如，用于开发服务器） |
| `allowUnixSockets` | `list[str]` | `[]` | 进程可以访问的 Unix 套接字路径（例如，Docker 套接字） |
| `allowAllUnixSockets` | `bool` | `False` | 允许访问所有 Unix 套接字 |
| `httpProxyPort` | `int` | `None` | 网络请求的 HTTP 代理端口 |
| `socksProxyPort` | `int` | `None` | 网络请求的 SOCKS 代理端口 |

### `SandboxIgnoreViolations`

用于忽略特定沙箱违规的配置。

```python
class SandboxIgnoreViolations(TypedDict, total=False):
    file: list[str]
    network: list[str]
```

| 属性 | 类型 | 默认值 | 描述 |
| :------- | :--- | :------ | :---------- |
| `file` | `list[str]` | `[]` | 要忽略违规的文件路径模式 |
| `network` | `list[str]` | `[]` | 要忽略违规的网络模式 |

### 沙箱外命令的权限回退

启用 `allowUnsandboxedCommands` 时，模型可以通过在工具输入中设置 `dangerouslyDisableSandbox: True` 来请求在沙箱外运行命令。这些请求回退到现有权限系统，这意味着您的 `can_use_tool` 处理程序将被调用，允许您实现自定义授权逻辑。

<Note>
**`excludedCommands` vs `allowUnsandboxedCommands`：**
- `excludedCommands`：始终自动绕过沙箱的静态命令列表（例如，`["docker"]`）。模型无法控制此。
- `allowUnsandboxedCommands`：让模型在运行时通过在工具输入中设置 `dangerouslyDisableSandbox: True` 来决定是否请求沙箱外执行。
</Note>

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async def can_use_tool(tool: str, input: dict) -> bool:
    # 检查模型是否请求绕过沙箱
    if tool == "Bash" and input.get("dangerouslyDisableSandbox"):
        # 模型想要在沙箱外运行此命令
        print(f"Unsandboxed command requested: {input.get('command')}")

        # 返回 True 以允许，False 以拒绝
        return is_command_authorized(input.get("command"))
    return True

async def main():
    async for message in query(
        prompt="Deploy my application",
        options=ClaudeAgentOptions(
            sandbox={
                "enabled": True,
                "allowUnsandboxedCommands": True  # 模型可以请求沙箱外执行
            },
            permission_mode="default",
            can_use_tool=can_use_tool
        )
    ):
        print(message)
```

此模式使您能够：

- **审计模型请求**：记录模型何时请求沙箱外执行
- **实现允许列表**：仅允许特定命令在沙箱外运行
- **添加批准工作流**：需要对特权操作进行明确授权

<Warning>
使用 `dangerouslyDisableSandbox: True` 运行的命令具有完整的系统访问权限。确保您的 `can_use_tool` 处理程序仔细验证这些请求。
</Warning>

## 另请参阅

- [Python SDK 指南](/docs/zh-CN/agent-sdk/python) - 教程和示例
- [SDK 概述](/docs/zh-CN/agent-sdk/overview) - 常规 SDK 概念
- [TypeScript SDK 参考](/docs/zh-CN/agent-sdk/typescript) - TypeScript SDK 文档
- [CLI 参考](https://code.claude.com/docs/zh-CN/cli-reference) - 命令行界面
- [常见工作流](https://code.claude.com/docs/zh-CN/common-workflows) - 分步指南