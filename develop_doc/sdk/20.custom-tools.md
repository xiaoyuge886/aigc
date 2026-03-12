# 自定义工具

构建和集成自定义工具以扩展 Claude Agent SDK 功能

---

自定义工具允许您通过进程内 MCP 服务器使用自己的功能扩展 Claude Code 的能力，使 Claude 能够与外部服务、API 交互或执行专门的操作。

## 创建自定义工具

使用 `createSdkMcpServer` 和 `tool` 辅助函数来定义类型安全的自定义工具：

<CodeGroup>

```typescript TypeScript
import { query, tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

// 创建一个带有自定义工具的 SDK MCP 服务器
const customServer = createSdkMcpServer({
  name: "my-custom-tools",
  version: "1.0.0",
  tools: [
    tool(
      "get_weather",
      "使用坐标获取某个位置的当前温度",
      {
        latitude: z.number().describe("纬度坐标"),
        longitude: z.number().describe("经度坐标")
      },
      async (args) => {
        const response = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${args.latitude}&longitude=${args.longitude}&current=temperature_2m&temperature_unit=fahrenheit`);
        const data = await response.json();

        return {
          content: [{
            type: "text",
            text: `温度：${data.current.temperature_2m}°F`
          }]
        };
      }
    )
  ]
});
```

```python Python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeSDKClient, ClaudeAgentOptions
from typing import Any
import aiohttp

# 使用 @tool 装饰器定义自定义工具
@tool("get_weather", "使用坐标获取某个位置的当前温度", {"latitude": float, "longitude": float})
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
    # 调用天气 API
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={args['latitude']}&longitude={args['longitude']}&current=temperature_2m&temperature_unit=fahrenheit"
        ) as response:
            data = await response.json()

    return {
        "content": [{
            "type": "text",
            "text": f"温度：{data['current']['temperature_2m']}°F"
        }]
    }

# 使用自定义工具创建 SDK MCP 服务器
custom_server = create_sdk_mcp_server(
    name="my-custom-tools",
    version="1.0.0",
    tools=[get_weather]  # 传递装饰过的函数
)
```

</CodeGroup>

## 使用自定义工具

通过 `mcpServers` 选项将自定义服务器作为字典/对象传递给 `query` 函数。

<Note>
**重要：** 自定义 MCP 工具需要流式输入模式。您必须为 `prompt` 参数使用异步生成器/可迭代对象 - 简单字符串无法与 MCP 服务器一起使用。
</Note>

### 工具名称格式

当 MCP 工具暴露给 Claude 时，它们的名称遵循特定格式：
- 模式：`mcp__{server_name}__{tool_name}`
- 示例：服务器 `my-custom-tools` 中名为 `get_weather` 的工具变成 `mcp__my-custom-tools__get_weather`

### 配置允许的工具

您可以通过 `allowedTools` 选项控制 Claude 可以使用哪些工具：

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 在查询中使用自定义工具和流式输入
async function* generateMessages() {
  yield {
    type: "user" as const,
    message: {
      role: "user" as const,
      content: "旧金山的天气怎么样？"
    }
  };
}

for await (const message of query({
  prompt: generateMessages(),  // 使用异步生成器进行流式输入
  options: {
    mcpServers: {
      "my-custom-tools": customServer  // 作为对象/字典传递，而不是数组
    },
    // 可选择指定 Claude 可以使用哪些工具
    allowedTools: [
      "mcp__my-custom-tools__get_weather",  // 允许天气工具
      // 根据需要添加其他工具
    ],
    maxTurns: 3
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

```python Python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

# 使用自定义工具与 Claude
options = ClaudeAgentOptions(
    mcp_servers={"my-custom-tools": custom_server},
    allowed_tools=[
        "mcp__my-custom-tools__get_weather",  # 允许天气工具
        # 根据需要添加其他工具
    ]
)

async def main():
    async with ClaudeSDKClient(options=options) as client:
        await client.query("旧金山的天气怎么样？")

        # 提取并打印响应
        async for msg in client.receive_response():
            print(msg)

asyncio.run(main())
```

</CodeGroup>

### 多工具示例

当您的 MCP 服务器有多个工具时，您可以有选择地允许它们：

<CodeGroup>

```typescript TypeScript
const multiToolServer = createSdkMcpServer({
  name: "utilities",
  version: "1.0.0",
  tools: [
    tool("calculate", "执行计算", { /* ... */ }, async (args) => { /* ... */ }),
    tool("translate", "翻译文本", { /* ... */ }, async (args) => { /* ... */ }),
    tool("search_web", "搜索网络", { /* ... */ }, async (args) => { /* ... */ })
  ]
});

// 仅允许特定工具和流式输入
async function* generateMessages() {
  yield {
    type: "user" as const,
    message: {
      role: "user" as const,
      content: "计算 5 + 3 并将 'hello' 翻译成西班牙语"
    }
  };
}

for await (const message of query({
  prompt: generateMessages(),  // 使用异步生成器进行流式输入
  options: {
    mcpServers: {
      utilities: multiToolServer
    },
    allowedTools: [
      "mcp__utilities__calculate",   // 允许计算器
      "mcp__utilities__translate",   // 允许翻译器
      // "mcp__utilities__search_web" 不被允许
    ]
  }
})) {
  // 处理消息
}
```

```python Python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool, create_sdk_mcp_server
from typing import Any
import asyncio

# 使用 @tool 装饰器定义多个工具
@tool("calculate", "执行计算", {"expression": str})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    result = eval(args["expression"])  # 在生产环境中使用安全的 eval
    return {"content": [{"type": "text", "text": f"结果：{result}"}]}

@tool("translate", "翻译文本", {"text": str, "target_lang": str})
async def translate(args: dict[str, Any]) -> dict[str, Any]:
    # 翻译逻辑在这里
    return {"content": [{"type": "text", "text": f"翻译：{args['text']}"}]}

@tool("search_web", "搜索网络", {"query": str})
async def search_web(args: dict[str, Any]) -> dict[str, Any]:
    # 搜索逻辑在这里
    return {"content": [{"type": "text", "text": f"搜索结果：{args['query']}"}]}

multi_tool_server = create_sdk_mcp_server(
    name="utilities",
    version="1.0.0",
    tools=[calculate, translate, search_web]  # 传递装饰过的函数
)

# 仅允许特定工具和流式输入
async def message_generator():
    yield {
        "type": "user",
        "message": {
            "role": "user",
            "content": "计算 5 + 3 并将 'hello' 翻译成西班牙语"
        }
    }

async for message in query(
    prompt=message_generator(),  # 使用异步生成器进行流式输入
    options=ClaudeAgentOptions(
        mcp_servers={"utilities": multi_tool_server},
        allowed_tools=[
            "mcp__utilities__calculate",   # 允许计算器
            "mcp__utilities__translate",   # 允许翻译器
            # "mcp__utilities__search_web" 不被允许
        ]
    )
):
    if hasattr(message, 'result'):
        print(message.result)
```

</CodeGroup>

## Python 的类型安全

`@tool` 装饰器支持各种模式定义方法以实现类型安全：

<CodeGroup>

```typescript TypeScript
import { z } from "zod";

tool(
  "process_data",
  "使用类型安全处理结构化数据",
  {
    // Zod 模式定义运行时验证和 TypeScript 类型
    data: z.object({
      name: z.string(),
      age: z.number().min(0).max(150),
      email: z.string().email(),
      preferences: z.array(z.string()).optional()
    }),
    format: z.enum(["json", "csv", "xml"]).default("json")
  },
  async (args) => {
    // args 基于模式完全类型化
    // TypeScript 知道：args.data.name 是字符串，args.data.age 是数字等
    console.log(`正在将 ${args.data.name} 的数据处理为 ${args.format}`);
    
    // 您的处理逻辑在这里
    return {
      content: [{
        type: "text",
        text: `已处理 ${args.data.name} 的数据`
      }]
    };
  }
)
```

```python Python
from typing import Any

# 简单类型映射 - 推荐用于大多数情况
@tool(
    "process_data",
    "使用类型安全处理结构化数据",
    {
        "name": str,
        "age": int,
        "email": str,
        "preferences": list  # 可选参数可以在函数中处理
    }
)
async def process_data(args: dict[str, Any]) -> dict[str, Any]:
    # 使用类型提示访问参数以获得 IDE 支持
    name = args["name"]
    age = args["age"]
    email = args["email"]
    preferences = args.get("preferences", [])
    
    print(f"正在处理 {name} 的数据（年龄：{age}）")
    
    return {
        "content": [{
            "type": "text",
            "text": f"已处理 {name} 的数据"
        }]
    }

# 对于更复杂的模式，您可以使用 JSON Schema 格式
@tool(
    "advanced_process",
    "使用高级验证处理数据",
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0, "maximum": 150},
            "email": {"type": "string", "format": "email"},
            "format": {"type": "string", "enum": ["json", "csv", "xml"], "default": "json"}
        },
        "required": ["name", "age", "email"]
    }
)
async def advanced_process(args: dict[str, Any]) -> dict[str, Any]:
    # 使用高级模式验证进行处理
    return {
        "content": [{
            "type": "text",
            "text": f"为 {args['name']} 进行高级处理"
        }]
    }
```

</CodeGroup>

## 错误处理

优雅地处理错误以提供有意义的反馈：

<CodeGroup>

```typescript TypeScript
tool(
  "fetch_data",
  "从 API 获取数据",
  {
    endpoint: z.string().url().describe("API 端点 URL")
  },
  async (args) => {
    try {
      const response = await fetch(args.endpoint);
      
      if (!response.ok) {
        return {
          content: [{
            type: "text",
            text: `API 错误：${response.status} ${response.statusText}`
          }]
        };
      }
      
      const data = await response.json();
      return {
        content: [{
          type: "text",
          text: JSON.stringify(data, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: "text",
          text: `获取数据失败：${error.message}`
        }]
      };
    }
  }
)
```

```python Python
import json
import aiohttp
from typing import Any

@tool(
    "fetch_data",
    "从 API 获取数据",
    {"endpoint": str}  # 简单模式
)
async def fetch_data(args: dict[str, Any]) -> dict[str, Any]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(args["endpoint"]) as response:
                if response.status != 200:
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"API 错误：{response.status} {response.reason}"
                        }]
                    }
                
                data = await response.json()
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(data, indent=2)
                    }]
                }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"获取数据失败：{str(e)}"
            }]
        }
```

</CodeGroup>

## 示例工具

### 数据库查询工具

<CodeGroup>

```typescript TypeScript
const databaseServer = createSdkMcpServer({
  name: "database-tools",
  version: "1.0.0",
  tools: [
    tool(
      "query_database",
      "执行数据库查询",
      {
        query: z.string().describe("要执行的 SQL 查询"),
        params: z.array(z.any()).optional().describe("查询参数")
      },
      async (args) => {
        const results = await db.query(args.query, args.params || []);
        return {
          content: [{
            type: "text",
            text: `找到 ${results.length} 行：\n${JSON.stringify(results, null, 2)}`
          }]
        };
      }
    )
  ]
});
```

```python Python
from typing import Any
import json

@tool(
    "query_database",
    "执行数据库查询",
    {"query": str, "params": list}  # 带有列表类型的简单模式
)
async def query_database(args: dict[str, Any]) -> dict[str, Any]:
    results = await db.query(args["query"], args.get("params", []))
    return {
        "content": [{
            "type": "text",
            "text": f"找到 {len(results)} 行：\n{json.dumps(results, indent=2)}"
        }]
    }

database_server = create_sdk_mcp_server(
    name="database-tools",
    version="1.0.0",
    tools=[query_database]  # 传递装饰过的函数
)
```

</CodeGroup>

### API 网关工具

<CodeGroup>

```typescript TypeScript
const apiGatewayServer = createSdkMcpServer({
  name: "api-gateway",
  version: "1.0.0",
  tools: [
    tool(
      "api_request",
      "向外部服务发出经过身份验证的 API 请求",
      {
        service: z.enum(["stripe", "github", "openai", "slack"]).describe("要调用的服务"),
        endpoint: z.string().describe("API 端点路径"),
        method: z.enum(["GET", "POST", "PUT", "DELETE"]).describe("HTTP 方法"),
        body: z.record(z.any()).optional().describe("请求体"),
        query: z.record(z.string()).optional().describe("查询参数")
      },
      async (args) => {
        const config = {
          stripe: { baseUrl: "https://api.stripe.com/v1", key: process.env.STRIPE_KEY },
          github: { baseUrl: "https://api.github.com", key: process.env.GITHUB_TOKEN },
          openai: { baseUrl: "https://api.openai.com/v1", key: process.env.OPENAI_KEY },
          slack: { baseUrl: "https://slack.com/api", key: process.env.SLACK_TOKEN }
        };
        
        const { baseUrl, key } = config[args.service];
        const url = new URL(`${baseUrl}${args.endpoint}`);
        
        if (args.query) {
          Object.entries(args.query).forEach(([k, v]) => url.searchParams.set(k, v));
        }
        
        const response = await fetch(url, {
          method: args.method,
          headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
          body: args.body ? JSON.stringify(args.body) : undefined
        });
        
        const data = await response.json();
        return {
          content: [{
            type: "text",
            text: JSON.stringify(data, null, 2)
          }]
        };
      }
    )
  ]
});
```

```python Python
import os
import json
import aiohttp
from typing import Any

# 对于带有枚举的复杂模式，使用 JSON Schema 格式
@tool(
    "api_request",
    "向外部服务发出经过身份验证的 API 请求",
    {
        "type": "object",
        "properties": {
            "service": {"type": "string", "enum": ["stripe", "github", "openai", "slack"]},
            "endpoint": {"type": "string"},
            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
            "body": {"type": "object"},
            "query": {"type": "object"}
        },
        "required": ["service", "endpoint", "method"]
    }
)
async def api_request(args: dict[str, Any]) -> dict[str, Any]:
    config = {
        "stripe": {"base_url": "https://api.stripe.com/v1", "key": os.environ["STRIPE_KEY"]},
        "github": {"base_url": "https://api.github.com", "key": os.environ["GITHUB_TOKEN"]},
        "openai": {"base_url": "https://api.openai.com/v1", "key": os.environ["OPENAI_KEY"]},
        "slack": {"base_url": "https://slack.com/api", "key": os.environ["SLACK_TOKEN"]}
    }
    
    service_config = config[args["service"]]
    url = f"{service_config['base_url']}{args['endpoint']}"
    
    if args.get("query"):
        params = "&".join([f"{k}={v}" for k, v in args["query"].items()])
        url += f"?{params}"
    
    headers = {"Authorization": f"Bearer {service_config['key']}", "Content-Type": "application/json"}
    
    async with aiohttp.ClientSession() as session:
        async with session.request(
            args["method"], url, headers=headers, json=args.get("body")
        ) as response:
            data = await response.json()
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(data, indent=2)
                }]
            }

api_gateway_server = create_sdk_mcp_server(
    name="api-gateway",
    version="1.0.0",
    tools=[api_request]  # 传递装饰过的函数
)
```

</CodeGroup>

### 计算器工具

<CodeGroup>

```typescript TypeScript
const calculatorServer = createSdkMcpServer({
  name: "calculator",
  version: "1.0.0",
  tools: [
    tool(
      "calculate",
      "执行数学计算",
      {
        expression: z.string().describe("要计算的数学表达式"),
        precision: z.number().optional().default(2).describe("小数精度")
      },
      async (args) => {
        try {
          // 在生产环境中使用安全的数学计算库
          const result = eval(args.expression); // 仅作示例！
          const formatted = Number(result).toFixed(args.precision);
          
          return {
            content: [{
              type: "text",
              text: `${args.expression} = ${formatted}`
            }]
          };
        } catch (error) {
          return {
            content: [{
              type: "text",
              text: `错误：无效表达式 - ${error.message}`
            }]
          };
        }
      }
    ),
    tool(
      "compound_interest",
      "计算投资的复利",
      {
        principal: z.number().positive().describe("初始投资金额"),
        rate: z.number().describe("年利率（作为小数，例如 0.05 表示 5%）"),
        time: z.number().positive().describe("投资期限（年）"),
        n: z.number().positive().default(12).describe("每年复利频率")
      },
      async (args) => {
        const amount = args.principal * Math.pow(1 + args.rate / args.n, args.n * args.time);
        const interest = amount - args.principal;
        
        return {
          content: [{
            type: "text",
            text: `投资分析：\n` +
                  `本金：$${args.principal.toFixed(2)}\n` +
                  `利率：${(args.rate * 100).toFixed(2)}%\n` +
                  `时间：${args.time} 年\n` +
                  `复利：每年 ${args.n} 次\n\n` +
                  `最终金额：$${amount.toFixed(2)}\n` +
                  `赚取利息：$${interest.toFixed(2)}\n` +
                  `回报：${((interest / args.principal) * 100).toFixed(2)}%`
          }]
        };
      }
    )
  ]
});
```

```python Python
import math
from typing import Any

@tool(
    "calculate",
    "执行数学计算",
    {"expression": str, "precision": int}  # 简单模式
)
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    try:
        # 在生产环境中使用安全的数学计算库
        result = eval(args["expression"], {"__builtins__": {}})
        precision = args.get("precision", 2)
        formatted = round(result, precision)
        
        return {
            "content": [{
                "type": "text",
                "text": f"{args['expression']} = {formatted}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"错误：无效表达式 - {str(e)}"
            }]
        }

@tool(
    "compound_interest",
    "计算投资的复利",
    {"principal": float, "rate": float, "time": float, "n": int}
)
async def compound_interest(args: dict[str, Any]) -> dict[str, Any]:
    principal = args["principal"]
    rate = args["rate"]
    time = args["time"]
    n = args.get("n", 12)
    
    amount = principal * (1 + rate / n) ** (n * time)
    interest = amount - principal
    
    return {
        "content": [{
            "type": "text",
            "text": f"""投资分析：
本金：${principal:.2f}
利率：{rate * 100:.2f}%
时间：{time} 年
复利：每年 {n} 次

最终金额：${amount:.2f}
赚取利息：${interest:.2f}
回报：{(interest / principal) * 100:.2f}%"""
        }]
    }

calculator_server = create_sdk_mcp_server(
    name="calculator",
    version="1.0.0",
    tools=[calculate, compound_interest]  # 传递装饰过的函数
)
```

</CodeGroup>

## 相关文档

- [TypeScript SDK 参考](/docs/zh-CN/agent-sdk/typescript)
- [Python SDK 参考](/docs/zh-CN/agent-sdk/python)
- [MCP 文档](https://modelcontextprotocol.io)
- [SDK 概述](/docs/zh-CN/agent-sdk/overview)