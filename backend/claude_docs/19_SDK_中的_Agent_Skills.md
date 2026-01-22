# SDK 中的代理技能

使用 Claude 代理 SDK 中的代理技能扩展 Claude 的专业功能

## 概述

代理技能使用专业功能扩展 Claude，Claude 会在相关时自主调用这些功能。技能被打包为 `SKILL.md` 文件，包含说明、描述和可选的支持资源。

有关技能的全面信息，包括优势、架构和编写指南，请参阅代理技能概述。

## 技能如何与 SDK 配合使用

使用 Claude 代理 SDK 时，技能具有以下特点：

1. **定义为文件系统工件**：在特定目录（`.claude/skills/`）中创建为 `SKILL.md` 文件
2. **从文件系统加载**：技能从配置的文件系统位置加载。您必须指定 `settingSources`（TypeScript）或 `setting_sources`（Python）以从文件系统加载技能
3. **自动发现**：加载文件系统设置后，在启动时从用户和项目目录发现技能元数据；触发时加载完整内容
4. **模型调用**：Claude 根据上下文自主选择何时使用它们
5. **通过 allowed_tools 启用**：将 `"Skill"` 添加到您的 `allowed_tools` 以启用技能

与子代理（可以以编程方式定义）不同，技能必须创建为文件系统工件。SDK 不提供用于注册技能的编程 API。

**默认行为**：默认情况下，SDK 不加载任何文件系统设置。要使用技能，您必须在选项中显式配置 `settingSources: ['user', 'project']`（TypeScript）或 `setting_sources=["user", "project"]`（Python）。

## 在 SDK 中使用技能

要在 SDK 中使用技能，您需要：

1. 在 `allowed_tools` 配置中包含 `"Skill"`
2. 配置 `settingSources`/`setting_sources` 以从文件系统加载技能

配置完成后，Claude 会自动从指定目录发现技能，并在与用户请求相关时调用它们。

## 技能位置

技能根据您的 `settingSources`/`setting_sources` 配置从文件系统目录加载：

- **项目技能**（`.claude/skills/`）：通过 git 与您的团队共享 - 当 `setting_sources` 包含 `"project"` 时加载
- **用户技能**（`~/.claude/skills/`）：跨所有项目的个人技能 - 当 `setting_sources` 包含 `"user"` 时加载
- **插件技能**：与已安装的 Claude Code 插件捆绑

## 创建技能

技能定义为包含具有 YAML 前置内容和 Markdown 内容的 `SKILL.md` 文件的目录。`description` 字段确定 Claude 何时调用您的技能。

**示例目录结构**：

```
.claude/skills/processing-pdfs/
└── SKILL.md
```

有关创建技能的完整指导，包括 SKILL.md 结构、多文件技能和示例，请参阅：

- Claude Code 中的代理技能：包含示例的完整指南
- 代理技能最佳实践：编写指南和命名约定

## 工具限制

SKILL.md 中的 `allowed-tools` 前置内容字段仅在直接使用 Claude Code CLI 时受支持。**通过 SDK 使用技能时不适用**。

使用 SDK 时，通过查询配置中的主 `allowedTools` 选项控制工具访问。

要在 SDK 应用程序中限制技能的工具，请使用 `allowedTools` 选项：

```python
options = ClaudeAgentOptions(
    cwd="/path/to/project",  # Project with .claude/skills/
    setting_sources=["user", "project"],  # Load Skills from filesystem
    allowed_tools=["Skill", "Read", "Bash"]  # Enable Skill tool
)

async for message in query(
    prompt="Extract text from invoice.pdf",
    options=options
):
    print(message)
```

## 发现可用技能

要查看 SDK 应用程序中可用的技能，只需询问 Claude：

```python
options = ClaudeAgentOptions(
    setting_sources=["user", "project"],  # Load Skills from filesystem
    allowed_tools=["Skill"]
)

async for message in query(
    prompt="What Skills are available?",
    options=options
):
    print(message)
```

Claude 将根据您当前的工作目录和已安装的插件列出可用的技能。

## 测试技能

通过提出与其描述相匹配的问题来测试技能：

```python
options = ClaudeAgentOptions(
    cwd="/path/to/project",
    setting_sources=["user", "project"],  # Load Skills from filesystem
    allowed_tools=["Skill", "Read", "Grep", "Glob"]
)

async for message in query(
    prompt="Analyze the codebase structure",
    options=options
):
    print(message)
```

如果描述与您的请求匹配，Claude 会自动调用相关技能。

## 故障排除

### 找不到技能

**检查 settingSources 配置**：仅当您显式配置 `settingSources`/`setting_sources` 时才会加载技能。这是最常见的问题：

```python
# Wrong - Skills won't be loaded
options = ClaudeAgentOptions(
    allowed_tools=["Skill"]
)

# Correct - Skills will be loaded
options = ClaudeAgentOptions(
    setting_sources=["user", "project"],  # Required to load Skills
    allowed_tools=["Skill"]
)
```

有关 `settingSources`/`setting_sources` 的更多详情，请参阅 TypeScript SDK 参考或 Python SDK 参考。

**检查工作目录**：SDK 相对于 `cwd` 选项加载技能。确保它指向包含 `.claude/skills/` 的目录：

```python
# Ensure your cwd points to the directory containing .claude/skills/
options = ClaudeAgentOptions(
    cwd="/path/to/project",  # Must contain .claude/skills/
    setting_sources=["user", "project"],  # Required to load Skills
    allowed_tools=["Skill"]
)
```

有关完整模式，请参阅上面的"在 SDK 中使用技能"部分。

**验证文件系统位置**：

```bash
# Check project Skills
ls .claude/skills/*/SKILL.md

# Check personal Skills
ls ~/.claude/skills/*/SKILL.md
```

### 技能未被使用

**检查技能工具是否启用**：确认 `"Skill"` 在您的 `allowedTools` 中。

**检查描述**：确保它具体且包含相关关键字。有关编写有效描述的指导，请参阅代理技能最佳实践。

### 其他故障排除

有关一般技能故障排除（YAML 语法、调试等），请参阅 Claude Code 技能故障排除部分。

## 相关文档

### 技能指南

- Claude Code 中的代理技能：包含创建、示例和故障排除的完整技能指南
- 代理技能概述：概念概述、优势和架构
- 代理技能最佳实践：有效技能的编写指南
- 代理技能食谱：示例技能和模板

### SDK 资源

- SDK 中的子代理：具有编程选项的类似文件系统代理
- SDK 中的斜杠命令：用户调用的命令
- SDK 概述：一般 SDK 概念
- TypeScript SDK 参考：完整 API 文档
- Python SDK 参考：完整 API 文档
