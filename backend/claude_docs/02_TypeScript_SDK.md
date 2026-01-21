# Agent SDK 参考 - TypeScript

TypeScript Agent SDK 的完整 API 参考，包括所有函数、类型和接口。

## 安装

```bash
npm install @anthropic-ai/claude-agent-sdk
```

## 函数

### `query()`

与 Claude Code 交互的主要函数。创建一个异步生成器，在消息到达时流式传输消息。

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
| --- | --- | --- |
| `prompt` | `string \| AsyncIterable<SDKUserMessage>` | 输入提示，可以是字符串或用于流式模式的异步可迭代对象 |
| `options` | `Options` | 可选配置对象 |

#### 返回值

返回一个 `Query` 对象，它扩展了 `AsyncGenerator<SDKMessage, void>` 并具有额外的方法。

### `tool()`

创建一个类型安全的 MCP 工具定义，用于 SDK MCP 服务器。

```typescript
function tool<Schema extends ZodRawShape>(
  name: string,
  description: string,
  inputSchema: Schema,
  handler: (args: z.infer<ZodObject<Schema>>, extra: unknown) => Promise<CallToolResult>
): SdkMcpToolDefinition<Schema>
```

### `createSdkMcpServer()`

创建一个在与应用程序相同进程中运行的 MCP 服务器实例。

```typescript
function createSdkMcpServer(options: {
  name: string;
  version?: string;
  tools?: Array<SdkMcpToolDefinition<any>>;
}): McpSdkServerConfigWithInstance
```

## 类型

### `Options`

`query()` 函数的配置对象。

| 属性 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `allowedTools` | `string[]` | 所有工具 | 允许的工具名称列表 |
| `systemPrompt` | `string \| { type: 'preset'; preset: 'claude_code'; append?: string }` | `undefined` | 系统提示配置 |
| `mcpServers` | `Record<string, McpServerConfig>` | `{}` | MCP 服务器配置 |
| `permissionMode` | `PermissionMode` | `'default'` | 会话的权限模式 |
| `continue` | `boolean` | `false` | 继续最近的对话 |
| `resume` | `string` | `undefined` | 要恢复的会话 ID |
| `maxTurns` | `number` | `undefined` | 最大对话轮数 |
| `model` | `string` | CLI 默认值 | 要使用的 Claude 模型 |
| `agents` | `Record<string, AgentDefinition>` | `undefined` | 以编程方式定义子代理 |
| `settingSources` | `SettingSource[]` | `[]` | 控制要加载哪些文件系统设置 |

### `AgentDefinition`

以编程方式定义的子代理的配置。

```typescript
type AgentDefinition = {
  description: string;
  tools?: string[];
  prompt: string;
  model?: 'sonnet' | 'opus' | 'haiku' | 'inherit';
}
```

### `PermissionMode`

```typescript
type PermissionMode =
  | 'default'           // 标准权限行为
  | 'acceptEdits'       // 自动接受文件编辑
  | 'bypassPermissions' // 绕过所有权限检查
  | 'plan'              // 规划模式 - 无执行
```

## 工具输入类型

### `Bash`

```typescript
interface BashInput {
  command: string;
  timeout?: number;
  description?: string;
  run_in_background?: boolean;
}
```

### `Read`

```typescript
interface FileReadInput {
  file_path: string;
  offset?: number;
  limit?: number;
}
```

### `Write`

```typescript
interface FileWriteInput {
  file_path: string;
  content: string;
}
```

### `Edit`

```typescript
interface FileEditInput {
  file_path: string;
  old_string: string;
  new_string: string;
  replace_all?: boolean;
}
```

### `Grep`

```typescript
interface GrepInput {
  pattern: string;
  path?: string;
  glob?: string;
  type?: string;
  output_mode?: 'content' | 'files_with_matches' | 'count';
  '-i'?: boolean;
  '-n'?: boolean;
}
```

### `Glob`

```typescript
interface GlobInput {
  pattern: string;
  path?: string;
}
```

## 消息类型

### `SDKMessage`

所有可能消息的联合类型。

```typescript
type SDKMessage =
  | SDKAssistantMessage
  | SDKUserMessage
  | SDKResultMessage
  | SDKSystemMessage;
```

### `SDKAssistantMessage`

助手响应消息。

```typescript
type SDKAssistantMessage = {
  type: 'assistant';
  uuid: UUID;
  session_id: string;
  message: APIAssistantMessage;
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
      result: string;
      total_cost_usd: number;
      usage: Usage;
    }
  | {
      type: 'result';
      subtype: 'error_max_turns' | 'error_during_execution';
    };
```

## 完整文档

有关完整的API文档，请参阅官方TypeScript SDK参考文档。
