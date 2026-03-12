# SDK 中的插件

通过 Agent SDK 加载自定义插件，使用命令、代理、技能和钩子来扩展 Claude Code

---

插件允许您使用可在项目间共享的自定义功能来扩展 Claude Code。通过 Agent SDK，您可以以编程方式从本地目录加载插件，以便向代理会话添加自定义斜杠命令、代理、技能、钩子和 MCP 服务器。

## 什么是插件？

插件是 Claude Code 扩展的包，可以包括：
- **命令**：自定义斜杠命令
- **代理**：用于特定任务的专门子代理
- **技能**：Claude 自主使用的模型调用功能
- **钩子**：响应工具使用和其他事件的事件处理程序
- **MCP 服务器**：通过模型上下文协议的外部工具集成

有关插件结构和如何创建插件的完整信息，请参阅[插件](https://code.claude.com/docs/plugins)。

## 加载插件

通过在选项配置中提供本地文件系统路径来加载插件。SDK 支持从不同位置加载多个插件。

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Hello",
  options: {
    plugins: [
      { type: "local", path: "./my-plugin" },
      { type: "local", path: "/absolute/path/to/another-plugin" }
    ]
  }
})) {
  // Plugin commands, agents, and other features are now available
}
```

```python Python
import asyncio
from claude_agent_sdk import query

async def main():
    async for message in query(
        prompt="Hello",
        options={
            "plugins": [
                {"type": "local", "path": "./my-plugin"},
                {"type": "local", "path": "/absolute/path/to/another-plugin"}
            ]
        }
    ):
        # Plugin commands, agents, and other features are now available
        pass

asyncio.run(main())
```

</CodeGroup>

### 路径规范

插件路径可以是：
- **相对路径**：相对于您当前工作目录解析（例如，`"./plugins/my-plugin"`）
- **绝对路径**：完整文件系统路径（例如，`"/home/user/plugins/my-plugin"`）

<Note>
路径应指向插件的根目录（包含 `.claude-plugin/plugin.json` 的目录）。
</Note>

## 验证插件安装

当插件成功加载时，它们会出现在系统初始化消息中。您可以验证您的插件是否可用：

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Hello",
  options: {
    plugins: [{ type: "local", path: "./my-plugin" }]
  }
})) {
  if (message.type === "system" && message.subtype === "init") {
    // Check loaded plugins
    console.log("Plugins:", message.plugins);
    // Example: [{ name: "my-plugin", path: "./my-plugin" }]

    // Check available commands from plugins
    console.log("Commands:", message.slash_commands);
    // Example: ["/help", "/compact", "my-plugin:custom-command"]
  }
}
```

```python Python
import asyncio
from claude_agent_sdk import query

async def main():
    async for message in query(
        prompt="Hello",
        options={"plugins": [{"type": "local", "path": "./my-plugin"}]}
    ):
        if message.type == "system" and message.subtype == "init":
            # Check loaded plugins
            print("Plugins:", message.data.get("plugins"))
            # Example: [{"name": "my-plugin", "path": "./my-plugin"}]

            # Check available commands from plugins
            print("Commands:", message.data.get("slash_commands"))
            # Example: ["/help", "/compact", "my-plugin:custom-command"]

asyncio.run(main())
```

</CodeGroup>

## 使用插件命令

来自插件的命令会自动使用插件名称进行命名空间处理，以避免冲突。格式为 `plugin-name:command-name`。

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Load a plugin with a custom /greet command
for await (const message of query({
  prompt: "/my-plugin:greet",  // Use plugin command with namespace
  options: {
    plugins: [{ type: "local", path: "./my-plugin" }]
  }
})) {
  // Claude executes the custom greeting command from the plugin
  if (message.type === "assistant") {
    console.log(message.content);
  }
}
```

```python Python
import asyncio
from claude_agent_sdk import query, AssistantMessage, TextBlock

async def main():
    # Load a plugin with a custom /greet command
    async for message in query(
        prompt="/demo-plugin:greet",  # Use plugin command with namespace
        options={"plugins": [{"type": "local", "path": "./plugins/demo-plugin"}]}
    ):
        # Claude executes the custom greeting command from the plugin
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")

asyncio.run(main())
```

</CodeGroup>

<Note>
如果您通过 CLI 安装了插件（例如，`/plugin install my-plugin@marketplace`），您仍然可以通过提供其安装路径在 SDK 中使用它。检查 `~/.claude/plugins/` 以查找 CLI 安装的插件。
</Note>

## 完整示例

以下是演示插件加载和使用的完整示例：

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";
import * as path from "path";

async function runWithPlugin() {
  const pluginPath = path.join(__dirname, "plugins", "my-plugin");

  console.log("Loading plugin from:", pluginPath);

  for await (const message of query({
    prompt: "What custom commands do you have available?",
    options: {
      plugins: [
        { type: "local", path: pluginPath }
      ],
      maxTurns: 3
    }
  })) {
    if (message.type === "system" && message.subtype === "init") {
      console.log("Loaded plugins:", message.plugins);
      console.log("Available commands:", message.slash_commands);
    }

    if (message.type === "assistant") {
      console.log("Assistant:", message.content);
    }
  }
}

runWithPlugin().catch(console.error);
```

```python Python
#!/usr/bin/env python3
"""Example demonstrating how to use plugins with the Agent SDK."""

from pathlib import Path
import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)


async def run_with_plugin():
    """Example using a custom plugin."""
    plugin_path = Path(__file__).parent / "plugins" / "demo-plugin"

    print(f"Loading plugin from: {plugin_path}")

    options = ClaudeAgentOptions(
        plugins=[
            {"type": "local", "path": str(plugin_path)}
        ],
        max_turns=3,
    )

    async for message in query(
        prompt="What custom commands do you have available?",
        options=options
    ):
        if message.type == "system" and message.subtype == "init":
            print(f"Loaded plugins: {message.data.get('plugins')}")
            print(f"Available commands: {message.data.get('slash_commands')}")

        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Assistant: {block.text}")


if __name__ == "__main__":
    anyio.run(run_with_plugin)
```

</CodeGroup>

## 插件结构参考

插件目录必须包含 `.claude-plugin/plugin.json` 清单文件。它可以选择性地包括：

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Required: plugin manifest
├── commands/                 # Custom slash commands
│   └── custom-cmd.md
├── agents/                   # Custom agents
│   └── specialist.md
├── skills/                   # Agent Skills
│   └── my-skill/
│       └── SKILL.md
├── hooks/                    # Event handlers
│   └── hooks.json
└── .mcp.json                # MCP server definitions
```

有关创建插件的详细信息，请参阅：
- [插件](https://code.claude.com/docs/plugins) - 完整的插件开发指南
- [插件参考](https://code.claude.com/docs/plugins-reference) - 技术规范和架构

## 常见用例

### 开发和测试

在开发期间加载插件，无需全局安装：

```typescript
plugins: [
  { type: "local", path: "./dev-plugins/my-plugin" }
]
```

### 项目特定的扩展

在您的项目存储库中包含插件以实现团队范围的一致性：

```typescript
plugins: [
  { type: "local", path: "./project-plugins/team-workflows" }
]
```

### 多个插件源

组合来自不同位置的插件：

```typescript
plugins: [
  { type: "local", path: "./local-plugin" },
  { type: "local", path: "~/.claude/custom-plugins/shared-plugin" }
]
```

## 故障排除

### 插件未加载

如果您的插件未出现在初始化消息中：

1. **检查路径**：确保路径指向插件根目录（包含 `.claude-plugin/`）
2. **验证 plugin.json**：确保您的清单文件具有有效的 JSON 语法
3. **检查文件权限**：确保插件目录可读

### 命令不可用

如果插件命令不起作用：

1. **使用命名空间**：插件命令需要 `plugin-name:command-name` 格式
2. **检查初始化消息**：验证命令是否以正确的命名空间出现在 `slash_commands` 中
3. **验证命令文件**：确保命令 markdown 文件位于 `commands/` 目录中

### 路径解析问题

如果相对路径不起作用：

1. **检查工作目录**：相对路径从您当前的工作目录解析
2. **使用绝对路径**：为了可靠性，请考虑使用绝对路径
3. **规范化路径**：使用路径实用程序正确构造路径

## 另请参阅

- [插件](https://code.claude.com/docs/plugins) - 完整的插件开发指南
- [插件参考](https://code.claude.com/docs/plugins-reference) - 技术规范
- [斜杠命令](/docs/zh-CN/agent-sdk/slash-commands) - 在 SDK 中使用斜杠命令
- [子代理](/docs/zh-CN/agent-sdk/subagents) - 使用专门的代理
- [技能](/docs/zh-CN/agent-sdk/skills) - 使用 Agent Skills