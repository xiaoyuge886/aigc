# Agent SDK 概述

使用 Claude Code 作为库构建生产级 AI 智能体

---

<Note>
Claude Code SDK 已更名为 Claude Agent SDK。如果您正在从旧版 SDK 迁移，请参阅[迁移指南](/docs/zh-CN/agent-sdk/migration-guide)。
</Note>

构建能够自主读取文件、运行命令、搜索网页、编辑代码等的 AI 智能体。Agent SDK 为您提供与 Claude Code 相同的工具、智能体循环和上下文管理，可在 Python 和 TypeScript 中编程使用。

<CodeGroup>
```python Python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find and fix the bug in auth.py",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"])
    ):
        print(message)  # Claude reads the file, finds the bug, edits it

asyncio.run(main())
```

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Find and fix the bug in auth.py",
  options: { allowedTools: ["Read", "Edit", "Bash"] }
})) {
  console.log(message);  // Claude reads the file, finds the bug, edits it
}
```
</CodeGroup>

Agent SDK 包含用于读取文件、运行命令和编辑代码的内置工具，因此您的智能体无需您实现工具执行即可立即开始工作。深入快速入门或探索使用 SDK 构建的真实智能体：

<CardGroup cols={2}>
  <Card title="快速入门" icon="play" href="/docs/zh-CN/agent-sdk/quickstart">
    几分钟内构建一个修复 bug 的智能体
  </Card>
  <Card title="示例智能体" icon="star" href="https://github.com/anthropics/claude-agent-sdk-demos">
    邮件助手、研究智能体等
  </Card>
</CardGroup>

## 开始使用

<Steps>
  <Step title="安装 SDK">
    <Tabs>
      <Tab title="TypeScript">
        ```bash
        npm install @anthropic-ai/claude-agent-sdk
        ```
      </Tab>
      <Tab title="Python">
        ```bash
        pip install claude-agent-sdk
        ```
      </Tab>
    </Tabs>
  </Step>
  <Step title="设置 API 密钥">
    从 [Console](https://platform.claude.com/) 获取 API 密钥，然后将其设置为环境变量：

    ```bash
    export ANTHROPIC_API_KEY=your-api-key
    ```

    SDK 还支持通过第三方 API 提供商进行身份验证：

    - **Amazon Bedrock**：设置 `CLAUDE_CODE_USE_BEDROCK=1` 环境变量并配置 AWS 凭证
    - **Google Vertex AI**：设置 `CLAUDE_CODE_USE_VERTEX=1` 环境变量并配置 Google Cloud 凭证
    - **Microsoft Azure**：设置 `CLAUDE_CODE_USE_FOUNDRY=1` 环境变量并配置 Azure 凭证

    有关详细信息，请参阅 [Bedrock](https://code.claude.com/docs/en/amazon-bedrock)、[Vertex AI](https://code.claude.com/docs/en/google-vertex-ai) 或 [Azure AI Foundry](https://code.claude.com/docs/en/azure-ai-foundry) 的设置指南。

    <Note>
    除非事先获得批准，Anthropic 不允许第三方开发者为其产品（包括基于 Claude Agent SDK 构建的智能体）提供 claude.ai 登录或速率限制。请改用本文档中描述的 API 密钥身份验证方法。
    </Note>
  </Step>
  <Step title="运行您的第一个智能体">
    此示例创建一个使用内置工具列出当前目录中文件的智能体。

    <CodeGroup>
    ```python Python
    import asyncio
    from claude_agent_sdk import query, ClaudeAgentOptions

    async def main():
        async for message in query(
            prompt="What files are in this directory?",
            options=ClaudeAgentOptions(allowed_tools=["Bash", "Glob"])
        ):
            if hasattr(message, "result"):
                print(message.result)

    asyncio.run(main())
    ```

    ```typescript TypeScript
    import { query } from "@anthropic-ai/claude-agent-sdk";

    for await (const message of query({
      prompt: "What files are in this directory?",
      options: { allowedTools: ["Bash", "Glob"] },
    })) {
      if ("result" in message) console.log(message.result);
    }
    ```
    </CodeGroup>
  </Step>
</Steps>

**准备好构建了吗？** 按照[快速入门](/docs/zh-CN/agent-sdk/quickstart)创建一个能在几分钟内找到并修复 bug 的智能体。

## 功能

Claude Code 的所有强大功能都可在 SDK 中使用：

<Tabs>
  <Tab title="内置工具">
    您的智能体可以开箱即用地读取文件、运行命令和搜索代码库。主要工具包括：

    | 工具 | 功能 |
    |------|------|
    | **Read** | 读取工作目录中的任何文件 |
    | **Write** | 创建新文件 |
    | **Edit** | 对现有文件进行精确编辑 |
    | **Bash** | 运行终端命令、脚本、git 操作 |
    | **Glob** | 按模式查找文件（`**/*.ts`、`src/**/*.py`） |
    | **Grep** | 使用正则表达式搜索文件内容 |
    | **WebSearch** | 搜索网页获取最新信息 |
    | **WebFetch** | 获取和解析网页内容 |
    | **[AskUserQuestion](/docs/zh-CN/agent-sdk/user-input#handle-clarifying-questions)** | 向用户提出带有多选选项的澄清问题 |

    此示例创建一个在代码库中搜索 TODO 注释的智能体：

    <CodeGroup>
    ```python Python
    import asyncio
    from claude_agent_sdk import query, ClaudeAgentOptions

    async def main():
        async for message in query(
            prompt="Find all TODO comments and create a summary",
            options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"])
        ):
            if hasattr(message, "result"):
                print(message.result)

    asyncio.run(main())
    ```

    ```typescript TypeScript
    import { query } from "@anthropic-ai/claude-agent-sdk";

    for await (const message of query({
      prompt: "Find all TODO comments and create a summary",
      options: { allowedTools: ["Read", "Glob", "Grep"] }
    })) {
      if ("result" in message) console.log(message.result);
    }
    ```
    </CodeGroup>

  </Tab>
  <Tab title="钩子">
    在智能体生命周期的关键节点运行自定义代码。SDK 钩子使用回调函数来验证、记录、阻止或转换智能体行为。

    **可用钩子：** `PreToolUse`、`PostToolUse`、`Stop`、`SessionStart`、`SessionEnd`、`UserPromptSubmit` 等。

    此示例将所有文件更改记录到审计文件中：

    <CodeGroup>
    ```python Python
    import asyncio
    from datetime import datetime
    from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher

    async def log_file_change(input_data, tool_use_id, context):
        file_path = input_data.get('tool_input', {}).get('file_path', 'unknown')
        with open('./audit.log', 'a') as f:
            f.write(f"{datetime.now()}: modified {file_path}\n")
        return {}

    async def main():
        async for message in query(
            prompt="Refactor utils.py to improve readability",
            options=ClaudeAgentOptions(
                permission_mode="acceptEdits",
                hooks={
                    "PostToolUse": [HookMatcher(matcher="Edit|Write", hooks=[log_file_change])]
                }
            )
        ):
            if hasattr(message, "result"):
                print(message.result)

    asyncio.run(main())
    ```

    ```typescript TypeScript
    import { query, HookCallback } from "@anthropic-ai/claude-agent-sdk";
    import { appendFileSync } from "fs";

    const logFileChange: HookCallback = async (input) => {
      const filePath = (input as any).tool_input?.file_path ?? "unknown";
      appendFileSync("./audit.log", `${new Date().toISOString()}: modified ${filePath}\n`);
      return {};
    };

    for await (const message of query({
      prompt: "Refactor utils.py to improve readability",
      options: {
        permissionMode: "acceptEdits",
        hooks: {
          PostToolUse: [{ matcher: "Edit|Write", hooks: [logFileChange] }]
        }
      }
    })) {
      if ("result" in message) console.log(message.result);
    }
    ```
    </CodeGroup>

    [了解更多关于钩子的信息 →](/docs/zh-CN/agent-sdk/hooks)
  </Tab>
  <Tab title="子智能体">
    生成专门的智能体来处理聚焦的子任务。您的主智能体委派工作，子智能体返回结果。

    定义具有专门指令的自定义智能体。在 `allowedTools` 中包含 `Task`，因为子智能体通过 Task 工具调用：

    <CodeGroup>
    ```python Python
    import asyncio
    from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

    async def main():
        async for message in query(
            prompt="Use the code-reviewer agent to review this codebase",
            options=ClaudeAgentOptions(
                allowed_tools=["Read", "Glob", "Grep", "Task"],
                agents={
                    "code-reviewer": AgentDefinition(
                        description="Expert code reviewer for quality and security reviews.",
                        prompt="Analyze code quality and suggest improvements.",
                        tools=["Read", "Glob", "Grep"]
                    )
                }
            )
        ):
            if hasattr(message, "result"):
                print(message.result)

    asyncio.run(main())
    ```

    ```typescript TypeScript
    import { query } from "@anthropic-ai/claude-agent-sdk";

    for await (const message of query({
      prompt: "Use the code-reviewer agent to review this codebase",
      options: {
        allowedTools: ["Read", "Glob", "Grep", "Task"],
        agents: {
          "code-reviewer": {
            description: "Expert code reviewer for quality and security reviews.",
            prompt: "Analyze code quality and suggest improvements.",
            tools: ["Read", "Glob", "Grep"]
          }
        }
      }
    })) {
      if ("result" in message) console.log(message.result);
    }
    ```
    </CodeGroup>

    来自子智能体上下文中的消息包含 `parent_tool_use_id` 字段，让您可以跟踪哪些消息属于哪个子智能体执行。

    [了解更多关于子智能体的信息 →](/docs/zh-CN/agent-sdk/subagents)
  </Tab>
  <Tab title="MCP">
    通过 Model Context Protocol 连接外部系统：数据库、浏览器、API 以及[数百种其他系统](https://github.com/modelcontextprotocol/servers)。

    此示例连接 [Playwright MCP 服务器](https://github.com/microsoft/playwright-mcp)，为您的智能体提供浏览器自动化功能：

    <CodeGroup>
    ```python Python
    import asyncio
    from claude_agent_sdk import query, ClaudeAgentOptions

    async def main():
        async for message in query(
            prompt="Open example.com and describe what you see",
            options=ClaudeAgentOptions(
                mcp_servers={
                    "playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]}
                }
            )
        ):
            if hasattr(message, "result"):
                print(message.result)

    asyncio.run(main())
    ```

    ```typescript TypeScript
    import { query } from "@anthropic-ai/claude-agent-sdk";

    for await (const message of query({
      prompt: "Open example.com and describe what you see",
      options: {
        mcpServers: {
          playwright: { command: "npx", args: ["@playwright/mcp@latest"] }
        }
      }
    })) {
      if ("result" in message) console.log(message.result);
    }
    ```
    </CodeGroup>

    [了解更多关于 MCP 的信息 →](/docs/zh-CN/agent-sdk/mcp)
  </Tab>
  <Tab title="权限">
    精确控制您的智能体可以使用哪些工具。允许安全操作、阻止危险操作，或要求对敏感操作进行审批。

    <Note>
    有关交互式审批提示和 `AskUserQuestion` 工具，请参阅[处理审批和用户输入](/docs/zh-CN/agent-sdk/user-input)。
    </Note>

    此示例创建一个只读智能体，可以分析但不能修改代码：

    <CodeGroup>
    ```python Python
    import asyncio
    from claude_agent_sdk import query, ClaudeAgentOptions

    async def main():
        async for message in query(
            prompt="Review this code for best practices",
            options=ClaudeAgentOptions(
                allowed_tools=["Read", "Glob", "Grep"],
                permission_mode="bypassPermissions"
            )
        ):
            if hasattr(message, "result"):
                print(message.result)

    asyncio.run(main())
    ```

    ```typescript TypeScript
    import { query } from "@anthropic-ai/claude-agent-sdk";

    for await (const message of query({
      prompt: "Review this code for best practices",
      options: {
        allowedTools: ["Read", "Glob", "Grep"],
        permissionMode: "bypassPermissions"
      }
    })) {
      if ("result" in message) console.log(message.result);
    }
    ```
    </CodeGroup>

    [了解更多关于权限的信息 →](/docs/zh-CN/agent-sdk/permissions)
  </Tab>
  <Tab title="会话">
    在多次交互中保持上下文。Claude 会记住已读取的文件、已完成的分析和对话历史。稍后恢复会话，或分叉会话以探索不同的方法。

    此示例从第一次查询中捕获会话 ID，然后恢复以继续使用完整上下文：

    <CodeGroup>
    ```python Python
    import asyncio
    from claude_agent_sdk import query, ClaudeAgentOptions

    async def main():
        session_id = None

        # First query: capture the session ID
        async for message in query(
            prompt="Read the authentication module",
            options=ClaudeAgentOptions(allowed_tools=["Read", "Glob"])
        ):
            if hasattr(message, 'subtype') and message.subtype == 'init':
                session_id = message.session_id

        # Resume with full context from the first query
        async for message in query(
            prompt="Now find all places that call it",  # "it" = auth module
            options=ClaudeAgentOptions(resume=session_id)
        ):
            if hasattr(message, "result"):
                print(message.result)

    asyncio.run(main())
    ```

    ```typescript TypeScript
    import { query } from "@anthropic-ai/claude-agent-sdk";

    let sessionId: string | undefined;

    // First query: capture the session ID
    for await (const message of query({
      prompt: "Read the authentication module",
      options: { allowedTools: ["Read", "Glob"] }
    })) {
      if (message.type === "system" && message.subtype === "init") {
        sessionId = message.session_id;
      }
    }

    // Resume with full context from the first query
    for await (const message of query({
      prompt: "Now find all places that call it",  // "it" = auth module
      options: { resume: sessionId }
    })) {
      if ("result" in message) console.log(message.result);
    }
    ```
    </CodeGroup>

    [了解更多关于会话的信息 →](/docs/zh-CN/agent-sdk/sessions)
  </Tab>
</Tabs>

### Claude Code 功能

SDK 还支持 Claude Code 基于文件系统的配置。要使用这些功能，请在选项中设置 `setting_sources=["project"]`（Python）或 `settingSources: ['project']`（TypeScript）。

| 功能 | 描述 | 位置 |
|------|------|------|
| [技能](/docs/zh-CN/agent-sdk/skills) | 在 Markdown 中定义的专门能力 | `.claude/skills/SKILL.md` |
| [斜杠命令](/docs/zh-CN/agent-sdk/slash-commands) | 用于常见任务的自定义命令 | `.claude/commands/*.md` |
| [记忆](/docs/zh-CN/agent-sdk/modifying-system-prompts) | 项目上下文和指令 | `CLAUDE.md` 或 `.claude/CLAUDE.md` |
| [插件](/docs/zh-CN/agent-sdk/plugins) | 通过自定义命令、智能体和 MCP 服务器进行扩展 | 通过 `plugins` 选项以编程方式配置 |

## 将 Agent SDK 与其他 Claude 工具进行比较

Claude 平台提供了多种使用 Claude 构建的方式。以下是 Agent SDK 的定位：

<Tabs>
  <Tab title="Agent SDK 与 Client SDK">
    [Anthropic Client SDK](/docs/zh-CN/api/client-sdks) 为您提供直接的 API 访问：您发送提示并自行实现工具执行。**Agent SDK** 为您提供带有内置工具执行的 Claude。

    使用 Client SDK，您需要实现工具循环。使用 Agent SDK，Claude 会处理它：

    <CodeGroup>
    ```python Python
    # Client SDK: You implement the tool loop
    response = client.messages.create(...)
    while response.stop_reason == "tool_use":
        result = your_tool_executor(response.tool_use)
        response = client.messages.create(tool_result=result, ...)

    # Agent SDK: Claude handles tools autonomously
    async for message in query(prompt="Fix the bug in auth.py"):
        print(message)
    ```

    ```typescript TypeScript
    // Client SDK: You implement the tool loop
    let response = await client.messages.create({...});
    while (response.stop_reason === "tool_use") {
      const result = yourToolExecutor(response.tool_use);
      response = await client.messages.create({ tool_result: result, ... });
    }

    // Agent SDK: Claude handles tools autonomously
    for await (const message of query({ prompt: "Fix the bug in auth.py" })) {
      console.log(message);
    }
    ```
    </CodeGroup>
  </Tab>
  <Tab title="Agent SDK 与 Claude Code CLI">
    相同的功能，不同的接口：

    | 使用场景 | 最佳选择 |
    |----------|----------|
    | 交互式开发 | CLI |
    | CI/CD 流水线 | SDK |
    | 自定义应用程序 | SDK |
    | 一次性任务 | CLI |
    | 生产自动化 | SDK |

    许多团队同时使用两者：CLI 用于日常开发，SDK 用于生产环境。工作流可以在两者之间直接转换。
  </Tab>
</Tabs>

## 更新日志

查看完整的更新日志，了解 SDK 更新、bug 修复和新功能：

- **TypeScript SDK**：[查看 CHANGELOG.md](https://github.com/anthropics/claude-agent-sdk-typescript/blob/main/CHANGELOG.md)
- **Python SDK**：[查看 CHANGELOG.md](https://github.com/anthropics/claude-agent-sdk-python/blob/main/CHANGELOG.md)

## 报告 bug

如果您在使用 Agent SDK 时遇到 bug 或问题：

- **TypeScript SDK**：[在 GitHub 上报告问题](https://github.com/anthropics/claude-agent-sdk-typescript/issues)
- **Python SDK**：[在 GitHub 上报告问题](https://github.com/anthropics/claude-agent-sdk-python/issues)

## 品牌指南

对于集成 Claude Agent SDK 的合作伙伴，使用 Claude 品牌是可选的。在您的产品中引用 Claude 时：

**允许：**
- "Claude Agent"（下拉菜单中的首选名称）
- "Claude"（当在已标记为"Agents"的菜单中时）
- "{YourAgentName} Powered by Claude"（如果您已有智能体名称）

**不允许：**
- "Claude Code" 或 "Claude Code Agent"
- Claude Code 品牌的 ASCII 艺术或模仿 Claude Code 的视觉元素

您的产品应保持自己的品牌，不应看起来像是 Claude Code 或任何 Anthropic 产品。有关品牌合规性的问题，请联系我们的[销售团队](https://www.anthropic.com/contact-sales)。

## 许可和条款

Claude Agent SDK 的使用受 [Anthropic 商业服务条款](https://www.anthropic.com/legal/commercial-terms)约束，包括当您使用它为您自己的客户和最终用户提供产品和服务时，除非特定组件或依赖项在该组件的 LICENSE 文件中标明受不同许可证约束。

## 后续步骤

<CardGroup cols={2}>
  <Card title="快速入门" icon="play" href="/docs/zh-CN/agent-sdk/quickstart">
    构建一个能在几分钟内找到并修复 bug 的智能体
  </Card>
  <Card title="示例智能体" icon="star" href="https://github.com/anthropics/claude-agent-sdk-demos">
    邮件助手、研究智能体等
  </Card>
  <Card title="TypeScript SDK" icon="code" href="/docs/zh-CN/agent-sdk/typescript">
    完整的 TypeScript API 参考和示例
  </Card>
  <Card title="Python SDK" icon="code" href="/docs/zh-CN/agent-sdk/python">
    完整的 Python API 参考和示例
  </Card>
</CardGroup>