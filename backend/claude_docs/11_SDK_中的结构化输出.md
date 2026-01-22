# SDK 中的结构化输出

从代理工作流获取经过验证的 JSON 结果

从代理工作流获取结构化的、经过验证的 JSON。Agent SDK 通过 JSON Schemas 支持结构化输出，确保您的代理以您需要的确切格式返回数据。

**何时使用结构化输出**

当您需要在代理完成包含工具的多轮工作流(文件搜索、命令执行、网络研究等)后获得经过验证的 JSON 时，请使用结构化输出。

对于不使用工具的单个 API 调用，请参阅 API 结构化输出。

## 为什么使用结构化输出

结构化输出为您的应用程序提供可靠的、类型安全的集成：

- **经过验证的结构**：始终接收与您的架构匹配的有效 JSON
- **简化集成**：无需解析或验证代码
- **类型安全**：与 TypeScript 或 Python 类型提示一起使用以实现端到端安全
- **清晰分离**：将输出要求与任务说明分开定义
- **工具自主性**：代理选择使用哪些工具，同时保证输出格式

## 结构化输出如何工作

1. **定义您的 JSON 架构**

   创建一个 JSON Schema，描述您希望代理返回的结构。该架构使用标准 JSON Schema 格式。

2. **添加 outputFormat 参数**

   在您的查询选项中包含 `outputFormat` 参数，其中 `type: "json_schema"` 和您的架构定义。

3. **运行您的查询**

   代理使用完成任务所需的任何工具(文件操作、命令、网络搜索等)。

4. **访问经过验证的输出**

   代理的最终结果将是与您的架构匹配的有效 JSON，可在 `message.structured_output` 中获得。

## 支持的 JSON Schema 功能

Agent SDK 支持与 API 结构化输出 相同的 JSON Schema 功能和限制。

主要支持的功能：

- 所有基本类型：object、array、string、integer、number、boolean、null
- `enum`、`const`、`required`、`additionalProperties`(必须为 `false`)
- 字符串格式：`date-time`、`date`、`email`、`uri`、`uuid` 等
- `$ref`、`$def` 和 `definitions`

有关支持的功能、限制和正则表达式模式支持的完整详细信息，请参阅 API 文档中的 JSON Schema 限制。

## 示例：TODO 跟踪代理

这是一个完整的示例，展示了一个代理搜索代码中的 TODO 并提取 git blame 信息：

```typescript
import { query } from '@anthropic-ai/claude-agent-sdk'

// 定义 TODO 提取的结构
const todoSchema = {
  type: 'object',
  properties: {
    todos: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          text: { type: 'string' },
          file: { type: 'string' },
          line: { type: 'number' },
          author: { type: 'string' },
          date: { type: 'string' }
        },
        required: ['text', 'file', 'line']
      }
    },
    total_count: { type: 'number' }
  },
  required: ['todos', 'total_count']
}

// 代理使用 Grep 查找 TODO，使用 Bash 获取 git blame 信息
for await (const message of query({
  prompt: 'Find all TODO comments in src/ and identify who added them',
  options: {
    outputFormat: {
      type: 'json_schema',
      schema: todoSchema
    }
  }
})) {
  if (message.type === 'result' && message.structured_output) {
    const data = message.structured_output
    console.log(`Found ${data.total_count} TODOs`)
    data.todos.forEach(todo => {
      console.log(`${todo.file}:${todo.line} - ${todo.text}`)
      if (todo.author) {
        console.log(`  Added by ${todo.author} on ${todo.date}`)
      }
    })
  }
}
```

代理自主使用正确的工具(Grep、Bash)来收集信息并返回经过验证的数据。

## 错误处理

如果代理无法生成与您的架构匹配的有效输出，您将收到一个错误结果：

```typescript
for await (const msg of query({
  prompt: 'Analyze the data',
  options: {
    outputFormat: {
      type: 'json_schema',
      schema: mySchema
    }
  }
})) {
  if (msg.type === 'result') {
    if (msg.subtype === 'success' && msg.structured_output) {
      console.log(msg.structured_output)
    } else if (msg.subtype === 'error_max_structured_output_retries') {
      console.error('Could not produce valid output')
    }
  }
}
```

## 相关资源

- JSON Schema 文档
- API 结构化输出 - 用于单个 API 调用
- 自定义工具 - 为您的代理定义工具
- TypeScript SDK 参考 - 完整的 TypeScript API
- Python SDK 参考 - 完整的 Python API
