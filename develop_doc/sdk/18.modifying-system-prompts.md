# 修改系统提示

了解如何通过三种方法自定义 Claude 的行为：输出样式、带 append 的 systemPrompt 以及自定义系统提示。

---

系统提示定义了 Claude 的行为、能力和响应风格。Claude Agent SDK 提供了三种自定义系统提示的方式：使用输出样式（持久化的基于文件的配置）、追加到 Claude Code 的提示，或使用完全自定义的提示。

## 理解系统提示

系统提示是塑造 Claude 在整个对话过程中行为方式的初始指令集。

<Note>
**默认行为：** Agent SDK 默认使用**最小化系统提示**。它仅包含基本的工具指令，但省略了 Claude Code 的编码指南、响应风格和项目上下文。要包含完整的 Claude Code 系统提示，请在 TypeScript 中指定 `systemPrompt: { preset: "claude_code" }`，或在 Python 中指定 `system_prompt={"type": "preset", "preset": "claude_code"}`。
</Note>

Claude Code 的系统提示包括：

- 工具使用说明和可用工具
- 代码风格和格式指南
- 响应语气和详细程度设置
- 安全和安保指令
- 关于当前工作目录和环境的上下文

## 修改方法

### 方法 1：CLAUDE.md 文件（项目级指令）

CLAUDE.md 文件提供项目特定的上下文和指令，当 Agent SDK 在某个目录中运行时会自动读取这些文件。它们充当项目的持久化"记忆"。

#### CLAUDE.md 如何与 SDK 配合工作

**位置和发现：**

- **项目级：** 工作目录中的 `CLAUDE.md` 或 `.claude/CLAUDE.md`
- **用户级：** `~/.claude/CLAUDE.md` 用于所有项目的全局指令

**重要：** SDK 仅在您显式配置 `settingSources`（TypeScript）或 `setting_sources`（Python）时才会读取 CLAUDE.md 文件：

- 包含 `'project'` 以加载项目级 CLAUDE.md
- 包含 `'user'` 以加载用户级 CLAUDE.md（`~/.claude/CLAUDE.md`）

`claude_code` 系统提示预设不会自动加载 CLAUDE.md——您还必须指定设置来源。

**内容格式：**
CLAUDE.md 文件使用纯 markdown 格式，可以包含：

- 编码指南和标准
- 项目特定上下文
- 常用命令或工作流程
- API 约定
- 测试要求

#### CLAUDE.md 示例

```markdown
# Project Guidelines

## Code Style

- Use TypeScript strict mode
- Prefer functional components in React
- Always include JSDoc comments for public APIs

## Testing

- Run `npm test` before committing
- Maintain >80% code coverage
- Use jest for unit tests, playwright for E2E

## Commands

- Build: `npm run build`
- Dev server: `npm run dev`
- Type check: `npm run typecheck`
```

#### 在 SDK 中使用 CLAUDE.md

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 重要：您必须指定 settingSources 来加载 CLAUDE.md
// 仅使用 claude_code 预设不会加载 CLAUDE.md 文件
const messages = [];

for await (const message of query({
  prompt: "Add a new React component for user profiles",
  options: {
    systemPrompt: {
      type: "preset",
      preset: "claude_code", // 使用 Claude Code 的系统提示
    },
    settingSources: ["project"], // 从项目加载 CLAUDE.md 所必需
  },
})) {
  messages.push(message);
}

// 现在 Claude 可以访问您 CLAUDE.md 中的项目指南
```

```python Python
from claude_agent_sdk import query, ClaudeAgentOptions

# 重要：您必须指定 setting_sources 来加载 CLAUDE.md
# 仅使用 claude_code 预设不会加载 CLAUDE.md 文件
messages = []

async for message in query(
    prompt="Add a new React component for user profiles",
    options=ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code"  # 使用 Claude Code 的系统提示
        },
        setting_sources=["project"]  # 从项目加载 CLAUDE.md 所必需
    )
):
    messages.append(message)

# 现在 Claude 可以访问您 CLAUDE.md 中的项目指南
```

</CodeGroup>

#### 何时使用 CLAUDE.md

**最适合：**

- **团队共享上下文** - 每个人都应遵循的指南
- **项目约定** - 编码标准、文件结构、命名模式
- **常用命令** - 项目特定的构建、测试、部署命令
- **长期记忆** - 应在所有会话中持久保存的上下文
- **版本控制的指令** - 提交到 git 以保持团队同步

**关键特征：**

- ✅ 在项目中的所有会话中持久保存
- ✅ 通过 git 与团队共享
- ✅ 自动发现（无需更改代码）
- ⚠️ 需要通过 `settingSources` 加载设置

### 方法 2：输出样式（持久化配置）

输出样式是修改 Claude 系统提示的已保存配置。它们以 markdown 文件形式存储，可以在不同会话和项目之间重复使用。

#### 创建输出样式

<CodeGroup>

```typescript TypeScript
import { writeFile, mkdir } from "fs/promises";
import { join } from "path";
import { homedir } from "os";

async function createOutputStyle(
  name: string,
  description: string,
  prompt: string
) {
  // 用户级：~/.claude/output-styles
  // 项目级：.claude/output-styles
  const outputStylesDir = join(homedir(), ".claude", "output-styles");

  await mkdir(outputStylesDir, { recursive: true });

  const content = `---
name: ${name}
description: ${description}
---

${prompt}`;

  const filePath = join(
    outputStylesDir,
    `${name.toLowerCase().replace(/\s+/g, "-")}.md`
  );
  await writeFile(filePath, content, "utf-8");
}

// 示例：创建代码审查专家
await createOutputStyle(
  "Code Reviewer",
  "Thorough code review assistant",
  `You are an expert code reviewer.

For every code submission:
1. Check for bugs and security issues
2. Evaluate performance
3. Suggest improvements
4. Rate code quality (1-10)`
);
```

```python Python
from pathlib import Path

async def create_output_style(name: str, description: str, prompt: str):
    # 用户级：~/.claude/output-styles
    # 项目级：.claude/output-styles
    output_styles_dir = Path.home() / '.claude' / 'output-styles'

    output_styles_dir.mkdir(parents=True, exist_ok=True)

    content = f"""---
name: {name}
description: {description}
---

{prompt}"""

    file_name = name.lower().replace(' ', '-') + '.md'
    file_path = output_styles_dir / file_name
    file_path.write_text(content, encoding='utf-8')

# 示例：创建代码审查专家
await create_output_style(
    'Code Reviewer',
    'Thorough code review assistant',
    """You are an expert code reviewer.

For every code submission:
1. Check for bugs and security issues
2. Evaluate performance
3. Suggest improvements
4. Rate code quality (1-10)"""
)
```

</CodeGroup>

#### 使用输出样式

创建后，通过以下方式激活输出样式：

- **CLI**：`/output-style [style-name]`
- **设置**：`.claude/settings.local.json`
- **创建新样式**：`/output-style:new [description]`

**SDK 用户注意：** 当您在选项中包含 `settingSources: ['user']` 或 `settingSources: ['project']`（TypeScript）/ `setting_sources=["user"]` 或 `setting_sources=["project"]`（Python）时，输出样式会被加载。

### 方法 3：使用带 append 的 `systemPrompt`

您可以使用 Claude Code 预设并添加 `append` 属性，在保留所有内置功能的同时添加自定义指令。

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

const messages = [];

for await (const message of query({
  prompt: "Help me write a Python function to calculate fibonacci numbers",
  options: {
    systemPrompt: {
      type: "preset",
      preset: "claude_code",
      append:
        "Always include detailed docstrings and type hints in Python code.",
    },
  },
})) {
  messages.push(message);
  if (message.type === "assistant") {
    console.log(message.message.content);
  }
}
```

```python Python
from claude_agent_sdk import query, ClaudeAgentOptions

messages = []

async for message in query(
    prompt="Help me write a Python function to calculate fibonacci numbers",
    options=ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": "Always include detailed docstrings and type hints in Python code."
        }
    )
):
    messages.append(message)
    if message.type == 'assistant':
        print(message.message.content)
```

</CodeGroup>

### 方法 4：自定义系统提示

您可以提供自定义字符串作为 `systemPrompt`，用您自己的指令完全替换默认提示。

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

const customPrompt = `You are a Python coding specialist.
Follow these guidelines:
- Write clean, well-documented code
- Use type hints for all functions
- Include comprehensive docstrings
- Prefer functional programming patterns when appropriate
- Always explain your code choices`;

const messages = [];

for await (const message of query({
  prompt: "Create a data processing pipeline",
  options: {
    systemPrompt: customPrompt,
  },
})) {
  messages.push(message);
  if (message.type === "assistant") {
    console.log(message.message.content);
  }
}
```

```python Python
from claude_agent_sdk import query, ClaudeAgentOptions

custom_prompt = """You are a Python coding specialist.
Follow these guidelines:
- Write clean, well-documented code
- Use type hints for all functions
- Include comprehensive docstrings
- Prefer functional programming patterns when appropriate
- Always explain your code choices"""

messages = []

async for message in query(
    prompt="Create a data processing pipeline",
    options=ClaudeAgentOptions(
        system_prompt=custom_prompt
    )
):
    messages.append(message)
    if message.type == 'assistant':
        print(message.message.content)
```

</CodeGroup>

## 四种方法的比较

| 特性                 | CLAUDE.md           | 输出样式      | 带 append 的 `systemPrompt` | 自定义 `systemPrompt`     |
| ----------------------- | ------------------- | ------------------ | -------------------------- | ------------------------- |
| **持久性**         | 项目级文件 | 保存为文件  | 仅限会话            | 仅限会话           |
| **可重用性**         | 项目级      | 跨项目 | 代码重复        | 代码重复       |
| **管理方式**          | 文件系统    | CLI + 文件     | 代码中                 | 代码中                |
| **默认工具**       | 保留        | 保留       | 保留               | 丢失（除非包含） |
| **内置安全性**     | 保持       | 保持      | 保持              | 必须手动添加          |
| **环境上下文** | 自动        | 自动       | 自动               | 必须手动提供       |
| **自定义级别** | 仅追加   | 替换默认 | 仅追加          | 完全控制       |
| **版本控制**     | 随项目     | 是             | 随代码               | 随代码              |
| **作用范围**               | 项目特定 | 用户或项目 | 代码会话            | 代码会话           |

**注意：** "带 append" 指的是在 TypeScript 中使用 `systemPrompt: { type: "preset", preset: "claude_code", append: "..." }`，或在 Python 中使用 `system_prompt={"type": "preset", "preset": "claude_code", "append": "..."}`。

## 用例和最佳实践

### 何时使用 CLAUDE.md

**最适合：**

- 项目特定的编码标准和约定
- 记录项目结构和架构
- 列出常用命令（构建、测试、部署）
- 应进行版本控制的团队共享上下文
- 适用于项目中所有 SDK 使用的指令

**示例：**

- "所有 API 端点应使用 async/await 模式"
- "提交前运行 `npm run lint:fix`"
- "数据库迁移文件在 `migrations/` 目录中"

**重要：** 要加载 CLAUDE.md 文件，您必须显式设置 `settingSources: ['project']`（TypeScript）或 `setting_sources=["project"]`（Python）。如果没有此设置，`claude_code` 系统提示预设不会自动加载 CLAUDE.md。

### 何时使用输出样式

**最适合：**

- 跨会话的持久行为更改
- 团队共享配置
- 专业化助手（代码审查员、数据科学家、DevOps）
- 需要版本控制的复杂提示修改

**示例：**

- 创建专用的 SQL 优化助手
- 构建以安全为重点的代码审查员
- 开发具有特定教学法的教学助手

### 何时使用带 append 的 `systemPrompt`

**最适合：**

- 添加特定的编码标准或偏好
- 自定义输出格式
- 添加领域特定知识
- 修改响应详细程度
- 在不丢失工具指令的情况下增强 Claude Code 的默认行为

### 何时使用自定义 `systemPrompt`

**最适合：**

- 完全控制 Claude 的行为
- 专业化的单次会话任务
- 测试新的提示策略
- 不需要默认工具的场景
- 构建具有独特行为的专业化代理

## 组合使用多种方法

您可以组合这些方法以获得最大灵活性：

### 示例：输出样式与会话特定追加内容

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 假设 "Code Reviewer" 输出样式已激活（通过 /output-style）
// 添加会话特定的关注领域
const messages = [];

for await (const message of query({
  prompt: "Review this authentication module",
  options: {
    systemPrompt: {
      type: "preset",
      preset: "claude_code",
      append: `
        For this review, prioritize:
        - OAuth 2.0 compliance
        - Token storage security
        - Session management
      `,
    },
  },
})) {
  messages.push(message);
}
```

```python Python
from claude_agent_sdk import query, ClaudeAgentOptions

# 假设 "Code Reviewer" 输出样式已激活（通过 /output-style）
# 添加会话特定的关注领域
messages = []

async for message in query(
    prompt="Review this authentication module",
    options=ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": """
            For this review, prioritize:
            - OAuth 2.0 compliance
            - Token storage security
            - Session management
            """
        }
    )
):
    messages.append(message)
```

</CodeGroup>

## 另请参阅

- [输出样式](https://code.claude.com/docs/en/output-styles) - 完整的输出样式文档
- [TypeScript SDK 指南](/docs/zh-CN/agent-sdk/typescript) - 完整的 SDK 使用指南
- [配置指南](https://code.claude.com/docs/en/settings) - 通用配置选项