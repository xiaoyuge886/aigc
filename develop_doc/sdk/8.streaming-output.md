# 实时流式传输响应

在文本和工具调用流式传入时，从 Agent SDK 获取实时响应

---

默认情况下，Agent SDK 在 Claude 完成每个响应的生成后，会产出完整的 `AssistantMessage` 对象。要在文本和工具调用生成时接收增量更新，请通过在选项中将 `include_partial_messages`（Python）或 `includePartialMessages`（TypeScript）设置为 `true` 来启用部分消息流式传输。

<Tip>
本页介绍输出流式传输（实时接收 token）。有关输入模式（如何发送消息），请参阅[向代理发送消息](/docs/zh-CN/agent-sdk/streaming-vs-single-mode)。您还可以[通过 CLI 使用 Agent SDK 流式传输响应](https://code.claude.com/docs/en/headless)。
</Tip>

## 启用流式输出

要启用流式传输，请在选项中将 `include_partial_messages`（Python）或 `includePartialMessages`（TypeScript）设置为 `true`。这会使 SDK 在产出通常的 `AssistantMessage` 和 `ResultMessage` 之外，还产出包含原始 API 事件的 `StreamEvent` 消息。

您的代码需要：
1. 检查每条消息的类型，以区分 `StreamEvent` 和其他消息类型
2. 对于 `StreamEvent`，提取 `event` 字段并检查其 `type`
3. 查找 `delta.type` 为 `text_delta` 的 `content_block_delta` 事件，其中包含实际的文本块

下面的示例启用了流式传输，并在文本块到达时打印它们。注意嵌套的类型检查：首先检查 `StreamEvent`，然后检查 `content_block_delta`，最后检查 `text_delta`：

<CodeGroup>

```python Python
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent
import asyncio

async def stream_response():
    options = ClaudeAgentOptions(
        include_partial_messages=True,
        allowed_tools=["Bash", "Read"],
    )

    async for message in query(prompt="List the files in my project", options=options):
        if isinstance(message, StreamEvent):
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    print(delta.get("text", ""), end="", flush=True)

asyncio.run(stream_response())
```

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "List the files in my project",
  options: {
    includePartialMessages: true,
    allowedTools: ["Bash", "Read"],
  }
})) {
  if (message.type === "stream_event") {
    const event = message.event;
    if (event.type === "content_block_delta") {
      if (event.delta.type === "text_delta") {
        process.stdout.write(event.delta.text);
      }
    }
  }
}
```

</CodeGroup>

## StreamEvent 参考

启用部分消息后，您会收到包装在对象中的原始 Claude API 流式事件。该类型在每个 SDK 中有不同的名称：

- **Python**：`StreamEvent`（从 `claude_agent_sdk.types` 导入）
- **TypeScript**：`SDKPartialAssistantMessage`，带有 `type: 'stream_event'`

两者都包含原始 Claude API 事件，而非累积的文本。您需要自行提取和累积文本增量。以下是每种类型的结构：

<CodeGroup>

```python Python
@dataclass
class StreamEvent:
    uuid: str                      # 此事件的唯一标识符
    session_id: str                # 会话标识符
    event: dict[str, Any]          # 原始 Claude API 流式事件
    parent_tool_use_id: str | None # 如果来自子代理，则为父工具 ID
```

```typescript TypeScript
type SDKPartialAssistantMessage = {
  type: 'stream_event';
  event: RawMessageStreamEvent;    // 来自 Anthropic SDK
  parent_tool_use_id: string | null;
  uuid: UUID;
  session_id: string;
}
```

</CodeGroup>

`event` 字段包含来自 [Claude API](/docs/zh-CN/build-with-claude/streaming#event-types) 的原始流式事件。常见的事件类型包括：

| 事件类型 | 描述 |
|:-----------|:------------|
| `message_start` | 新消息开始 |
| `content_block_start` | 新内容块开始（文本或工具使用） |
| `content_block_delta` | 内容的增量更新 |
| `content_block_stop` | 内容块结束 |
| `message_delta` | 消息级别的更新（停止原因、用量） |
| `message_stop` | 消息结束 |

## 消息流程

启用部分消息后，您将按以下顺序接收消息：

```
StreamEvent (message_start)
StreamEvent (content_block_start) - 文本块
StreamEvent (content_block_delta) - 文本块...
StreamEvent (content_block_stop)
StreamEvent (content_block_start) - tool_use 块
StreamEvent (content_block_delta) - 工具输入块...
StreamEvent (content_block_stop)
StreamEvent (message_delta)
StreamEvent (message_stop)
AssistantMessage - 包含所有内容的完整消息
... 工具执行 ...
... 下一轮的更多流式事件 ...
ResultMessage - 最终结果
```

未启用部分消息时（Python 中的 `include_partial_messages`，TypeScript 中的 `includePartialMessages`），您会收到除 `StreamEvent` 之外的所有消息类型。常见类型包括 `SystemMessage`（会话初始化）、`AssistantMessage`（完整响应）、`ResultMessage`（最终结果）和 `CompactBoundaryMessage`（指示对话历史已被压缩）。

## 流式传输文本响应

要在文本生成时显示文本，请查找 `delta.type` 为 `text_delta` 的 `content_block_delta` 事件。这些事件包含增量文本块。下面的示例在每个块到达时打印它：

<CodeGroup>

```python Python
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent
import asyncio

async def stream_text():
    options = ClaudeAgentOptions(include_partial_messages=True)

    async for message in query(prompt="Explain how databases work", options=options):
        if isinstance(message, StreamEvent):
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    # 在每个文本块到达时打印
                    print(delta.get("text", ""), end="", flush=True)

    print()  # 最后的换行

asyncio.run(stream_text())
```

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Explain how databases work",
  options: { includePartialMessages: true }
})) {
  if (message.type === "stream_event") {
    const event = message.event;
    if (event.type === "content_block_delta" && event.delta.type === "text_delta") {
      process.stdout.write(event.delta.text);
    }
  }
}

console.log(); // 最后的换行
```

</CodeGroup>

## 流式传输工具调用

工具调用也会增量流式传输。您可以跟踪工具何时开始、在其输入生成时接收输入，以及查看它们何时完成。下面的示例跟踪当前正在调用的工具，并在 JSON 输入流式传入时累积它。它使用三种事件类型：

- `content_block_start`：工具开始
- `content_block_delta` 带有 `input_json_delta`：输入块到达
- `content_block_stop`：工具调用完成

<CodeGroup>

```python Python
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import StreamEvent
import asyncio

async def stream_tool_calls():
    options = ClaudeAgentOptions(
        include_partial_messages=True,
        allowed_tools=["Read", "Bash"],
    )

    # 跟踪当前工具并累积其输入 JSON
    current_tool = None
    tool_input = ""

    async for message in query(prompt="Read the README.md file", options=options):
        if isinstance(message, StreamEvent):
            event = message.event
            event_type = event.get("type")

            if event_type == "content_block_start":
                # 新的工具调用正在开始
                content_block = event.get("content_block", {})
                if content_block.get("type") == "tool_use":
                    current_tool = content_block.get("name")
                    tool_input = ""
                    print(f"Starting tool: {current_tool}")

            elif event_type == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "input_json_delta":
                    # 在 JSON 输入流式传入时累积
                    chunk = delta.get("partial_json", "")
                    tool_input += chunk
                    print(f"  Input chunk: {chunk}")

            elif event_type == "content_block_stop":
                # 工具调用完成 - 显示最终输入
                if current_tool:
                    print(f"Tool {current_tool} called with: {tool_input}")
                    current_tool = None

asyncio.run(stream_tool_calls())
```

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 跟踪当前工具并累积其输入 JSON
let currentTool: string | null = null;
let toolInput = "";

for await (const message of query({
  prompt: "Read the README.md file",
  options: {
    includePartialMessages: true,
    allowedTools: ["Read", "Bash"],
  }
})) {
  if (message.type === "stream_event") {
    const event = message.event;

    if (event.type === "content_block_start") {
      // 新的工具调用正在开始
      if (event.content_block.type === "tool_use") {
        currentTool = event.content_block.name;
        toolInput = "";
        console.log(`Starting tool: ${currentTool}`);
      }
    } else if (event.type === "content_block_delta") {
      if (event.delta.type === "input_json_delta") {
        // 在 JSON 输入流式传入时累积
        const chunk = event.delta.partial_json;
        toolInput += chunk;
        console.log(`  Input chunk: ${chunk}`);
      }
    } else if (event.type === "content_block_stop") {
      // 工具调用完成 - 显示最终输入
      if (currentTool) {
        console.log(`Tool ${currentTool} called with: ${toolInput}`);
        currentTool = null;
      }
    }
  }
}
```

</CodeGroup>

## 构建流式 UI

此示例将文本和工具流式传输组合成一个统一的 UI。它跟踪代理当前是否正在执行工具（使用 `in_tool` 标志），以在工具运行时显示状态指示器，如 `[Using Read...]`。不在工具中时文本正常流式传输，工具完成时触发"done"消息。此模式适用于需要在多步骤代理任务期间显示进度的聊天界面。

<CodeGroup>

```python Python
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
from claude_agent_sdk.types import StreamEvent
import asyncio
import sys

async def streaming_ui():
    options = ClaudeAgentOptions(
        include_partial_messages=True,
        allowed_tools=["Read", "Bash", "Grep"],
    )

    # 跟踪我们当前是否在工具调用中
    in_tool = False

    async for message in query(
        prompt="Find all TODO comments in the codebase",
        options=options
    ):
        if isinstance(message, StreamEvent):
            event = message.event
            event_type = event.get("type")

            if event_type == "content_block_start":
                content_block = event.get("content_block", {})
                if content_block.get("type") == "tool_use":
                    # 工具调用正在开始 - 显示状态指示器
                    tool_name = content_block.get("name")
                    print(f"\n[Using {tool_name}...]", end="", flush=True)
                    in_tool = True

            elif event_type == "content_block_delta":
                delta = event.get("delta", {})
                # 仅在不执行工具时流式传输文本
                if delta.get("type") == "text_delta" and not in_tool:
                    sys.stdout.write(delta.get("text", ""))
                    sys.stdout.flush()

            elif event_type == "content_block_stop":
                if in_tool:
                    # 工具调用完成
                    print(" done", flush=True)
                    in_tool = False

        elif isinstance(message, ResultMessage):
            # 代理完成所有工作
            print(f"\n\n--- Complete ---")

asyncio.run(streaming_ui())
```

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 跟踪我们当前是否在工具调用中
let inTool = false;

for await (const message of query({
  prompt: "Find all TODO comments in the codebase",
  options: {
    includePartialMessages: true,
    allowedTools: ["Read", "Bash", "Grep"],
  }
})) {
  if (message.type === "stream_event") {
    const event = message.event;

    if (event.type === "content_block_start") {
      if (event.content_block.type === "tool_use") {
        // 工具调用正在开始 - 显示状态指示器
        process.stdout.write(`\n[Using ${event.content_block.name}...]`);
        inTool = true;
      }
    } else if (event.type === "content_block_delta") {
      // 仅在不执行工具时流式传输文本
      if (event.delta.type === "text_delta" && !inTool) {
        process.stdout.write(event.delta.text);
      }
    } else if (event.type === "content_block_stop") {
      if (inTool) {
        // 工具调用完成
        console.log(" done");
        inTool = false;
      }
    }
  } else if (message.type === "result") {
    // 代理完成所有工作
    console.log("\n\n--- Complete ---");
  }
}
```

</CodeGroup>

## 已知限制

某些 SDK 功能与流式传输不兼容：

- **扩展思考**：当您显式设置 `max_thinking_tokens`（Python）或 `maxThinkingTokens`（TypeScript）时，不会发出 `StreamEvent` 消息。您只会在每轮结束后收到完整消息。请注意，SDK 中默认禁用思考功能，因此除非您启用它，否则流式传输可以正常工作。
- **结构化输出**：JSON 结果仅出现在最终的 `ResultMessage.structured_output` 中，而不是作为流式增量。详情请参阅[结构化输出](/docs/zh-CN/agent-sdk/structured-outputs)。

## 后续步骤

现在您可以实时流式传输文本和工具调用了，请探索以下相关主题：

- [交互式与一次性查询](/docs/zh-CN/agent-sdk/streaming-vs-single-mode)：为您的用例选择输入模式
- [结构化输出](/docs/zh-CN/agent-sdk/structured-outputs)：从代理获取类型化的 JSON 响应
- [权限](/docs/zh-CN/agent-sdk/permissions)：控制代理可以使用哪些工具