# SDK 中的斜杠命令

学习如何通过 SDK 使用斜杠命令来控制 Claude Code 会话

斜杠命令提供了一种使用以 `/` 开头的特殊命令来控制 Claude Code 会话的方法。这些命令可以通过 SDK 发送，以执行清除对话历史、压缩消息或获取帮助等操作。

## 发现可用的斜杠命令

Claude Agent SDK 在系统初始化消息中提供有关可用斜杠命令的信息。在会话开始时访问此信息：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Hello Claude",
  options: { maxTurns: 1 }
})) {
  if (message.type === "system" && message.subtype === "init") {
    console.log("Available slash commands:", message.slash_commands);
    // Example output: ["/compact", "/clear", "/help"]
  }
}
```

## 发送斜杠命令

通过在提示字符串中包含斜杠命令来发送它们，就像常规文本一样：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Send a slash command
for await (const message of query({
  prompt: "/compact",
  options: { maxTurns: 1 }
})) {
  if (message.type === "result") {
    console.log("Command executed:", message.result);
  }
}
```

## 常见斜杠命令

### `/compact` - 压缩对话历史

`/compact` 命令通过总结较旧的消息同时保留重要上下文来减少对话历史的大小：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "/compact",
  options: { maxTurns: 1 }
})) {
  if (message.type === "system" && message.subtype === "compact_boundary") {
    console.log("Compaction completed");
    console.log("Pre-compaction tokens:", message.compact_metadata.pre_tokens);
    console.log("Trigger:", message.compact_metadata.trigger);
  }
}
```

### `/clear` - 清除对话

`/clear` 命令通过清除所有先前历史来开始新的对话：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Clear conversation and start fresh
for await (const message of query({
  prompt: "/clear",
  options: { maxTurns: 1 }
})) {
  if (message.type === "system" && message.subtype === "init") {
    console.log("Conversation cleared, new session started");
    console.log("Session ID:", message.session_id);
  }
}
```

## 创建自定义斜杠命令

除了使用内置斜杠命令外，您还可以创建自己的自定义命令，这些命令可通过 SDK 使用。自定义命令定义为特定目录中的 markdown 文件，类似于子代理的配置方式。

### 文件位置

自定义斜杠命令根据其作用域存储在指定目录中：

- **项目命令**：`.claude/commands/` - 仅在当前项目中可用
- **个人命令**：`~/.claude/commands/` - 在您的所有项目中可用

### 文件格式

每个自定义命令都是一个 markdown 文件，其中：

- 文件名（不含 `.md` 扩展名）成为命令名称
- 文件内容定义命令的功能
- 可选的 YAML 前言提供配置

#### 基本示例

创建 `.claude/commands/refactor.md`：

```markdown
Refactor the selected code to improve readability and maintainability.
Focus on clean code principles and best practices.
```

这将创建 `/refactor` 命令，您可以通过 SDK 使用它。

#### 带前言的示例

创建 `.claude/commands/security-check.md`：

```markdown
---
allowed-tools: Read, Grep, Glob
description: Run security vulnerability scan
model: claude-3-5-sonnet-20241022
---

Analyze the codebase for security vulnerabilities including:
- SQL injection risks
- XSS vulnerabilities
- Exposed credentials
- Insecure configurations
```

### 在 SDK 中使用自定义命令

一旦在文件系统中定义，自定义命令就会自动通过 SDK 可用：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Use a custom command
for await (const message of query({
  prompt: "/refactor src/auth/login.ts",
  options: { maxTurns: 3 }
})) {
  if (message.type === "assistant") {
    console.log("Refactoring suggestions:", message.message);
  }
}

// Custom commands appear in the slash_commands list
for await (const message of query({
  prompt: "Hello",
  options: { maxTurns: 1 }
})) {
  if (message.type === "system" && message.subtype === "init") {
    // Will include both built-in and custom commands
    console.log("Available commands:", message.slash_commands);
    // Example: ["/compact", "/clear", "/help", "/refactor", "/security-check"]
  }
}
```

### 高级功能

#### 参数和占位符

自定义命令支持使用占位符的动态参数：

创建 `.claude/commands/fix-issue.md`：

```markdown
---
argument-hint: [issue-number] [priority]
description: Fix a GitHub issue
---

Fix issue #$1 with priority $2.
Check the issue description and implement the necessary changes.
```

在 SDK 中使用：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Pass arguments to custom command
for await (const message of query({
  prompt: "/fix-issue 123 high",
  options: { maxTurns: 5 }
})) {
  // Command will process with $1="123" and $2="high"
  if (message.type === "result") {
    console.log("Issue fixed:", message.result);
  }
}
```

#### Bash 命令执行

自定义命令可以执行 bash 命令并包含其输出：

创建 `.claude/commands/git-commit.md`：

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit
---

## Context

- Current status: !`git status`
- Current diff: !`git diff HEAD`

## Task

Create a git commit with appropriate message based on the changes.
```

#### 文件引用

使用 `@` 前缀包含文件内容：

创建 `.claude/commands/review-config.md`：

```markdown
---
description: Review configuration files
---

Review the following configuration files for issues:
- Package config: @package.json
- TypeScript config: @tsconfig.json
- Environment config: @.env

Check for security issues, outdated dependencies, and misconfigurations.
```

### 使用命名空间进行组织

在子目录中组织命令以获得更好的结构：

```
.claude/commands/
├── frontend/
│   ├── component.md      # Creates /component (project:frontend)
│   └── style-check.md     # Creates /style-check (project:frontend)
├── backend/
│   ├── api-test.md        # Creates /api-test (project:backend)
│   └── db-migrate.md      # Creates /db-migrate (project:backend)
└── review.md              # Creates /review (project)
```

子目录出现在命令描述中，但不影响命令名称本身。

### 实际示例

#### 代码审查命令

创建 `.claude/commands/code-review.md`：

```markdown
---
allowed-tools: Read, Grep, Glob, Bash(git diff:*)
description: Comprehensive code review
---

## Changed Files
!`git diff --name-only HEAD~1`

## Detailed Changes
!`git diff HEAD~1`

## Review Checklist

Review the above changes for:
1. Code quality and readability
2. Security vulnerabilities
3. Performance implications
4. Test coverage
5. Documentation completeness

Provide specific, actionable feedback organized by priority.
```

#### 测试运行器命令

创建 `.claude/commands/test.md`：

```markdown
---
allowed-tools: Bash, Read, Edit
argument-hint: [test-pattern]
description: Run tests with optional pattern
---

Run tests matching pattern: $ARGUMENTS

1. Detect the test framework (Jest, pytest, etc.)
2. Run tests with the provided pattern
3. If tests fail, analyze and fix them
4. Re-run to verify fixes
```

通过 SDK 使用这些命令：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// Run code review
for await (const message of query({
  prompt: "/code-review",
  options: { maxTurns: 3 }
})) {
  // Process review feedback
}

// Run specific tests
for await (const message of query({
  prompt: "/test auth",
  options: { maxTurns: 5 }
})) {
  // Handle test results
}
```

## 另请参阅

- 斜杠命令 - 完整的斜杠命令文档
- SDK 中的子代理 - 子代理的类似基于文件系统的配置
- TypeScript SDK 参考 - 完整的 API 文档
- SDK 概述 - 一般 SDK 概念
- CLI 参考 - 命令行界面
