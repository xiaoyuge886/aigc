# SDK 中的 Agent 技能

使用 Claude Agent SDK 中的 Agent 技能为 Claude 扩展专业能力

---

## 概述

Agent 技能为 Claude 扩展了专业能力，Claude 会在相关时自主调用这些技能。技能以 `SKILL.md` 文件的形式打包，包含指令、描述和可选的支持资源。

有关技能的全面信息，包括优势、架构和编写指南，请参阅 [Agent 技能概述](/docs/zh-CN/agents-and-tools/agent-skills/overview)。

## 技能如何与 SDK 配合工作

使用 Claude Agent SDK 时，技能：

1. **定义为文件系统工件**：作为 `SKILL.md` 文件创建在特定目录中（`.claude/skills/`）
2. **从文件系统加载**：技能从配置的文件系统位置加载。您必须指定 `settingSources`（TypeScript）或 `setting_sources`（Python）以从文件系统加载技能
3. **自动发现**：一旦加载了文件系统设置，技能元数据在启动时从用户和项目目录中发现；完整内容在触发时加载
4. **模型调用**：Claude 根据上下文自主选择何时使用它们
5. **通过 allowed_tools 启用**：将 `"Skill"` 添加到您的 `allowed_tools` 中以启用技能

与子代理（可以通过编程方式定义）不同，技能必须作为文件系统工件创建。SDK 不提供用于注册技能的编程 API。

<Note>
**默认行为**：默认情况下，SDK 不会加载任何文件系统设置。要使用技能，您必须在选项中显式配置 `settingSources: ['user', 'project']`（TypeScript）或 `setting_sources=["user", "project"]`（Python）。
</Note>

## 在 SDK 中使用技能

要在 SDK 中使用技能，您需要：

1. 在 `allowed_tools` 配置中包含 `"Skill"`
2. 配置 `settingSources`/`setting_sources` 以从文件系统加载技能

配置完成后，Claude 会自动从指定目录发现技能，并在与用户请求相关时调用它们。

<CodeGroup>

```python Python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        cwd="/path/to/project",  # 包含 .claude/skills/ 的项目
        setting_sources=["user", "project"],  # 从文件系统加载技能
        allowed_tools=["Skill", "Read", "Write", "Bash"]  # 启用 Skill 工具
    )

    async for message in query(
        prompt="Help me process this PDF document",
        options=options
    ):
        print(message)

asyncio.run(main())
```

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Help me process this PDF document",
  options: {
    cwd: "/path/to/project",  // 包含 .claude/skills/ 的项目
    settingSources: ["user", "project"],  // 从文件系统加载技能
    allowedTools: ["Skill", "Read", "Write", "Bash"]  // 启用 Skill 工具
  }
})) {
  console.log(message);
}
```

</CodeGroup>

## 技能位置

技能根据您的 `settingSources`/`setting_sources` 配置从文件系统目录加载：

- **项目技能**（`.claude/skills/`）：通过 git 与团队共享 - 当 `setting_sources` 包含 `"project"` 时加载
- **用户技能**（`~/.claude/skills/`）：跨所有项目的个人技能 - 当 `setting_sources` 包含 `"user"` 时加载
- **插件技能**：与已安装的 Claude Code 插件捆绑

## 创建技能

技能定义为包含 `SKILL.md` 文件的目录，文件包含 YAML 前置元数据和 Markdown 内容。`description` 字段决定 Claude 何时调用您的技能。

**示例目录结构**：
```bash
.claude/skills/processing-pdfs/
└── SKILL.md
```

有关创建技能的完整指南，包括 SKILL.md 结构、多文件技能和示例，请参阅：
- [Claude Code 中的 Agent 技能](https://code.claude.com/docs/en/skills)：包含示例的完整指南
- [Agent 技能最佳实践](/docs/zh-CN/agents-and-tools/agent-skills/best-practices)：编写指南和命名约定

## 工具限制

<Note>
SKILL.md 中的 `allowed-tools` 前置元数据字段仅在直接使用 Claude Code CLI 时受支持。**通过 SDK 使用技能时不适用**。

使用 SDK 时，请通过查询配置中的主 `allowedTools` 选项控制工具访问。
</Note>

要在 SDK 应用程序中限制技能的工具，请使用 `allowedTools` 选项：

<Note>
以下代码片段假设已包含第一个示例中的导入语句。
</Note>

<CodeGroup>

```python Python
options = ClaudeAgentOptions(
    setting_sources=["user", "project"],  # 从文件系统加载技能
    allowed_tools=["Skill", "Read", "Grep", "Glob"]  # 受限工具集
)

async for message in query(
    prompt="Analyze the codebase structure",
    options=options
):
    print(message)
```

```typescript TypeScript
// 技能只能使用 Read、Grep 和 Glob 工具
for await (const message of query({
  prompt: "Analyze the codebase structure",
  options: {
    settingSources: ["user", "project"],  // 从文件系统加载技能
    allowedTools: ["Skill", "Read", "Grep", "Glob"]  // 受限工具集
  }
})) {
  console.log(message);
}
```

</CodeGroup>

## 发现可用技能

要查看 SDK 应用程序中有哪些可用技能，只需询问 Claude：

<CodeGroup>

```python Python
options = ClaudeAgentOptions(
    setting_sources=["user", "project"],  # 从文件系统加载技能
    allowed_tools=["Skill"]
)

async for message in query(
    prompt="What Skills are available?",
    options=options
):
    print(message)
```

```typescript TypeScript
for await (const message of query({
  prompt: "What Skills are available?",
  options: {
    settingSources: ["user", "project"],  // 从文件系统加载技能
    allowedTools: ["Skill"]
  }
})) {
  console.log(message);
}
```

</CodeGroup>

Claude 将根据您当前的工作目录和已安装的插件列出可用的技能。

## 测试技能

通过提出与技能描述匹配的问题来测试技能：

<CodeGroup>

```python Python
options = ClaudeAgentOptions(
    cwd="/path/to/project",
    setting_sources=["user", "project"],  # 从文件系统加载技能
    allowed_tools=["Skill", "Read", "Bash"]
)

async for message in query(
    prompt="Extract text from invoice.pdf",
    options=options
):
    print(message)
```

```typescript TypeScript
for await (const message of query({
  prompt: "Extract text from invoice.pdf",
  options: {
    cwd: "/path/to/project",
    settingSources: ["user", "project"],  // 从文件系统加载技能
    allowedTools: ["Skill", "Read", "Bash"]
  }
})) {
  console.log(message);
}
```

</CodeGroup>

如果描述与您的请求匹配，Claude 会自动调用相关技能。

## 故障排除

### 未找到技能

**检查 settingSources 配置**：技能仅在您显式配置 `settingSources`/`setting_sources` 时才会加载。这是最常见的问题：

<CodeGroup>

```python Python
# 错误 - 技能不会被加载
options = ClaudeAgentOptions(
    allowed_tools=["Skill"]
)

# 正确 - 技能将被加载
options = ClaudeAgentOptions(
    setting_sources=["user", "project"],  # 加载技能所必需
    allowed_tools=["Skill"]
)
```

```typescript TypeScript
// 错误 - 技能不会被加载
const options = {
  allowedTools: ["Skill"]
};

// 正确 - 技能将被加载
const options = {
  settingSources: ["user", "project"],  // 加载技能所必需
  allowedTools: ["Skill"]
};
```

</CodeGroup>

有关 `settingSources`/`setting_sources` 的更多详细信息，请参阅 [TypeScript SDK 参考](/docs/zh-CN/agent-sdk/typescript#settingsource) 或 [Python SDK 参考](/docs/zh-CN/agent-sdk/python#settingsource)。

**检查工作目录**：SDK 相对于 `cwd` 选项加载技能。确保它指向包含 `.claude/skills/` 的目录：

<CodeGroup>

```python Python
# 确保您的 cwd 指向包含 .claude/skills/ 的目录
options = ClaudeAgentOptions(
    cwd="/path/to/project",  # 必须包含 .claude/skills/
    setting_sources=["user", "project"],  # 加载技能所必需
    allowed_tools=["Skill"]
)
```

```typescript TypeScript
// 确保您的 cwd 指向包含 .claude/skills/ 的目录
const options = {
  cwd: "/path/to/project",  // 必须包含 .claude/skills/
  settingSources: ["user", "project"],  // 加载技能所必需
  allowedTools: ["Skill"]
};
```

</CodeGroup>

请参阅上面的"在 SDK 中使用技能"部分了解完整模式。

**验证文件系统位置**：
```bash
# 检查项目技能
ls .claude/skills/*/SKILL.md

# 检查个人技能
ls ~/.claude/skills/*/SKILL.md
```

### 技能未被使用

**检查 Skill 工具是否已启用**：确认 `"Skill"` 在您的 `allowedTools` 中。

**检查描述**：确保描述具体且包含相关关键词。请参阅 [Agent 技能最佳实践](/docs/zh-CN/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions) 了解编写有效描述的指南。

### 其他故障排除

有关通用技能故障排除（YAML 语法、调试等），请参阅 [Claude Code 技能故障排除部分](https://code.claude.com/docs/en/skills#troubleshooting)。

## 相关文档

### 技能指南
- [Claude Code 中的 Agent 技能](https://code.claude.com/docs/en/skills)：包含创建、示例和故障排除的完整技能指南
- [Agent 技能概述](/docs/zh-CN/agents-and-tools/agent-skills/overview)：概念概述、优势和架构
- [Agent 技能最佳实践](/docs/zh-CN/agents-and-tools/agent-skills/best-practices)：编写有效技能的指南
- [Agent 技能手册](https://platform.claude.com/cookbook/skills-notebooks-01-skills-introduction)：示例技能和模板

### SDK 资源
- [SDK 中的子代理](/docs/zh-CN/agent-sdk/subagents)：类似的基于文件系统的代理，具有编程选项
- [SDK 中的斜杠命令](/docs/zh-CN/agent-sdk/slash-commands)：用户调用的命令
- [SDK 概述](/docs/zh-CN/agent-sdk/overview)：通用 SDK 概念
- [TypeScript SDK 参考](/docs/zh-CN/agent-sdk/typescript)：完整 API 文档
- [Python SDK 参考](/docs/zh-CN/agent-sdk/python)：完整 API 文档