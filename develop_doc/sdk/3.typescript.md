# Agent SDK 参考 - TypeScript

TypeScript Agent SDK 的完整 API 参考，包括所有函数、类型和接口。

---

<script src="/components/typescript-sdk-type-links.js" defer />

<Note>
**试用新的 V2 接口（预览版）：** 现已推出简化接口，支持 `send()` 和 `receive()` 模式，使多轮对话更加便捷。[了解更多关于 TypeScript V2 预览版的信息](/docs/zh-CN/agent-sdk/typescript-v2-preview)
</Note>

## 安装

```bash
npm install @anthropic-ai/claude-agent-sdk
```

## 函数

### `query()`

与 Claude Code 交互的主要函数。创建一个异步生成器，在消息到达时进行流式传输。

```typescript
function query({
  prompt,
  options
}: {
  prompt: string | AsyncIterable<SDKUserMessage>;
  options?: Options;
}): Query
```

#### 参数

| 参数 | 类型 | 描述 |
| :-------- | :--- | :---------- |
| `prompt` | `string \| AsyncIterable<`[`SDKUserMessage`](#sdkusermessage)`>` | 输入提示，可以是字符串或用于流式模式的异步可迭代对象 |
| `options` | [`Options`](#options) | 可选配置对象（参见下方 Options 类型） |

#### 返回值

返回一个 [`Query`](#query-1) 对象，该对象扩展了 `AsyncGenerator<`[`SDKMessage`](#sdkmessage)`, void>` 并包含额外方法。

### `tool()`

创建类型安全的 MCP 工具定义，用于 SDK MCP 服务器。

```typescript
function tool<Schema extends ZodRawShape>(
  name: string,
  description: string,
  inputSchema: Schema,
  handler: (args: z.infer<ZodObject<Schema>>, extra: unknown) => Promise<CallToolResult>
): SdkMcpToolDefinition<Schema>
```

#### 参数

| 参数 | 类型 | 描述 |
| :-------- | :--- | :---------- |
| `name` | `string` | 工具的名称 |
| `description` | `string` | 工具功能的描述 |
| `inputSchema` | `Schema extends ZodRawShape` | 定义工具输入参数的 Zod schema |
| `handler` | `(args, extra) => Promise<`[`CallToolResult`](#calltoolresult)`>` | 执行工具逻辑的异步函数 |

### `createSdkMcpServer()`

创建一个与应用程序在同一进程中运行的 MCP 服务器实例。

```typescript
function createSdkMcpServer(options: {
  name: string;
  version?: string;
  tools?: Array<SdkMcpToolDefinition<any>>;
}): McpSdkServerConfigWithInstance
```

#### 参数

| 参数 | 类型 | 描述 |
| :-------- | :--- | :---------- |
| `options.name` | `string` | MCP 服务器的名称 |
| `options.version` | `string` | 可选的版本字符串 |
| `options.tools` | `Array<SdkMcpToolDefinition>` | 使用 [`tool()`](#tool) 创建的工具定义数组 |

## 类型

### `Options`

`query()` 函数的配置对象。

| 属性 | 类型 | 默认值 | 描述 |
| :------- | :--- | :------ | :---------- |
| `abortController` | `AbortController` | `new AbortController()` | 用于取消操作的控制器 |
| `additionalDirectories` | `string[]` | `[]` | Claude 可以访问的额外目录 |
| `agents` | `Record<string, [`AgentDefinition`](#agentdefinition)>` | `undefined` | 以编程方式定义子代理 |
| `allowDangerouslySkipPermissions` | `boolean` | `false` | 启用绕过权限。使用 `permissionMode: 'bypassPermissions'` 时必须设置 |
| `allowedTools` | `string[]` | 所有工具 | 允许的工具名称列表 |
| `betas` | [`SdkBeta`](#sdkbeta)`[]` | `[]` | 启用测试版功能（例如 `['context-1m-2025-08-07']`） |
| `canUseTool` | [`CanUseTool`](#canusetool) | `undefined` | 工具使用的自定义权限函数 |
| `continue` | `boolean` | `false` | 继续最近的对话 |
| `cwd` | `string` | `process.cwd()` | 当前工作目录 |
| `disallowedTools` | `string[]` | `[]` | 禁止的工具名称列表 |
| `enableFileCheckpointing` | `boolean` | `false` | 启用文件变更跟踪以支持回退。参见[文件检查点](/docs/zh-CN/agent-sdk/file-checkpointing) |
| `env` | `Dict<string>` | `process.env` | 环境变量 |
| `executable` | `'bun' \| 'deno' \| 'node'` | 自动检测 | 要使用的 JavaScript 运行时 |
| `executableArgs` | `string[]` | `[]` | 传递给可执行文件的参数 |
| `extraArgs` | `Record<string, string \| null>` | `{}` | 额外参数 |
| `fallbackModel` | `string` | `undefined` | 主模型失败时使用的备用模型 |
| `forkSession` | `boolean` | `false` | 使用 `resume` 恢复时，分叉到新的会话 ID 而不是继续原始会话 |
| `hooks` | `Partial<Record<`[`HookEvent`](#hookevent)`, `[`HookCallbackMatcher`](#hookcallbackmatcher)`[]>>` | `{}` | 事件的钩子回调 |
| `includePartialMessages` | `boolean` | `false` | 包含部分消息事件 |
| `maxBudgetUsd` | `number` | `undefined` | 查询的最大预算（美元） |
| `maxThinkingTokens` | `number` | `undefined` | 思考过程的最大 token 数 |
| `maxTurns` | `number` | `undefined` | 最大对话轮次 |
| `mcpServers` | `Record<string, [`McpServerConfig`](#mcpserverconfig)>` | `{}` | MCP 服务器配置 |
| `model` | `string` | CLI 默认值 | 要使用的 Claude 模型 |
| `outputFormat` | `{ type: 'json_schema', schema: JSONSchema }` | `undefined` | 定义代理结果的输出格式。详见[结构化输出](/docs/zh-CN/agent-sdk/structured-outputs) |
| `pathToClaudeCodeExecutable` | `string` | 使用内置可执行文件 | Claude Code 可执行文件的路径 |
| `permissionMode` | [`PermissionMode`](#permissionmode) | `'default'` | 会话的权限模式 |
| `permissionPromptToolName` | `string` | `undefined` | 用于权限提示的 MCP 工具名称 |
| `plugins` | [`SdkPluginConfig`](#sdkpluginconfig)`[]` | `[]` | 从本地路径加载自定义插件。详见[插件](/docs/zh-CN/agent-sdk/plugins) |
| `resume` | `string` | `undefined` | 要恢复的会话 ID |
| `resumeSessionAt` | `string` | `undefined` | 在特定消息 UUID 处恢复会话 |
| `sandbox` | [`SandboxSettings`](#sandboxsettings) | `undefined` | 以编程方式配置沙箱行为。详见[沙箱设置](#sandboxsettings) |
| `settingSources` | [`SettingSource`](#settingsource)`[]` | `[]`（无设置） | 控制从哪些文件系统设置加载。省略时不加载任何设置。**注意：** 必须包含 `'project'` 才能加载 CLAUDE.md 文件 |
| `stderr` | `(data: string) => void` | `undefined` | stderr 输出的回调 |
| `strictMcpConfig` | `boolean` | `false` | 强制严格的 MCP 验证 |
| `systemPrompt` | `string \| { type: 'preset'; preset: 'claude_code'; append?: string }` | `undefined`（最小提示） | 系统提示配置。传入字符串作为自定义提示，或传入 `{ type: 'preset', preset: 'claude_code' }` 以使用 Claude Code 的系统提示。使用预设对象形式时，添加 `append` 可以用额外指令扩展系统提示 |
| `tools` | `string[] \| { type: 'preset'; preset: 'claude_code' }` | `undefined` | 工具配置。传入工具名称数组或使用预设获取 Claude Code 的默认工具 |

### `Query`

`query()` 函数返回的接口。

```typescript
interface Query extends AsyncGenerator<SDKMessage, void> {
  interrupt(): Promise<void>;
  rewindFiles(userMessageUuid: string): Promise<void>;
  setPermissionMode(mode: PermissionMode): Promise<void>;
  setModel(model?: string): Promise<void>;
  setMaxThinkingTokens(maxThinkingTokens: number | null): Promise<void>;
  supportedCommands(): Promise<SlashCommand[]>;
  supportedModels(): Promise<ModelInfo[]>;
  mcpServerStatus(): Promise<McpServerStatus[]>;
  accountInfo(): Promise<AccountInfo>;
}
```

#### 方法

| 方法 | 描述 |
| :----- | :---------- |
| `interrupt()` | 中断查询（仅在流式输入模式下可用） |
| `rewindFiles(userMessageUuid)` | 将文件恢复到指定用户消息时的状态。需要 `enableFileCheckpointing: true`。参见[文件检查点](/docs/zh-CN/agent-sdk/file-checkpointing) |
| `setPermissionMode()` | 更改权限模式（仅在流式输入模式下可用） |
| `setModel()` | 更改模型（仅在流式输入模式下可用） |
| `setMaxThinkingTokens()` | 更改最大思考 token 数（仅在流式输入模式下可用） |
| `supportedCommands()` | 返回可用的斜杠命令 |
| `supportedModels()` | 返回可用模型及其显示信息 |
| `mcpServerStatus()` | 返回已连接 MCP 服务器的状态 |
| `accountInfo()` | 返回账户信息 |

### `AgentDefinition`

以编程方式定义的子代理配置。

```typescript
type AgentDefinition = {
  description: string;
  tools?: string[];
  prompt: string;
  model?: 'sonnet' | 'opus' | 'haiku' | 'inherit';
}
```

| 字段 | 必填 | 描述 |
|:------|:---------|:------------|
| `description` | 是 | 描述何时使用此代理的自然语言描述 |
| `tools` | 否 | 允许的工具名称数组。如果省略，则继承所有工具 |
| `prompt` | 是 | 代理的系统提示 |
| `model` | 否 | 此代理的模型覆盖。如果省略，则使用主模型 |

### `SettingSource`

控制 SDK 从哪些基于文件系统的配置源加载设置。

```typescript
type SettingSource = 'user' | 'project' | 'local';
```

| 值 | 描述 | 位置 |
|:------|:------------|:---------|
| `'user'` | 全局用户设置 | `~/.claude/settings.json` |
| `'project'` | 共享项目设置（版本控制） | `.claude/settings.json` |
| `'local'` | 本地项目设置（gitignored） | `.claude/settings.local.json` |

#### 默认行为

当 `settingSources` 被**省略**或为 **undefined** 时，SDK **不会**加载任何文件系统设置。这为 SDK 应用程序提供了隔离性。

#### 为什么使用 settingSources？

**加载所有文件系统设置（旧版行为）：**
```typescript
// 像 SDK v0.0.x 一样加载所有设置
const result = query({
  prompt: "Analyze this code",
  options: {
    settingSources: ['user', 'project', 'local']  // 加载所有设置
  }
});
```

**仅加载特定设置源：**
```typescript
// 仅加载项目设置，忽略用户和本地设置
const result = query({
  prompt: "Run CI checks",
  options: {
    settingSources: ['project']  // 仅 .claude/settings.json
  }
});
```

**测试和 CI 环境：**
```typescript
// 通过排除本地设置确保 CI 中的一致行为
const result = query({
  prompt: "Run tests",
  options: {
    settingSources: ['project'],  // 仅团队共享设置
    permissionMode: 'bypassPermissions'
  }
});
```

**纯 SDK 应用程序：**
```typescript
// 以编程方式定义所有内容（默认行为）
// 无文件系统依赖 - settingSources 默认为 []
const result = query({
  prompt: "Review this PR",
  options: {
    // settingSources: [] 是默认值，无需指定
    agents: { /* ... */ },
    mcpServers: { /* ... */ },
    allowedTools: ['Read', 'Grep', 'Glob']
  }
});
```

**加载 CLAUDE.md 项目指令：**
```typescript
// 加载项目设置以包含 CLAUDE.md 文件
const result = query({
  prompt: "Add a new feature following project conventions",
  options: {
    systemPrompt: {
      type: 'preset',
      preset: 'claude_code'  // 使用 CLAUDE.md 时必需
    },
    settingSources: ['project'],  // 从项目目录加载 CLAUDE.md
    allowedTools: ['Read', 'Write', 'Edit']
  }
});
```

#### 设置优先级

当加载多个源时，设置按以下优先级合并（从高到低）：
1. 本地设置（`.claude/settings.local.json`）
2. 项目设置（`.claude/settings.json`）
3. 用户设置（`~/.claude/settings.json`）

编程选项（如 `agents`、`allowedTools`）始终覆盖文件系统设置。

### `PermissionMode`

```typescript
type PermissionMode =
  | 'default'           // 标准权限行为
  | 'acceptEdits'       // 自动接受文件编辑
  | 'bypassPermissions' // 绕过所有权限检查
  | 'plan'              // 规划模式 - 不执行
```

### `CanUseTool`

用于控制工具使用的自定义权限函数类型。

```typescript
type CanUseTool = (
  toolName: string,
  input: ToolInput,
  options: {
    signal: AbortSignal;
    suggestions?: PermissionUpdate[];
  }
) => Promise<PermissionResult>;
```

### `PermissionResult`

权限检查的结果。

```typescript
type PermissionResult = 
  | {
      behavior: 'allow';
      updatedInput: ToolInput;
      updatedPermissions?: PermissionUpdate[];
    }
  | {
      behavior: 'deny';
      message: string;
      interrupt?: boolean;
    }
```

### `McpServerConfig`

MCP 服务器的配置。

```typescript
type McpServerConfig = 
  | McpStdioServerConfig
  | McpSSEServerConfig
  | McpHttpServerConfig
  | McpSdkServerConfigWithInstance;
```

#### `McpStdioServerConfig`

```typescript
type McpStdioServerConfig = {
  type?: 'stdio';
  command: string;
  args?: string[];
  env?: Record<string, string>;
}
```

#### `McpSSEServerConfig`

```typescript
type McpSSEServerConfig = {
  type: 'sse';
  url: string;
  headers?: Record<string, string>;
}
```

#### `McpHttpServerConfig`

```typescript
type McpHttpServerConfig = {
  type: 'http';
  url: string;
  headers?: Record<string, string>;
}
```

#### `McpSdkServerConfigWithInstance`

```typescript
type McpSdkServerConfigWithInstance = {
  type: 'sdk';
  name: string;
  instance: McpServer;
}
```

### `SdkPluginConfig`

SDK 中加载插件的配置。

```typescript
type SdkPluginConfig = {
  type: 'local';
  path: string;
}
```

| 字段 | 类型 | 描述 |
|:------|:-----|:------------|
| `type` | `'local'` | 必须为 `'local'`（目前仅支持本地插件） |
| `path` | `string` | 插件目录的绝对或相对路径 |

**示例：**
```typescript
plugins: [
  { type: 'local', path: './my-plugin' },
  { type: 'local', path: '/absolute/path/to/plugin' }
]
```

有关创建和使用插件的完整信息，请参见[插件](/docs/zh-CN/agent-sdk/plugins)。

## 消息类型

### `SDKMessage`

查询返回的所有可能消息的联合类型。

```typescript
type SDKMessage = 
  | SDKAssistantMessage
  | SDKUserMessage
  | SDKUserMessageReplay
  | SDKResultMessage
  | SDKSystemMessage
  | SDKPartialAssistantMessage
  | SDKCompactBoundaryMessage;
```

### `SDKAssistantMessage`

助手响应消息。

```typescript
type SDKAssistantMessage = {
  type: 'assistant';
  uuid: UUID;
  session_id: string;
  message: APIAssistantMessage; // 来自 Anthropic SDK
  parent_tool_use_id: string | null;
}
```

### `SDKUserMessage`

用户输入消息。

```typescript
type SDKUserMessage = {
  type: 'user';
  uuid?: UUID;
  session_id: string;
  message: APIUserMessage; // 来自 Anthropic SDK
  parent_tool_use_id: string | null;
}
```

### `SDKUserMessageReplay`

带有必需 UUID 的重放用户消息。

```typescript
type SDKUserMessageReplay = {
  type: 'user';
  uuid: UUID;
  session_id: string;
  message: APIUserMessage;
  parent_tool_use_id: string | null;
}
```

### `SDKResultMessage`

最终结果消息。

```typescript
type SDKResultMessage =
  | {
      type: 'result';
      subtype: 'success';
      uuid: UUID;
      session_id: string;
      duration_ms: number;
      duration_api_ms: number;
      is_error: boolean;
      num_turns: number;
      result: string;
      total_cost_usd: number;
      usage: NonNullableUsage;
      modelUsage: { [modelName: string]: ModelUsage };
      permission_denials: SDKPermissionDenial[];
      structured_output?: unknown;
    }
  | {
      type: 'result';
      subtype:
        | 'error_max_turns'
        | 'error_during_execution'
        | 'error_max_budget_usd'
        | 'error_max_structured_output_retries';
      uuid: UUID;
      session_id: string;
      duration_ms: number;
      duration_api_ms: number;
      is_error: boolean;
      num_turns: number;
      total_cost_usd: number;
      usage: NonNullableUsage;
      modelUsage: { [modelName: string]: ModelUsage };
      permission_denials: SDKPermissionDenial[];
      errors: string[];
    }
```

### `SDKSystemMessage`

系统初始化消息。

```typescript
type SDKSystemMessage = {
  type: 'system';
  subtype: 'init';
  uuid: UUID;
  session_id: string;
  apiKeySource: ApiKeySource;
  cwd: string;
  tools: string[];
  mcp_servers: {
    name: string;
    status: string;
  }[];
  model: string;
  permissionMode: PermissionMode;
  slash_commands: string[];
  output_style: string;
}
```

### `SDKPartialAssistantMessage`

流式部分消息（仅当 `includePartialMessages` 为 true 时）。

```typescript
type SDKPartialAssistantMessage = {
  type: 'stream_event';
  event: RawMessageStreamEvent; // 来自 Anthropic SDK
  parent_tool_use_id: string | null;
  uuid: UUID;
  session_id: string;
}
```

### `SDKCompactBoundaryMessage`

表示对话压缩边界的消息。

```typescript
type SDKCompactBoundaryMessage = {
  type: 'system';
  subtype: 'compact_boundary';
  uuid: UUID;
  session_id: string;
  compact_metadata: {
    trigger: 'manual' | 'auto';
    pre_tokens: number;
  };
}
```

### `SDKPermissionDenial`

关于被拒绝的工具使用的信息。

```typescript
type SDKPermissionDenial = {
  tool_name: string;
  tool_use_id: string;
  tool_input: ToolInput;
}
```

## 钩子类型

有关使用钩子的综合指南（包含示例和常见模式），请参见[钩子指南](/docs/zh-CN/agent-sdk/hooks)。

### `HookEvent`

可用的钩子事件。

```typescript
type HookEvent =
  | 'PreToolUse'
  | 'PostToolUse'
  | 'PostToolUseFailure'
  | 'Notification'
  | 'UserPromptSubmit'
  | 'SessionStart'
  | 'SessionEnd'
  | 'Stop'
  | 'SubagentStart'
  | 'SubagentStop'
  | 'PreCompact'
  | 'PermissionRequest';
```

### `HookCallback`

钩子回调函数类型。

```typescript
type HookCallback = (
  input: HookInput, // 所有钩子输入类型的联合
  toolUseID: string | undefined,
  options: { signal: AbortSignal }
) => Promise<HookJSONOutput>;
```

### `HookCallbackMatcher`

带有可选匹配器的钩子配置。

```typescript
interface HookCallbackMatcher {
  matcher?: string;
  hooks: HookCallback[];
}
```

### `HookInput`

所有钩子输入类型的联合类型。

```typescript
type HookInput =
  | PreToolUseHookInput
  | PostToolUseHookInput
  | PostToolUseFailureHookInput
  | NotificationHookInput
  | UserPromptSubmitHookInput
  | SessionStartHookInput
  | SessionEndHookInput
  | StopHookInput
  | SubagentStartHookInput
  | SubagentStopHookInput
  | PreCompactHookInput
  | PermissionRequestHookInput;
```

### `BaseHookInput`

所有钩子输入类型扩展的基础接口。

```typescript
type BaseHookInput = {
  session_id: string;
  transcript_path: string;
  cwd: string;
  permission_mode?: string;
}
```

#### `PreToolUseHookInput`

```typescript
type PreToolUseHookInput = BaseHookInput & {
  hook_event_name: 'PreToolUse';
  tool_name: string;
  tool_input: unknown;
}
```

#### `PostToolUseHookInput`

```typescript
type PostToolUseHookInput = BaseHookInput & {
  hook_event_name: 'PostToolUse';
  tool_name: string;
  tool_input: unknown;
  tool_response: unknown;
}
```

#### `PostToolUseFailureHookInput`

```typescript
type PostToolUseFailureHookInput = BaseHookInput & {
  hook_event_name: 'PostToolUseFailure';
  tool_name: string;
  tool_input: unknown;
  error: string;
  is_interrupt?: boolean;
}
```

#### `NotificationHookInput`

```typescript
type NotificationHookInput = BaseHookInput & {
  hook_event_name: 'Notification';
  message: string;
  title?: string;
}
```

#### `UserPromptSubmitHookInput`

```typescript
type UserPromptSubmitHookInput = BaseHookInput & {
  hook_event_name: 'UserPromptSubmit';
  prompt: string;
}
```

#### `SessionStartHookInput`

```typescript
type SessionStartHookInput = BaseHookInput & {
  hook_event_name: 'SessionStart';
  source: 'startup' | 'resume' | 'clear' | 'compact';
}
```

#### `SessionEndHookInput`

```typescript
type SessionEndHookInput = BaseHookInput & {
  hook_event_name: 'SessionEnd';
  reason: ExitReason;  // EXIT_REASONS 数组中的字符串
}
```

#### `StopHookInput`

```typescript
type StopHookInput = BaseHookInput & {
  hook_event_name: 'Stop';
  stop_hook_active: boolean;
}
```

#### `SubagentStartHookInput`

```typescript
type SubagentStartHookInput = BaseHookInput & {
  hook_event_name: 'SubagentStart';
  agent_id: string;
  agent_type: string;
}
```

#### `SubagentStopHookInput`

```typescript
type SubagentStopHookInput = BaseHookInput & {
  hook_event_name: 'SubagentStop';
  stop_hook_active: boolean;
}
```

#### `PreCompactHookInput`

```typescript
type PreCompactHookInput = BaseHookInput & {
  hook_event_name: 'PreCompact';
  trigger: 'manual' | 'auto';
  custom_instructions: string | null;
}
```

#### `PermissionRequestHookInput`

```typescript
type PermissionRequestHookInput = BaseHookInput & {
  hook_event_name: 'PermissionRequest';
  tool_name: string;
  tool_input: unknown;
  permission_suggestions?: PermissionUpdate[];
}
```

### `HookJSONOutput`

钩子返回值。

```typescript
type HookJSONOutput = AsyncHookJSONOutput | SyncHookJSONOutput;
```

#### `AsyncHookJSONOutput`

```typescript
type AsyncHookJSONOutput = {
  async: true;
  asyncTimeout?: number;
}
```

#### `SyncHookJSONOutput`

```typescript
type SyncHookJSONOutput = {
  continue?: boolean;
  suppressOutput?: boolean;
  stopReason?: string;
  decision?: 'approve' | 'block';
  systemMessage?: string;
  reason?: string;
  hookSpecificOutput?:
    | {
        hookEventName: 'PreToolUse';
        permissionDecision?: 'allow' | 'deny' | 'ask';
        permissionDecisionReason?: string;
        updatedInput?: Record<string, unknown>;
      }
    | {
        hookEventName: 'UserPromptSubmit';
        additionalContext?: string;
      }
    | {
        hookEventName: 'SessionStart';
        additionalContext?: string;
      }
    | {
        hookEventName: 'PostToolUse';
        additionalContext?: string;
      };
}
```

## 工具输入类型

所有内置 Claude Code 工具的输入 schema 文档。这些类型从 `@anthropic-ai/claude-agent-sdk` 导出，可用于类型安全的工具交互。

### `ToolInput`

**注意：** 这是一个仅用于文档说明的类型。它表示所有工具输入类型的联合。

```typescript
type ToolInput =
  | AgentInput
  | AskUserQuestionInput
  | BashInput
  | BashOutputInput
  | FileEditInput
  | FileReadInput
  | FileWriteInput
  | GlobInput
  | GrepInput
  | KillShellInput
  | NotebookEditInput
  | WebFetchInput
  | WebSearchInput
  | TodoWriteInput
  | ExitPlanModeInput
  | ListMcpResourcesInput
  | ReadMcpResourceInput;
```

### Task

**工具名称：** `Task`

```typescript
interface AgentInput {
  /**
   * 任务的简短描述（3-5 个词）
   */
  description: string;
  /**
   * 代理要执行的任务
   */
  prompt: string;
  /**
   * 用于此任务的专用代理类型
   */
  subagent_type: string;
}
```

启动新代理以自主处理复杂的多步骤任务。

### AskUserQuestion

**工具名称：** `AskUserQuestion`

```typescript
interface AskUserQuestionInput {
  /**
   * 要向用户提出的问题（1-4 个问题）
   */
  questions: Array<{
    /**
     * 要向用户提出的完整问题。应清晰、具体，
     * 并以问号结尾。
     */
    question: string;
    /**
     * 显示为标签/标记的非常简短的标签（最多 12 个字符）。
     * 示例："Auth method"、"Library"、"Approach"
     */
    header: string;
    /**
     * 可用选项（2-4 个选项）。系统会自动提供
     * "Other" 选项。
     */
    options: Array<{
      /**
       * 此选项的显示文本（1-5 个词）
       */
      label: string;
      /**
       * 此选项含义的说明
       */
      description: string;
    }>;
    /**
     * 设置为 true 以允许多选
     */
    multiSelect: boolean;
  }>;
  /**
   * 由权限系统填充的用户答案。
   * 将问题文本映射到选定的选项标签。
   * 多选答案以逗号分隔。
   */
  answers?: Record<string, string>;
}
```

在执行过程中向用户提出澄清问题。有关使用详情，请参见[处理审批和用户输入](/docs/zh-CN/agent-sdk/user-input#handle-clarifying-questions)。

### Bash

**工具名称：** `Bash`

```typescript
interface BashInput {
  /**
   * 要执行的命令
   */
  command: string;
  /**
   * 可选的超时时间（毫秒）（最大 600000）
   */
  timeout?: number;
  /**
   * 用 5-10 个词清晰简洁地描述此命令的作用
   */
  description?: string;
  /**
   * 设置为 true 以在后台运行此命令
   */
  run_in_background?: boolean;
}
```

在持久 shell 会话中执行 bash 命令，支持可选的超时和后台执行。

### BashOutput

**工具名称：** `BashOutput`

```typescript
interface BashOutputInput {
  /**
   * 要获取输出的后台 shell 的 ID
   */
  bash_id: string;
  /**
   * 可选的正则表达式用于过滤输出行
   */
  filter?: string;
}
```

从正在运行或已完成的后台 bash shell 中获取输出。

### Edit

**工具名称：** `Edit`

```typescript
interface FileEditInput {
  /**
   * 要修改的文件的绝对路径
   */
  file_path: string;
  /**
   * 要替换的文本
   */
  old_string: string;
  /**
   * 替换后的文本（必须与 old_string 不同）
   */
  new_string: string;
  /**
   * 替换所有出现的 old_string（默认 false）
   */
  replace_all?: boolean;
}
```

在文件中执行精确的字符串替换。

### Read

**工具名称：** `Read`

```typescript
interface FileReadInput {
  /**
   * 要读取的文件的绝对路径
   */
  file_path: string;
  /**
   * 开始读取的行号
   */
  offset?: number;
  /**
   * 要读取的行数
   */
  limit?: number;
}
```

从本地文件系统读取文件，包括文本、图片、PDF 和 Jupyter notebook。

### Write

**工具名称：** `Write`

```typescript
interface FileWriteInput {
  /**
   * 要写入的文件的绝对路径
   */
  file_path: string;
  /**
   * 要写入文件的内容
   */
  content: string;
}
```

将文件写入本地文件系统，如果文件已存在则覆盖。

### Glob

**工具名称：** `Glob`

```typescript
interface GlobInput {
  /**
   * 用于匹配文件的 glob 模式
   */
  pattern: string;
  /**
   * 要搜索的目录（默认为 cwd）
   */
  path?: string;
}
```

快速文件模式匹配，适用于任何规模的代码库。

### Grep

**工具名称：** `Grep`

```typescript
interface GrepInput {
  /**
   * 要搜索的正则表达式模式
   */
  pattern: string;
  /**
   * 要搜索的文件或目录（默认为 cwd）
   */
  path?: string;
  /**
   * 用于过滤文件的 glob 模式（例如 "*.js"）
   */
  glob?: string;
  /**
   * 要搜索的文件类型（例如 "js"、"py"、"rust"）
   */
  type?: string;
  /**
   * 输出模式："content"、"files_with_matches" 或 "count"
   */
  output_mode?: 'content' | 'files_with_matches' | 'count';
  /**
   * 不区分大小写搜索
   */
  '-i'?: boolean;
  /**
   * 显示行号（用于 content 模式）
   */
  '-n'?: boolean;
  /**
   * 每个匹配项之前显示的行数
   */
  '-B'?: number;
  /**
   * 每个匹配项之后显示的行数
   */
  '-A'?: number;
  /**
   * 每个匹配项前后显示的行数
   */
  '-C'?: number;
  /**
   * 将输出限制为前 N 行/条目
   */
  head_limit?: number;
  /**
   * 启用多行模式
   */
  multiline?: boolean;
}
```

基于 ripgrep 构建的强大搜索工具，支持正则表达式。

### KillBash

**工具名称：** `KillBash`

```typescript
interface KillShellInput {
  /**
   * 要终止的后台 shell 的 ID
   */
  shell_id: string;
}
```

通过 ID 终止正在运行的后台 bash shell。

### NotebookEdit

**工具名称：** `NotebookEdit`

```typescript
interface NotebookEditInput {
  /**
   * Jupyter notebook 文件的绝对路径
   */
  notebook_path: string;
  /**
   * 要编辑的单元格的 ID
   */
  cell_id?: string;
  /**
   * 单元格的新内容
   */
  new_source: string;
  /**
   * 单元格的类型（code 或 markdown）
   */
  cell_type?: 'code' | 'markdown';
  /**
   * 编辑类型（replace、insert、delete）
   */
  edit_mode?: 'replace' | 'insert' | 'delete';
}
```

编辑 Jupyter notebook 文件中的单元格。

### WebFetch

**工具名称：** `WebFetch`

```typescript
interface WebFetchInput {
  /**
   * 要获取内容的 URL
   */
  url: string;
  /**
   * 对获取的内容运行的提示
   */
  prompt: string;
}
```

从 URL 获取内容并使用 AI 模型进行处理。

### WebSearch

**工具名称：** `WebSearch`

```typescript
interface WebSearchInput {
  /**
   * 要使用的搜索查询
   */
  query: string;
  /**
   * 仅包含来自这些域名的结果
   */
  allowed_domains?: string[];
  /**
   * 永远不包含来自这些域名的结果
   */
  blocked_domains?: string[];
}
```

搜索网络并返回格式化的结果。

### TodoWrite

**工具名称：** `TodoWrite`

```typescript
interface TodoWriteInput {
  /**
   * 更新后的待办事项列表
   */
  todos: Array<{
    /**
     * 任务描述
     */
    content: string;
    /**
     * 任务状态
     */
    status: 'pending' | 'in_progress' | 'completed';
    /**
     * 任务描述的主动形式
     */
    activeForm: string;
  }>;
}
```

创建和管理结构化任务列表以跟踪进度。

### ExitPlanMode

**工具名称：** `ExitPlanMode`

```typescript
interface ExitPlanModeInput {
  /**
   * 供用户审批的计划
   */
  plan: string;
}
```

退出规划模式并提示用户审批计划。

### ListMcpResources

**工具名称：** `ListMcpResources`

```typescript
interface ListMcpResourcesInput {
  /**
   * 可选的服务器名称用于过滤资源
   */
  server?: string;
}
```

列出已连接服务器的可用 MCP 资源。

### ReadMcpResource

**工具名称：** `ReadMcpResource`

```typescript
interface ReadMcpResourceInput {
  /**
   * MCP 服务器名称
   */
  server: string;
  /**
   * 要读取的资源 URI
   */
  uri: string;
}
```

从服务器读取特定的 MCP 资源。

## 工具输出类型

所有内置 Claude Code 工具的输出 schema 文档。这些类型表示每个工具返回的实际响应数据。

### `ToolOutput`

**注意：** 这是一个仅用于文档说明的类型。它表示所有工具输出类型的联合。

```typescript
type ToolOutput =
  | TaskOutput
  | AskUserQuestionOutput
  | BashOutput
  | BashOutputToolOutput
  | EditOutput
  | ReadOutput
  | WriteOutput
  | GlobOutput
  | GrepOutput
  | KillBashOutput
  | NotebookEditOutput
  | WebFetchOutput
  | WebSearchOutput
  | TodoWriteOutput
  | ExitPlanModeOutput
  | ListMcpResourcesOutput
  | ReadMcpResourceOutput;
```

### Task

**工具名称：** `Task`

```typescript
interface TaskOutput {
  /**
   * 子代理的最终结果消息
   */
  result: string;
  /**
   * Token 使用统计
   */
  usage?: {
    input_tokens: number;
    output_tokens: number;
    cache_creation_input_tokens?: number;
    cache_read_input_tokens?: number;
  };
  /**
   * 总费用（美元）
   */
  total_cost_usd?: number;
  /**
   * 执行时长（毫秒）
   */
  duration_ms?: number;
}
```

返回子代理完成委托任务后的最终结果。

### AskUserQuestion

**工具名称：** `AskUserQuestion`

```typescript
interface AskUserQuestionOutput {
  /**
   * 提出的问题
   */
  questions: Array<{
    question: string;
    header: string;
    options: Array<{
      label: string;
      description: string;
    }>;
    multiSelect: boolean;
  }>;
  /**
   * 用户提供的答案。
   * 将问题文本映射到答案字符串。
   * 多选答案以逗号分隔。
   */
  answers: Record<string, string>;
}
```

返回提出的问题和用户的答案。

### Bash

**工具名称：** `Bash`

```typescript
interface BashOutput {
  /**
   * 合并的 stdout 和 stderr 输出
   */
  output: string;
  /**
   * 命令的退出码
   */
  exitCode: number;
  /**
   * 命令是否因超时被终止
   */
  killed?: boolean;
  /**
   * 后台进程的 Shell ID
   */
  shellId?: string;
}
```

返回带有退出状态的命令输出。后台命令会立即返回一个 shellId。

### BashOutput

**工具名称：** `BashOutput`

```typescript
interface BashOutputToolOutput {
  /**
   * 自上次检查以来的新输出
   */
  output: string;
  /**
   * 当前 shell 状态
   */
  status: 'running' | 'completed' | 'failed';
  /**
   * 退出码（完成时）
   */
  exitCode?: number;
}
```

返回后台 shell 的增量输出。

### Edit

**工具名称：** `Edit`

```typescript
interface EditOutput {
  /**
   * 确认消息
   */
  message: string;
  /**
   * 执行的替换次数
   */
  replacements: number;
  /**
   * 被编辑的文件路径
   */
  file_path: string;
}
```

返回成功编辑的确认信息及替换次数。

### Read

**工具名称：** `Read`

```typescript
type ReadOutput = 
  | TextFileOutput
  | ImageFileOutput
  | PDFFileOutput
  | NotebookFileOutput;

interface TextFileOutput {
  /**
   * 带行号的文件内容
   */
  content: string;
  /**
   * 文件中的总行数
   */
  total_lines: number;
  /**
   * 实际返回的行数
   */
  lines_returned: number;
}

interface ImageFileOutput {
  /**
   * Base64 编码的图像数据
   */
  image: string;
  /**
   * 图像 MIME 类型
   */
  mime_type: string;
  /**
   * 文件大小（字节）
   */
  file_size: number;
}

interface PDFFileOutput {
  /**
   * 页面内容数组
   */
  pages: Array<{
    page_number: number;
    text?: string;
    images?: Array<{
      image: string;
      mime_type: string;
    }>;
  }>;
  /**
   * 总页数
   */
  total_pages: number;
}

interface NotebookFileOutput {
  /**
   * Jupyter notebook 单元格
   */
  cells: Array<{
    cell_type: 'code' | 'markdown';
    source: string;
    outputs?: any[];
    execution_count?: number;
  }>;
  /**
   * Notebook 元数据
   */
  metadata?: Record<string, any>;
}
```

以适合文件类型的格式返回文件内容。

### Write

**工具名称：** `Write`

```typescript
interface WriteOutput {
  /**
   * 成功消息
   */
  message: string;
  /**
   * 写入的字节数
   */
  bytes_written: number;
  /**
   * 写入的文件路径
   */
  file_path: string;
}
```

成功写入文件后返回确认信息。

### Glob

**工具名称：** `Glob`

```typescript
interface GlobOutput {
  /**
   * 匹配的文件路径数组
   */
  matches: string[];
  /**
   * 找到的匹配数量
   */
  count: number;
  /**
   * 使用的搜索目录
   */
  search_path: string;
}
```

返回与 glob 模式匹配的文件路径，按修改时间排序。

### Grep

**工具名称：** `Grep`

```typescript
type GrepOutput = 
  | GrepContentOutput
  | GrepFilesOutput
  | GrepCountOutput;

interface GrepContentOutput {
  /**
   * 带上下文的匹配行
   */
  matches: Array<{
    file: string;
    line_number?: number;
    line: string;
    before_context?: string[];
    after_context?: string[];
  }>;
  /**
   * 匹配总数
   */
  total_matches: number;
}

interface GrepFilesOutput {
  /**
   * 包含匹配的文件
   */
  files: string[];
  /**
   * 包含匹配的文件数量
   */
  count: number;
}

interface GrepCountOutput {
  /**
   * 每个文件的匹配计数
   */
  counts: Array<{
    file: string;
    count: number;
  }>;
  /**
   * 所有文件的匹配总数
   */
  total: number;
}
```

以 output_mode 指定的格式返回搜索结果。

### KillBash

**工具名称：** `KillBash`

```typescript
interface KillBashOutput {
  /**
   * 成功消息
   */
  message: string;
  /**
   * 被终止的 shell 的 ID
   */
  shell_id: string;
}
```

终止后台 shell 后返回确认信息。

### NotebookEdit

**工具名称：** `NotebookEdit`

```typescript
interface NotebookEditOutput {
  /**
   * 成功消息
   */
  message: string;
  /**
   * 执行的编辑类型
   */
  edit_type: 'replaced' | 'inserted' | 'deleted';
  /**
   * 受影响的单元格 ID
   */
  cell_id?: string;
  /**
   * 编辑后 notebook 中的总单元格数
   */
  total_cells: number;
}
```

修改 Jupyter notebook 后返回确认信息。

### WebFetch

**工具名称：** `WebFetch`

```typescript
interface WebFetchOutput {
  /**
   * AI 模型对提示的响应
   */
  response: string;
  /**
   * 获取的 URL
   */
  url: string;
  /**
   * 重定向后的最终 URL
   */
  final_url?: string;
  /**
   * HTTP 状态码
   */
  status_code?: number;
}
```

返回 AI 对获取的网页内容的分析。

### WebSearch

**工具名称：** `WebSearch`

```typescript
interface WebSearchOutput {
  /**
   * 搜索结果
   */
  results: Array<{
    title: string;
    url: string;
    snippet: string;
    /**
     * 可用的附加元数据
     */
    metadata?: Record<string, any>;
  }>;
  /**
   * 结果总数
   */
  total_results: number;
  /**
   * 搜索的查询
   */
  query: string;
}
```

返回来自网络的格式化搜索结果。

### TodoWrite

**工具名称：** `TodoWrite`

```typescript
interface TodoWriteOutput {
  /**
   * 成功消息
   */
  message: string;
  /**
   * 当前待办事项统计
   */
  stats: {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
  };
}
```

返回确认信息及当前任务统计。

### ExitPlanMode

**工具名称：** `ExitPlanMode`

```typescript
interface ExitPlanModeOutput {
  /**
   * 确认消息
   */
  message: string;
  /**
   * 用户是否批准了计划
   */
  approved?: boolean;
}
```

退出计划模式后返回确认信息。

### ListMcpResources

**工具名称：** `ListMcpResources`

```typescript
interface ListMcpResourcesOutput {
  /**
   * 可用资源
   */
  resources: Array<{
    uri: string;
    name: string;
    description?: string;
    mimeType?: string;
    server: string;
  }>;
  /**
   * 资源总数
   */
  total: number;
}
```

返回可用 MCP 资源列表。

### ReadMcpResource

**工具名称：** `ReadMcpResource`

```typescript
interface ReadMcpResourceOutput {
  /**
   * 资源内容
   */
  contents: Array<{
    uri: string;
    mimeType?: string;
    text?: string;
    blob?: string;
  }>;
  /**
   * 提供资源的服务器
   */
  server: string;
}
```

返回请求的 MCP 资源的内容。

## 权限类型

### `PermissionUpdate`

更新权限的操作。

```typescript
type PermissionUpdate = 
  | {
      type: 'addRules';
      rules: PermissionRuleValue[];
      behavior: PermissionBehavior;
      destination: PermissionUpdateDestination;
    }
  | {
      type: 'replaceRules';
      rules: PermissionRuleValue[];
      behavior: PermissionBehavior;
      destination: PermissionUpdateDestination;
    }
  | {
      type: 'removeRules';
      rules: PermissionRuleValue[];
      behavior: PermissionBehavior;
      destination: PermissionUpdateDestination;
    }
  | {
      type: 'setMode';
      mode: PermissionMode;
      destination: PermissionUpdateDestination;
    }
  | {
      type: 'addDirectories';
      directories: string[];
      destination: PermissionUpdateDestination;
    }
  | {
      type: 'removeDirectories';
      directories: string[];
      destination: PermissionUpdateDestination;
    }
```

### `PermissionBehavior`

```typescript
type PermissionBehavior = 'allow' | 'deny' | 'ask';
```

### `PermissionUpdateDestination`

```typescript
type PermissionUpdateDestination = 
  | 'userSettings'     // 全局用户设置
  | 'projectSettings'  // 按目录的项目设置
  | 'localSettings'    // 被 gitignore 的本地设置
  | 'session'          // 仅当前会话
```

### `PermissionRuleValue`

```typescript
type PermissionRuleValue = {
  toolName: string;
  ruleContent?: string;
}
```

## 其他类型

### `ApiKeySource`

```typescript
type ApiKeySource = 'user' | 'project' | 'org' | 'temporary';
```

### `SdkBeta`

可通过 `betas` 选项启用的可用 Beta 功能。有关更多信息，请参阅 [Beta 头部](/docs/zh-CN/api/beta-headers)。

```typescript
type SdkBeta = 'context-1m-2025-08-07';
```

| 值 | 描述 | 兼容模型 |
|:------|:------------|:------------------|
| `'context-1m-2025-08-07'` | 启用 100 万 token [上下文窗口](/docs/zh-CN/build-with-claude/context-windows) | Claude Opus 4.6、Claude Sonnet 4.5、Claude Sonnet 4 |

### `SlashCommand`

关于可用斜杠命令的信息。

```typescript
type SlashCommand = {
  name: string;
  description: string;
  argumentHint: string;
}
```

### `ModelInfo`

关于可用模型的信息。

```typescript
type ModelInfo = {
  value: string;
  displayName: string;
  description: string;
}
```

### `McpServerStatus`

已连接 MCP 服务器的状态。

```typescript
type McpServerStatus = {
  name: string;
  status: 'connected' | 'failed' | 'needs-auth' | 'pending';
  serverInfo?: {
    name: string;
    version: string;
  };
}
```

### `AccountInfo`

已认证用户的账户信息。

```typescript
type AccountInfo = {
  email?: string;
  organization?: string;
  subscriptionType?: string;
  tokenSource?: string;
  apiKeySource?: string;
}
```

### `ModelUsage`

在结果消息中返回的每个模型的使用统计。

```typescript
type ModelUsage = {
  inputTokens: number;
  outputTokens: number;
  cacheReadInputTokens: number;
  cacheCreationInputTokens: number;
  webSearchRequests: number;
  costUSD: number;
  contextWindow: number;
}
```

### `ConfigScope`

```typescript
type ConfigScope = 'local' | 'user' | 'project';
```

### `NonNullableUsage`

[`Usage`](#usage) 的一个版本，所有可空字段都变为非空。

```typescript
type NonNullableUsage = {
  [K in keyof Usage]: NonNullable<Usage[K]>;
}
```

### `Usage`

Token 使用统计（来自 `@anthropic-ai/sdk`）。

```typescript
type Usage = {
  input_tokens: number | null;
  output_tokens: number | null;
  cache_creation_input_tokens?: number | null;
  cache_read_input_tokens?: number | null;
}
```

### `CallToolResult`

MCP 工具结果类型（来自 `@modelcontextprotocol/sdk/types.js`）。

```typescript
type CallToolResult = {
  content: Array<{
    type: 'text' | 'image' | 'resource';
    // 其他字段因类型而异
  }>;
  isError?: boolean;
}
```

### `AbortError`

用于中止操作的自定义错误类。

```typescript
class AbortError extends Error {}
```

## 沙箱配置

### `SandboxSettings`

沙箱行为的配置。使用此选项以编程方式启用命令沙箱并配置网络限制。

```typescript
type SandboxSettings = {
  enabled?: boolean;
  autoAllowBashIfSandboxed?: boolean;
  excludedCommands?: string[];
  allowUnsandboxedCommands?: boolean;
  network?: NetworkSandboxSettings;
  ignoreViolations?: SandboxIgnoreViolations;
  enableWeakerNestedSandbox?: boolean;
}
```

| 属性 | 类型 | 默认值 | 描述 |
| :------- | :--- | :------ | :---------- |
| `enabled` | `boolean` | `false` | 为命令执行启用沙箱模式 |
| `autoAllowBashIfSandboxed` | `boolean` | `false` | 启用沙箱时自动批准 bash 命令 |
| `excludedCommands` | `string[]` | `[]` | 始终绕过沙箱限制的命令（例如 `['docker']`）。这些命令自动在沙箱外运行，无需模型参与 |
| `allowUnsandboxedCommands` | `boolean` | `false` | 允许模型请求在沙箱外运行命令。当为 `true` 时，模型可以在工具输入中设置 `dangerouslyDisableSandbox`，这将回退到[权限系统](#permissions-fallback-for-unsandboxed-commands) |
| `network` | [`NetworkSandboxSettings`](#networksandboxsettings) | `undefined` | 网络特定的沙箱配置 |
| `ignoreViolations` | [`SandboxIgnoreViolations`](#sandboxignoreviolations) | `undefined` | 配置要忽略的沙箱违规 |
| `enableWeakerNestedSandbox` | `boolean` | `false` | 启用较弱的嵌套沙箱以提高兼容性 |

<Note>
**文件系统和网络访问限制**不通过沙箱设置配置。相反，它们源自[权限规则](https://code.claude.com/docs/zh-CN/settings#permission-settings)：

- **文件系统读取限制**：读取拒绝规则
- **文件系统写入限制**：编辑允许/拒绝规则
- **网络限制**：WebFetch 允许/拒绝规则

使用沙箱设置进行命令执行沙箱化，使用权限规则进行文件系统和网络访问控制。
</Note>

#### 使用示例

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const result = await query({
  prompt: "Build and test my project",
  options: {
    sandbox: {
      enabled: true,
      autoAllowBashIfSandboxed: true,
      network: {
        allowLocalBinding: true
      }
    }
  }
});
```

<Warning>
**Unix 套接字安全**：`allowUnixSockets` 选项可以授予对强大系统服务的访问权限。例如，允许 `/var/run/docker.sock` 实际上通过 Docker API 授予了完整的主机系统访问权限，绕过了沙箱隔离。仅允许严格必要的 Unix 套接字，并了解每个套接字的安全影响。
</Warning>

### `NetworkSandboxSettings`

沙箱模式的网络特定配置。

```typescript
type NetworkSandboxSettings = {
  allowLocalBinding?: boolean;
  allowUnixSockets?: string[];
  allowAllUnixSockets?: boolean;
  httpProxyPort?: number;
  socksProxyPort?: number;
}
```

| 属性 | 类型 | 默认值 | 描述 |
| :------- | :--- | :------ | :---------- |
| `allowLocalBinding` | `boolean` | `false` | 允许进程绑定到本地端口（例如用于开发服务器） |
| `allowUnixSockets` | `string[]` | `[]` | 进程可以访问的 Unix 套接字路径（例如 Docker 套接字） |
| `allowAllUnixSockets` | `boolean` | `false` | 允许访问所有 Unix 套接字 |
| `httpProxyPort` | `number` | `undefined` | 用于网络请求的 HTTP 代理端口 |
| `socksProxyPort` | `number` | `undefined` | 用于网络请求的 SOCKS 代理端口 |

### `SandboxIgnoreViolations`

忽略特定沙箱违规的配置。

```typescript
type SandboxIgnoreViolations = {
  file?: string[];
  network?: string[];
}
```

| 属性 | 类型 | 默认值 | 描述 |
| :------- | :--- | :------ | :---------- |
| `file` | `string[]` | `[]` | 要忽略违规的文件路径模式 |
| `network` | `string[]` | `[]` | 要忽略违规的网络模式 |

### 非沙箱命令的权限回退

当启用 `allowUnsandboxedCommands` 时，模型可以通过在工具输入中设置 `dangerouslyDisableSandbox: true` 来请求在沙箱外运行命令。这些请求会回退到现有的权限系统，这意味着您的 `canUseTool` 处理程序将被调用，允许您实现自定义授权逻辑。

<Note>
**`excludedCommands` 与 `allowUnsandboxedCommands`：**
- `excludedCommands`：始终自动绕过沙箱的静态命令列表（例如 `['docker']`）。模型对此没有控制权。
- `allowUnsandboxedCommands`：让模型在运行时通过在工具输入中设置 `dangerouslyDisableSandbox: true` 来决定是否请求非沙箱执行。
</Note>

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

const result = await query({
  prompt: "Deploy my application",
  options: {
    sandbox: {
      enabled: true,
      allowUnsandboxedCommands: true  // 模型可以请求非沙箱执行
    },
    permissionMode: "default",
    canUseTool: async (tool, input) => {
      // 检查模型是否请求绕过沙箱
      if (tool === "Bash" && input.dangerouslyDisableSandbox) {
        // 模型想要在沙箱外运行此命令
        console.log(`Unsandboxed command requested: ${input.command}`);

        // 返回 true 允许，false 拒绝
        return isCommandAuthorized(input.command);
      }
      return true;
    }
  }
});
```

此模式使您能够：

- **审计模型请求**：记录模型何时请求非沙箱执行
- **实现允许列表**：仅允许特定命令在非沙箱环境中运行
- **添加审批工作流**：要求对特权操作进行明确授权

<Warning>
使用 `dangerouslyDisableSandbox: true` 运行的命令具有完整的系统访问权限。确保您的 `canUseTool` 处理程序仔细验证这些请求。

如果 `permissionMode` 设置为 `bypassPermissions` 且 `allowUnsandboxedCommands` 已启用，模型可以在没有任何审批提示的情况下自主在沙箱外执行命令。这种组合实际上允许模型静默地逃脱沙箱隔离。
</Warning>

## 另请参阅

- [SDK 概述](/docs/zh-CN/agent-sdk/overview) - 通用 SDK 概念
- [Python SDK 参考](/docs/zh-CN/agent-sdk/python) - Python SDK 文档
- [CLI 参考](https://code.claude.com/docs/zh-CN/cli-reference) - 命令行界面
- [常见工作流](https://code.claude.com/docs/zh-CN/common-workflows) - 分步指南