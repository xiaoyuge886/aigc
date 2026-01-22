# Agent SDK 参考 - Python

Python Agent SDK 的完整 API 参考，包括所有函数、类型和类。

## 安装

```bash
pip install claude-agent-sdk
```

## 在 `query()` 和 `ClaudeSDKClient` 之间选择

Python SDK 提供了两种与 Claude Code 交互的方式：

### 快速比较

| 功能 | `query()` | `ClaudeSDKClient` |
| --- | --- | --- |
| __会话__ | 每次创建新会话 | 重用同一会话 |
| __对话__ | 单次交换 | 同一上下文中的多次交换 |
| __连接__ | 自动管理 | 手动控制 |
| __流式输入__ | ✅ 支持 | ✅ 支持 |
| __中断__ | ❌ 不支持 | ✅ 支持 |
| __钩子__ | ❌ 不支持 | ✅ 支持 |
| __自定义工具__ | ❌ 不支持 | ✅ 支持 |
| __继续聊天__ | ❌ 每次新会话 | ✅ 维持对话 |
| __用例__ | 一次性任务 | 连续对话 |

### 何时使用 `query()`（每次新建会话）

__最适合：__

- 不需要对话历史的一次性问题
- 不需要来自之前交换的上下文的独立任务
- 简单的自动化脚本
- 当您想每次都重新开始时

### 何时使用 `ClaudeSDKClient`（连续对话）

__最适合：__

- __继续对话__ - 当您需要 Claude 记住上下文时
- __后续问题__ - 基于之前的回应进行构建
- __交互式应用程序__ - 聊天界面、REPL
- __响应驱动的逻辑__ - 当下一步操作取决于 Claude 的响应时
- __会话控制__ - 显式管理对话生命周期

## 函数

### `query()`

为每次与 Claude Code 的交互创建一个新会话。返回一个异步迭代器，在消息到达时产生消息。每次调用 `query()` 都会重新开始，不记得之前的交互。

```python
async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: ClaudeAgentOptions | None = None
) -> AsyncIterator[Message]
```

#### 参数

| 参数 | 类型 | 描述 |
| --- | --- | --- |
| `prompt` | `str | AsyncIterable[dict]` | 输入提示，可以是字符串或异步可迭代对象（用于流式模式） |
| `options` | `ClaudeAgentOptions | None` | 可选配置对象（如果为 None，默认为 `ClaudeAgentOptions()`） |

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

| 参数 | 类型 | 描述 |
| --- | --- | --- |
| `name` | `str` | 工具的唯一标识符 |
| `description` | `str` | 工具功能的人类可读描述 |
| `input_schema` | `type | dict[str, Any]` | 定义工具输入参数的架构（见下文） |

#### 输入架构选项

1. __简单类型映射__（推荐）：

   ```python
   {"text": str, "count": int, "enabled": bool}
   ```

2. __JSON Schema 格式__（用于复杂验证）：

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

创建在 Python 应用程序内运行的进程内 MCP 服务器。

```python
def create_sdk_mcp_server(
    name: str,
    version: str = "1.0.0",
    tools: list[SdkMcpTool[Any]] | None = None
) -> McpSdkServerConfig
```

#### 参数

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `name` | `str` | - | 服务器的唯一标识符 |
| `version` | `str` | `"1.0.0"` | 服务器版本字符串 |
| `tools` | `list[SdkMcpTool[Any]] | None` | `None` | 使用 `@tool` 装饰器创建的工具函数列表 |

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

__在多次交换中维持对话会话。__ 这是 TypeScript SDK 的 `query()` 函数内部工作方式的 Python 等效物 - 它创建一个可以继续对话的客户端对象。

#### 关键特性

- __会话连续性__：在多个 `query()` 调用中维持对话上下文
- __同一对话__：Claude 记住会话中的之前消息
- __中断支持__：可以在 Claude 执行中途停止
- __显式生命周期__：您控制会话何时开始和结束
- __响应驱动流__：可以对响应做出反应并发送后续消息
- __自定义工具和钩子__：支持自定义工具（使用 `@tool` 装饰器创建）和钩子

```python
class ClaudeSDKClient:
    def __init__(self, options: ClaudeAgentOptions | None = None)
    async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None
    async def query(self, prompt: str | AsyncIterable[dict], session_id: str = "default") -> None
    async def receive_messages(self) -> AsyncIterator[Message]
    async def receive_response(self) -> AsyncIterator[Message]
    async def interrupt(self) -> None
    async def disconnect(self) -> None
```

#### 方法

| 方法 | 描述 |
| --- | --- |
| `__init__(options)` | 使用可选配置初始化客户端 |
| `connect(prompt)` | 连接到 Claude，可选初始提示或消息流 |
| `query(prompt, session_id)` | 以流式模式发送新请求 |
| `receive_messages()` | 以异步迭代器形式接收来自 Claude 的所有消息 |
| `receive_response()` | 接收消息直到并包括 ResultMessage |
| `interrupt()` | 发送中断信号（仅在流式模式下工作） |
| `disconnect()` | 从 Claude 断开连接 |

#### 上下文管理器支持

客户端可以用作异步上下文管理器以实现自动连接管理：

```python
async with ClaudeSDKClient() as client:
    await client.query("Hello Claude")
    async for message in client.receive_response():
        print(message)
```

> __重要：__ 在迭代消息时，避免使用 `break` 提前退出，因为这可能导致 asyncio 清理问题。相反，让迭代自然完成或使用标志来跟踪何时找到所需内容。

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

## 另请参阅

- Python SDK 指南 - 教程和示例
- SDK 概述 - 常规 SDK 概念
- TypeScript SDK 参考 - TypeScript SDK 文档
