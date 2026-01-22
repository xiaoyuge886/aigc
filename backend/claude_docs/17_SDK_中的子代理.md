# SDK 中的子代理

在 Claude Agent SDK 中使用子代理

Claude Agent SDK 中的子代理是由主代理编排的专门化 AI。使用子代理进行上下文管理和并行化。

本指南解释如何使用 `agents` 参数在 SDK 中定义和使用子代理。

## 概述

在使用 SDK 时，子代理可以通过两种方式定义：

1. **编程方式** - 在 `query()` 选项中使用 `agents` 参数（推荐用于 SDK 应用程序）
2. **基于文件系统** - 将带有 YAML 前置内容的 markdown 文件放置在指定目录中（`.claude/agents/`）

本指南主要关注使用 `agents` 参数的编程方式，这为 SDK 应用程序提供了更集成的开发体验。

## 使用子代理的好处

### 上下文管理

子代理与主代理保持独立的上下文，防止信息过载并保持交互的专注性。这种隔离确保专门化任务不会用无关细节污染主对话上下文。

**示例**：`research-assistant` 子代理可以探索数十个文件和文档页面，而不会用所有中间搜索结果混乱主对话 - 只返回相关发现。

### 并行化

多个子代理可以并发运行，显著加速复杂工作流程。

**示例**：在代码审查期间，您可以同时运行 `style-checker`、`security-scanner` 和 `test-coverage` 子代理，将审查时间从几分钟缩短到几秒钟。

### 专门化指令和知识

每个子代理都可以有定制的系统提示，具有特定的专业知识、最佳实践和约束。

**示例**：`database-migration` 子代理可以拥有关于 SQL 最佳实践、回滚策略和数据完整性检查的详细知识，这些在主代理的指令中会是不必要的噪音。

### 工具限制

子代理可以限制为特定工具，减少意外操作的风险。

**示例**：`doc-reviewer` 子代理可能只能访问 Read 和 Grep 工具，确保它可以分析但永远不会意外修改您的文档文件。

## 创建子代理

### 编程定义（推荐）

使用 `agents` 参数直接在代码中定义子代理：

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk';

const result = query({
  prompt: "审查身份验证模块的安全问题",
  options: {
    agents: {
      'code-reviewer': {
        description: '专家代码审查专家。用于质量、安全和可维护性审查。',
        prompt: `您是一位代码审查专家，具有安全、性能和最佳实践方面的专业知识。

审查代码时：
- 识别安全漏洞
- 检查性能问题
- 验证编码标准的遵守情况
- 建议具体改进

在反馈中要彻底但简洁。`,
        tools: ['Read', 'Grep', 'Glob'],
        model: 'sonnet'
      },
      'test-runner': {
        description: '运行和分析测试套件。用于测试执行和覆盖率分析。',
        prompt: `您是测试执行专家。运行测试并提供清晰的结果分析。

专注于：
- 运行测试命令
- 分析测试输出
- 识别失败的测试
- 建议失败的修复方案`,
        tools: ['Bash', 'Read', 'Grep'],
      }
    }
  }
});

for await (const message of result) {
  console.log(message);
}
```

### AgentDefinition 配置

| 字段 | 类型 | 必需 | 描述 |
| --- | --- | --- | --- |
| `description` | `string` | 是 | 何时使用此代理的自然语言描述 |
| `prompt` | `string` | 是 | 代理的系统提示，定义其角色和行为 |
| `tools` | `string[]` | 否 | 允许的工具名称数组。如果省略，继承所有工具 |
| `model` | `'sonnet' | 'opus' | 'haiku' | 'inherit'` | 否 | 此代理的模型覆盖。如果省略，默认为主模型 |

### 基于文件系统的定义（替代方案）

您也可以将子代理定义为特定目录中的 markdown 文件：

- **项目级别**：`.claude/agents/*.md` - 仅在当前项目中可用
- **用户级别**：`~/.claude/agents/*.md` - 在所有项目中可用

每个子代理都是一个带有 YAML 前置内容的 markdown 文件：

```markdown
---
name: code-reviewer
description: 专家代码审查专家。用于质量、安全和可维护性审查。
tools: Read, Grep, Glob, Bash
---

您的子代理系统提示在这里。这定义了子代理的
角色、能力和解决问题的方法。
```

**注意**：编程定义的代理（通过 `agents` 参数）优先于同名的基于文件系统的代理。

## SDK 如何使用子代理

使用 Claude Agent SDK 时，子代理可以通过编程方式定义或从文件系统加载。Claude 将：

1. **加载编程代理** 从选项中的 `agents` 参数
2. **自动检测文件系统代理** 从 `.claude/agents/` 目录（如果未被覆盖）
3. **自动调用它们** 基于任务匹配和代理的 `description`
4. **使用它们的专门化提示** 和工具限制
5. **为每个子代理调用维护独立上下文**

编程定义的代理（通过 `agents` 参数）优先于同名的基于文件系统的代理。

## 示例子代理

有关子代理的全面示例，包括代码审查器、测试运行器、调试器和安全审计器，请参阅主要子代理指南。该指南包括详细的配置和创建有效子代理的最佳实践。

## SDK 集成模式

### 自动调用

SDK 将根据任务上下文自动调用适当的子代理。确保您的代理的 `description` 字段清楚地指示何时应该使用它：

```typescript
const result = query({
  prompt: "优化 API 层中的数据库查询",
  options: {
    agents: {
      'performance-optimizer': {
        description: '当代码更改可能影响性能时主动使用。必须用于优化任务。',
        prompt: '您是性能优化专家...',
        tools: ['Read', 'Edit', 'Bash', 'Grep'],
        model: 'sonnet'
      }
    }
  }
});
```

### 显式调用

用户可以在提示中请求特定的子代理：

```typescript
const result = query({
  prompt: "使用 code-reviewer 代理检查身份验证模块",
  options: {
    agents: {
      'code-reviewer': {
        description: '专家代码审查专家',
        prompt: '您是专注于安全的代码审查员...',
        tools: ['Read', 'Grep', 'Glob']
      }
    }
  }
});
```

### 动态代理配置

您可以根据应用程序的需要动态配置代理：

```typescript
import { query, type AgentDefinition } from '@anthropic-ai/claude-agent-sdk';

function createSecurityAgent(securityLevel: 'basic' | 'strict'): AgentDefinition {
  return {
    description: '安全代码审查员',
    prompt: `您是一位${securityLevel === 'strict' ? '严格' : '平衡'}的安全审查员...`,
    tools: ['Read', 'Grep', 'Glob'],
    model: securityLevel === 'strict' ? 'opus' : 'sonnet'
  };
}

const result = query({
  prompt: "审查此 PR 的安全问题",
  options: {
    agents: {
      'security-reviewer': createSecurityAgent('strict')
    }
  }
});
```

## 工具限制

子代理可以通过 `tools` 字段限制工具访问：

- **省略该字段** - 代理继承所有可用工具（默认）
- **指定工具** - 代理只能使用列出的工具

只读分析代理的示例：

```typescript
const result = query({
  prompt: "分析此代码库的架构",
  options: {
    agents: {
      'code-analyzer': {
        description: '静态代码分析和架构审查',
        prompt: `您是代码架构分析师。分析代码结构，
识别模式，并建议改进而不进行更改。`,
        tools: ['Read', 'Grep', 'Glob']  // 没有写入或执行权限
      }
    }
  }
});
```

### 常见工具组合

**只读代理**（分析、审查）：

```typescript
tools: ['Read', 'Grep', 'Glob']
```

**测试执行代理**：

```typescript
tools: ['Bash', 'Read', 'Grep']
```

**代码修改代理**：

```typescript
tools: ['Read', 'Edit', 'Write', 'Grep', 'Glob']
```

## 相关文档

- 主要子代理指南 - 全面的子代理文档
- SDK 概述 - Claude Agent SDK 概述
- 设置 - 配置文件参考
- 斜杠命令 - 自定义命令创建
