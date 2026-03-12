# 快速入门

使用 Python 或 TypeScript Agent SDK 开始构建自主工作的 AI 智能体

---

使用 Agent SDK 构建一个 AI 智能体，它可以读取您的代码、查找错误并修复它们，全程无需人工干预。

**您将完成的内容：**
1. 使用 Agent SDK 设置项目
2. 创建一个包含一些有错误代码的文件
3. 运行一个自动查找并修复错误的智能体

## 前提条件

- **Node.js 18+** 或 **Python 3.10+**
- 一个 **Anthropic 账户**（[在此注册](https://platform.claude.com/)）

## 设置

<Steps>
  <Step title="创建项目文件夹">
    为此快速入门创建一个新目录：

    ```bash
    mkdir my-agent && cd my-agent
    ```

    对于您自己的项目，您可以从任何文件夹运行 SDK；默认情况下，它可以访问该目录及其子目录中的文件。
  </Step>

  <Step title="安装 SDK">
    为您的语言安装 Agent SDK 包：

    <Tabs>
      <Tab title="TypeScript">
        ```bash
        npm install @anthropic-ai/claude-agent-sdk
        ```
      </Tab>
      <Tab title="Python (uv)">
        [uv Python 包管理器](https://docs.astral.sh/uv/) 是一个快速的 Python 包管理器，可以自动处理虚拟环境：
        ```bash
        uv init && uv add claude-agent-sdk
        ```
      </Tab>
      <Tab title="Python (pip)">
        首先创建虚拟环境，然后安装：
        ```bash
        python3 -m venv .venv && source .venv/bin/activate
        pip3 install claude-agent-sdk
        ```
      </Tab>
    </Tabs>
  </Step>

  <Step title="设置 API 密钥">
    从 [Claude 控制台](https://platform.claude.com/) 获取 API 密钥，然后在项目目录中创建 `.env` 文件：

    ```bash
    ANTHROPIC_API_KEY=your-api-key
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
</Steps>

## 创建一个有错误的文件

本快速入门将引导您构建一个能够查找和修复代码错误的智能体。首先，您需要一个包含一些故意错误的文件供智能体修复。在 `my-agent` 目录中创建 `utils.py` 并粘贴以下代码：

```python
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

def get_user_name(user):
    return user["name"].upper()
```

这段代码有两个错误：
1. `calculate_average([])` 会因除以零而崩溃
2. `get_user_name(None)` 会因 TypeError 而崩溃

## 构建一个查找和修复错误的智能体

如果您使用 Python SDK，请创建 `agent.py`；如果使用 TypeScript，请创建 `agent.ts`：

<CodeGroup>
```python Python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def main():
    # 智能体循环：在 Claude 工作时流式传输消息
    async for message in query(
        prompt="Review utils.py for bugs that would cause crashes. Fix any issues you find.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Glob"],  # Claude 可以使用的工具
            permission_mode="acceptEdits"            # 自动批准文件编辑
        )
    ):
        # 打印人类可读的输出
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)              # Claude 的推理
                elif hasattr(block, "name"):
                    print(f"Tool: {block.name}")   # 正在调用的工具
        elif isinstance(message, ResultMessage):
            print(f"Done: {message.subtype}")      # 最终结果

asyncio.run(main())
```

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 智能体循环：在 Claude 工作时流式传输消息
for await (const message of query({
  prompt: "Review utils.py for bugs that would cause crashes. Fix any issues you find.",
  options: {
    allowedTools: ["Read", "Edit", "Glob"],  // Claude 可以使用的工具
    permissionMode: "acceptEdits"            // 自动批准文件编辑
  }
})) {
  // 打印人类可读的输出
  if (message.type === "assistant" && message.message?.content) {
    for (const block of message.message.content) {
      if ("text" in block) {
        console.log(block.text);             // Claude 的推理
      } else if ("name" in block) {
        console.log(`Tool: ${block.name}`);  // 正在调用的工具
      }
    }
  } else if (message.type === "result") {
    console.log(`Done: ${message.subtype}`); // 最终结果
  }
}
```
</CodeGroup>

这段代码有三个主要部分：

1. **`query`**：创建智能体循环的主入口点。它返回一个异步迭代器，因此您使用 `async for` 在 Claude 工作时流式传输消息。请参阅 [Python](/docs/zh-CN/agent-sdk/python#query) 或 [TypeScript](/docs/zh-CN/agent-sdk/typescript#query) SDK 参考中的完整 API。

2. **`prompt`**：您希望 Claude 做什么。Claude 会根据任务确定使用哪些工具。

3. **`options`**：智能体的配置。此示例使用 `allowedTools` 将 Claude 限制为 `Read`、`Edit` 和 `Glob`，并使用 `permissionMode: "acceptEdits"` 自动批准文件更改。其他选项包括 `systemPrompt`、`mcpServers` 等。查看 [Python](/docs/zh-CN/agent-sdk/python#claudeagentoptions) 或 [TypeScript](/docs/zh-CN/agent-sdk/typescript#claudeagentoptions) 的所有选项。

`async for` 循环在 Claude 思考、调用工具、观察结果并决定下一步操作时持续运行。每次迭代都会产生一条消息：Claude 的推理、工具调用、工具结果或最终结果。SDK 处理编排（工具执行、上下文管理、重试），因此您只需消费流即可。当 Claude 完成任务或遇到错误时，循环结束。

循环内的消息处理会过滤出人类可读的输出。如果不进行过滤，您会看到原始消息对象，包括系统初始化和内部状态，这对调试有用，但在其他情况下会产生噪音。

<Note>
此示例使用流式传输来实时显示进度。如果您不需要实时输出（例如，用于后台作业或 CI 管道），您可以一次性收集所有消息。有关详细信息，请参阅[流式传输与单轮模式](/docs/zh-CN/agent-sdk/streaming-vs-single-mode)。
</Note>

### 运行您的智能体

您的智能体已准备就绪。使用以下命令运行它：

<Tabs>
  <Tab title="Python">
    ```bash
    python3 agent.py
    ```
  </Tab>
  <Tab title="TypeScript">
    ```bash
    npx tsx agent.ts
    ```
  </Tab>
</Tabs>

运行后，检查 `utils.py`。您会看到处理空列表和空用户的防御性代码。您的智能体自主完成了以下操作：

1. **读取** `utils.py` 以理解代码
2. **分析** 逻辑并识别会导致崩溃的边界情况
3. **编辑** 文件以添加适当的错误处理

这就是 Agent SDK 的不同之处：Claude 直接执行工具，而不是要求您来实现它们。

<Note>
如果您看到"API key not found"，请确保您已在 `.env` 文件或 shell 环境中设置了 `ANTHROPIC_API_KEY` 环境变量。有关更多帮助，请参阅[完整故障排除指南](https://code.claude.com/docs/en/troubleshooting)。
</Note>

### 尝试其他提示

现在您的智能体已设置好，尝试一些不同的提示：

- `"Add docstrings to all functions in utils.py"`
- `"Add type hints to all functions in utils.py"`
- `"Create a README.md documenting the functions in utils.py"`

### 自定义您的智能体

您可以通过更改选项来修改智能体的行为。以下是一些示例：

**添加网络搜索功能：**

<CodeGroup>
```python Python
options=ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob", "WebSearch"],
    permission_mode="acceptEdits"
)
```

```typescript TypeScript
options: {
  allowedTools: ["Read", "Edit", "Glob", "WebSearch"],
  permissionMode: "acceptEdits"
}
```
</CodeGroup>

**为 Claude 提供自定义系统提示：**

<CodeGroup>
```python Python
options=ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob"],
    permission_mode="acceptEdits",
    system_prompt="You are a senior Python developer. Always follow PEP 8 style guidelines."
)
```

```typescript TypeScript
options: {
  allowedTools: ["Read", "Edit", "Glob"],
  permissionMode: "acceptEdits",
  systemPrompt: "You are a senior Python developer. Always follow PEP 8 style guidelines."
}
```
</CodeGroup>

**在终端中运行命令：**

<CodeGroup>
```python Python
options=ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob", "Bash"],
    permission_mode="acceptEdits"
)
```

```typescript TypeScript
options: {
  allowedTools: ["Read", "Edit", "Glob", "Bash"],
  permissionMode: "acceptEdits"
}
```
</CodeGroup>

启用 `Bash` 后，尝试：`"Write unit tests for utils.py, run them, and fix any failures"`

## 关键概念

**工具** 控制您的智能体可以做什么：

| 工具 | 智能体可以做什么 |
|-------|----------------------|
| `Read`、`Glob`、`Grep` | 只读分析 |
| `Read`、`Edit`、`Glob` | 分析和修改代码 |
| `Read`、`Edit`、`Bash`、`Glob`、`Grep` | 完全自动化 |

**权限模式** 控制您需要多少人工监督：

| 模式 | 行为 | 使用场景 |
|------|----------|----------|
| `acceptEdits` | 自动批准文件编辑，其他操作需要询问 | 受信任的开发工作流 |
| `bypassPermissions` | 无需提示即可运行 | CI/CD 管道、自动化 |
| `default` | 需要 `canUseTool` 回调来处理审批 | 自定义审批流程 |

上面的示例使用 `acceptEdits` 模式，该模式自动批准文件操作，使智能体可以在没有交互式提示的情况下运行。如果您想提示用户进行审批，请使用 `default` 模式并提供一个收集用户输入的 [`canUseTool` 回调](/docs/zh-CN/agent-sdk/user-input)。如需更多控制，请参阅[权限](/docs/zh-CN/agent-sdk/permissions)。

## 后续步骤

现在您已经创建了第一个智能体，了解如何扩展其功能并根据您的用例进行定制：

- **[权限](/docs/zh-CN/agent-sdk/permissions)**：控制您的智能体可以做什么以及何时需要审批
- **[钩子](/docs/zh-CN/agent-sdk/hooks)**：在工具调用之前或之后运行自定义代码
- **[会话](/docs/zh-CN/agent-sdk/sessions)**：构建保持上下文的多轮智能体
- **[MCP 服务器](/docs/zh-CN/agent-sdk/mcp)**：连接到数据库、浏览器、API 和其他外部系统
- **[托管](/docs/zh-CN/agent-sdk/hosting)**：将智能体部署到 Docker、云和 CI/CD
- **[示例智能体](https://github.com/anthropics/claude-agent-sdk-demos)**：查看完整示例：邮件助手、研究智能体等