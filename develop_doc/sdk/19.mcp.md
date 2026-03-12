# 通过 MCP 连接外部工具

配置 MCP 服务器以使用外部工具扩展您的代理。涵盖传输类型、大型工具集的工具搜索、身份验证和错误处理。

---

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/docs/getting-started/intro) 是一个用于将 AI 代理连接到外部工具和数据源的开放标准。通过 MCP，您的代理可以查询数据库、集成 Slack 和 GitHub 等 API，以及连接其他服务，而无需编写自定义工具实现。

MCP 服务器可以作为本地进程运行、通过 HTTP 连接，或直接在您的 SDK 应用程序中执行。

## 快速开始

此示例使用 [HTTP 传输](#httpsse-servers)连接到 [Claude Code 文档](https://code.claude.com/docs) MCP 服务器，并使用带通配符的 [`allowedTools`](#allow-mcp-tools) 来允许服务器的所有工具。

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Use the docs MCP server to explain what hooks are in Claude Code",
  options: {
    mcpServers: {
      "claude-code-docs": {
        type: "http",
        url: "https://code.claude.com/docs/mcp"
      }
    },
    allowedTools: ["mcp__claude-code-docs__*"]
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

```python Python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def main():
    options = ClaudeAgentOptions(
        mcp_servers={
            "claude-code-docs": {
                "type": "http",
                "url": "https://code.claude.com/docs/mcp"
            }
        },
        allowed_tools=["mcp__claude-code-docs__*"]
    )

    async for message in query(prompt="Use the docs MCP server to explain what hooks are in Claude Code", options=options):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)

asyncio.run(main())
```

</CodeGroup>

代理连接到文档服务器，搜索有关 hooks 的信息，并返回结果。

## 添加 MCP 服务器

您可以在调用 `query()` 时在代码中配置 MCP 服务器，或在 SDK 自动加载的 `.mcp.json` 文件中进行配置。

### 在代码中

直接在 `mcpServers` 选项中传递 MCP 服务器：

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "List files in my project",
  options: {
    mcpServers: {
      "filesystem": {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/Users/me/projects"]
      }
    },
    allowedTools: ["mcp__filesystem__*"]
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

```python Python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def main():
    options = ClaudeAgentOptions(
        mcp_servers={
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/me/projects"]
            }
        },
        allowed_tools=["mcp__filesystem__*"]
    )

    async for message in query(prompt="List files in my project", options=options):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)

asyncio.run(main())
```

</CodeGroup>

### 从配置文件

在项目根目录创建 `.mcp.json` 文件。SDK 会自动加载此文件：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/me/projects"]
    }
  }
}
```

## 允许 MCP 工具

MCP 工具需要明确的权限才能让 Claude 使用。如果没有权限，Claude 会看到工具可用但无法调用它们。

### 工具命名约定

MCP 工具遵循 `mcp__<server-name>__<tool-name>` 的命名模式。例如，名为 `"github"` 的 GitHub 服务器中的 `list_issues` 工具会变成 `mcp__github__list_issues`。

### 使用 allowedTools 授予访问权限

使用 `allowedTools` 指定 Claude 可以使用哪些 MCP 工具：

```typescript
options: {
  mcpServers: { /* your servers */ },
  allowedTools: [
    "mcp__github__*",              // github 服务器的所有工具
    "mcp__db__query",              // 仅 db 服务器的 query 工具
    "mcp__slack__send_message"     // 仅 slack 的 send_message
  ]
}
```

通配符（`*`）允许您授权服务器的所有工具，而无需逐一列出。

### 替代方案：更改权限模式

除了列出允许的工具外，您还可以更改权限模式以授予更广泛的访问权限：

- `permissionMode: "acceptEdits"`：自动批准工具使用（对于破坏性操作仍会提示）
- `permissionMode: "bypassPermissions"`：跳过所有安全提示，包括文件删除或运行 shell 命令等破坏性操作。请谨慎使用，尤其是在生产环境中。此模式会传播到 Task 工具生成的子代理。

```typescript
options: {
  mcpServers: { /* your servers */ },
  permissionMode: "acceptEdits"  // 无需 allowedTools
}
```

有关权限模式的更多详细信息，请参阅[权限](/docs/zh-CN/agent-sdk/permissions)。

### 发现可用工具

要查看 MCP 服务器提供了哪些工具，请查看服务器的文档或连接到服务器并检查 `system` init 消息：

```typescript
for await (const message of query({ prompt: "...", options })) {
  if (message.type === "system" && message.subtype === "init") {
    console.log("Available MCP tools:", message.mcp_servers);
  }
}
```

## 传输类型

MCP 服务器使用不同的传输协议与您的代理通信。请查看服务器的文档以了解它支持哪种传输方式：

- 如果文档给出的是**要运行的命令**（如 `npx @modelcontextprotocol/server-github`），请使用 stdio
- 如果文档给出的是 **URL**，请使用 HTTP 或 SSE
- 如果您在代码中构建自己的工具，请使用 SDK MCP 服务器

### stdio 服务器

通过 stdin/stdout 通信的本地进程。用于在同一台机器上运行的 MCP 服务器：

<Tabs>
  <Tab title="在代码中">
    <CodeGroup>

    ```typescript TypeScript
    options: {
      mcpServers: {
        "github": {
          command: "npx",
          args: ["-y", "@modelcontextprotocol/server-github"],
          env: {
            GITHUB_TOKEN: process.env.GITHUB_TOKEN
          }
        }
      },
      allowedTools: ["mcp__github__list_issues", "mcp__github__search_issues"]
    }
    ```

    ```python Python
    options = ClaudeAgentOptions(
        mcp_servers={
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]
                }
            }
        },
        allowed_tools=["mcp__github__list_issues", "mcp__github__search_issues"]
    )
    ```

    </CodeGroup>
  </Tab>
  <Tab title=".mcp.json">
    ```json
    {
      "mcpServers": {
        "github": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-github"],
          "env": {
            "GITHUB_TOKEN": "${GITHUB_TOKEN}"
          }
        }
      }
    }
    ```
  </Tab>
</Tabs>

### HTTP/SSE 服务器

对于云托管的 MCP 服务器和远程 API，请使用 HTTP 或 SSE：

<Tabs>
  <Tab title="在代码中">
    <CodeGroup>

    ```typescript TypeScript
    options: {
      mcpServers: {
        "remote-api": {
          type: "sse",
          url: "https://api.example.com/mcp/sse",
          headers: {
            Authorization: `Bearer ${process.env.API_TOKEN}`
          }
        }
      },
      allowedTools: ["mcp__remote-api__*"]
    }
    ```

    ```python Python
    options = ClaudeAgentOptions(
        mcp_servers={
            "remote-api": {
                "type": "sse",
                "url": "https://api.example.com/mcp/sse",
                "headers": {
                    "Authorization": f"Bearer {os.environ['API_TOKEN']}"
                }
            }
        },
        allowed_tools=["mcp__remote-api__*"]
    )
    ```

    </CodeGroup>
  </Tab>
  <Tab title=".mcp.json">
    ```json
    {
      "mcpServers": {
        "remote-api": {
          "type": "sse",
          "url": "https://api.example.com/mcp/sse",
          "headers": {
            "Authorization": "Bearer ${API_TOKEN}"
          }
        }
      }
    }
    ```
  </Tab>
</Tabs>

对于 HTTP（非流式），请改用 `"type": "http"`。

### SDK MCP 服务器

直接在应用程序代码中定义自定义工具，而不是运行单独的服务器进程。有关实现详情，请参阅[自定义工具指南](/docs/zh-CN/agent-sdk/custom-tools)。

## MCP 工具搜索

当您配置了大量 MCP 工具时，工具定义可能会占用上下文窗口的很大一部分。MCP 工具搜索通过按需动态加载工具而不是预加载所有工具来解决此问题。

### 工作原理

工具搜索默认以自动模式运行。当您的 MCP 工具描述占用超过上下文窗口 10% 时，它会激活。触发时：

1. MCP 工具被标记为 `defer_loading: true`，而不是预先加载到上下文中
2. Claude 使用搜索工具在需要时发现相关的 MCP 工具
3. 只有 Claude 实际需要的工具才会加载到上下文中

工具搜索需要支持 `tool_reference` 块的模型：Sonnet 4 及更高版本，或 Opus 4 及更高版本。Haiku 模型不支持工具搜索。

### 配置工具搜索

使用 `ENABLE_TOOL_SEARCH` 环境变量控制工具搜索行为：

| 值 | 行为 |
|:------|:---------|
| `auto` | 当 MCP 工具超过上下文的 10% 时激活（默认） |
| `auto:5` | 在 5% 阈值时激活（自定义百分比） |
| `true` | 始终启用 |
| `false` | 禁用，所有 MCP 工具预先加载 |

在 `env` 选项中设置值：

<CodeGroup>

```typescript TypeScript
const options = {
  mcpServers: { /* your MCP servers */ },
  env: {
    ENABLE_TOOL_SEARCH: "auto:5"  // 在 5% 阈值时启用
  }
};
```

```python Python
options = ClaudeAgentOptions(
    mcp_servers={ ... },  # your MCP servers
    env={
        "ENABLE_TOOL_SEARCH": "auto:5"  # 在 5% 阈值时启用
    }
)
```

</CodeGroup>

## 身份验证

大多数 MCP 服务器需要身份验证才能访问外部服务。通过服务器配置中的环境变量传递凭据。

### 通过环境变量传递凭据

使用 `env` 字段将 API 密钥、令牌和其他凭据传递给 MCP 服务器：

<Tabs>
  <Tab title="在代码中">
    <CodeGroup>

    ```typescript TypeScript
    options: {
      mcpServers: {
        "github": {
          command: "npx",
          args: ["-y", "@modelcontextprotocol/server-github"],
          env: {
            GITHUB_TOKEN: process.env.GITHUB_TOKEN
          }
        }
      },
      allowedTools: ["mcp__github__list_issues"]
    }
    ```

    ```python Python
    options = ClaudeAgentOptions(
        mcp_servers={
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]
                }
            }
        },
        allowed_tools=["mcp__github__list_issues"]
    )
    ```

    </CodeGroup>
  </Tab>
  <Tab title=".mcp.json">
    ```json
    {
      "mcpServers": {
        "github": {
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-github"],
          "env": {
            "GITHUB_TOKEN": "${GITHUB_TOKEN}"
          }
        }
      }
    }
    ```

    `${GITHUB_TOKEN}` 语法会在运行时展开环境变量。
  </Tab>
</Tabs>

有关包含调试日志的完整工作示例，请参阅[列出仓库中的 issues](#list-issues-from-a-repository)。

### 远程服务器的 HTTP 头

对于 HTTP 和 SSE 服务器，直接在服务器配置中传递身份验证头：

<Tabs>
  <Tab title="在代码中">
    <CodeGroup>

    ```typescript TypeScript
    options: {
      mcpServers: {
        "secure-api": {
          type: "http",
          url: "https://api.example.com/mcp",
          headers: {
            Authorization: `Bearer ${process.env.API_TOKEN}`
          }
        }
      },
      allowedTools: ["mcp__secure-api__*"]
    }
    ```

    ```python Python
    options = ClaudeAgentOptions(
        mcp_servers={
            "secure-api": {
                "type": "http",
                "url": "https://api.example.com/mcp",
                "headers": {
                    "Authorization": f"Bearer {os.environ['API_TOKEN']}"
                }
            }
        },
        allowed_tools=["mcp__secure-api__*"]
    )
    ```

    </CodeGroup>
  </Tab>
  <Tab title=".mcp.json">
    ```json
    {
      "mcpServers": {
        "secure-api": {
          "type": "http",
          "url": "https://api.example.com/mcp",
          "headers": {
            "Authorization": "Bearer ${API_TOKEN}"
          }
        }
      }
    }
    ```

    `${API_TOKEN}` 语法会在运行时展开环境变量。
  </Tab>
</Tabs>

### OAuth2 身份验证

[MCP 规范支持 OAuth 2.1](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization) 进行授权。SDK 不会自动处理 OAuth 流程，但您可以在应用程序中完成 OAuth 流程后通过头传递访问令牌：

<CodeGroup>

```typescript TypeScript
// 在您的应用中完成 OAuth 流程后
const accessToken = await getAccessTokenFromOAuthFlow();

const options = {
  mcpServers: {
    "oauth-api": {
      type: "http",
      url: "https://api.example.com/mcp",
      headers: {
        Authorization: `Bearer ${accessToken}`
      }
    }
  },
  allowedTools: ["mcp__oauth-api__*"]
};
```

```python Python
# 在您的应用中完成 OAuth 流程后
access_token = await get_access_token_from_oauth_flow()

options = ClaudeAgentOptions(
    mcp_servers={
        "oauth-api": {
            "type": "http",
            "url": "https://api.example.com/mcp",
            "headers": {
                "Authorization": f"Bearer {access_token}"
            }
        }
    },
    allowed_tools=["mcp__oauth-api__*"]
)
```

</CodeGroup>

## 示例

### 列出仓库中的 issues

此示例连接到 [GitHub MCP 服务器](https://github.com/modelcontextprotocol/servers/tree/main/src/github)以列出最近的 issues。该示例包含调试日志以验证 MCP 连接和工具调用。

在运行之前，创建一个具有 `repo` 范围的 [GitHub 个人访问令牌](https://github.com/settings/tokens)并将其设置为环境变量：

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "List the 3 most recent issues in anthropics/claude-code",
  options: {
    mcpServers: {
      "github": {
        command: "npx",
        args: ["-y", "@modelcontextprotocol/server-github"],
        env: {
          GITHUB_TOKEN: process.env.GITHUB_TOKEN
        }
      }
    },
    allowedTools: ["mcp__github__list_issues"]
  }
})) {
  // 验证 MCP 服务器连接成功
  if (message.type === "system" && message.subtype === "init") {
    console.log("MCP servers:", message.mcp_servers);
  }

  // 记录 Claude 调用 MCP 工具的时间
  if (message.type === "assistant") {
    for (const block of message.content) {
      if (block.type === "tool_use" && block.name.startsWith("mcp__")) {
        console.log("MCP tool called:", block.name);
      }
    }
  }

  // 打印最终结果
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

```python Python
import asyncio
import os
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, SystemMessage, AssistantMessage

async def main():
    options = ClaudeAgentOptions(
        mcp_servers={
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]
                }
            }
        },
        allowed_tools=["mcp__github__list_issues"]
    )

    async for message in query(prompt="List the 3 most recent issues in anthropics/claude-code", options=options):
        # 验证 MCP 服务器连接成功
        if isinstance(message, SystemMessage) and message.subtype == "init":
            print("MCP servers:", message.data.get("mcp_servers"))

        # 记录 Claude 调用 MCP 工具的时间
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "name") and block.name.startswith("mcp__"):
                    print("MCP tool called:", block.name)

        # 打印最终结果
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)

asyncio.run(main())
```

</CodeGroup>

### 查询数据库

此示例使用 [Postgres MCP 服务器](https://github.com/modelcontextprotocol/servers/tree/main/src/postgres)查询数据库。连接字符串作为参数传递给服务器。代理会自动发现数据库架构、编写 SQL 查询并返回结果：

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 来自环境变量的连接字符串
const connectionString = process.env.DATABASE_URL;

for await (const message of query({
  // 自然语言查询 - Claude 编写 SQL
  prompt: "How many users signed up last week? Break it down by day.",
  options: {
    mcpServers: {
      "postgres": {
        command: "npx",
        // 将连接字符串作为参数传递给服务器
        args: ["-y", "@modelcontextprotocol/server-postgres", connectionString]
      }
    },
    // 仅允许读取查询，不允许写入
    allowedTools: ["mcp__postgres__query"]
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

```python Python
import asyncio
import os
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def main():
    # 来自环境变量的连接字符串
    connection_string = os.environ["DATABASE_URL"]

    options = ClaudeAgentOptions(
        mcp_servers={
            "postgres": {
                "command": "npx",
                # 将连接字符串作为参数传递给服务器
                "args": ["-y", "@modelcontextprotocol/server-postgres", connection_string]
            }
        },
        # 仅允许读取查询，不允许写入
        allowed_tools=["mcp__postgres__query"]
    )

    # 自然语言查询 - Claude 编写 SQL
    async for message in query(
        prompt="How many users signed up last week? Break it down by day.",
        options=options
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)

asyncio.run(main())
```

</CodeGroup>

## 错误处理

MCP 服务器可能因各种原因连接失败：服务器进程可能未安装、凭据可能无效，或远程服务器可能无法访问。

SDK 在每次查询开始时会发出一个子类型为 `init` 的 `system` 消息。此消息包含每个 MCP 服务器的连接状态。检查 `status` 字段以在代理开始工作之前检测连接失败：

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "Process data",
  options: {
    mcpServers: {
      "data-processor": dataServer
    }
  }
})) {
  if (message.type === "system" && message.subtype === "init") {
    const failedServers = message.mcp_servers.filter(
      s => s.status !== "connected"
    );

    if (failedServers.length > 0) {
      console.warn("Failed to connect:", failedServers);
    }
  }

  if (message.type === "result" && message.subtype === "error_during_execution") {
    console.error("Execution failed");
  }
}
```

```python Python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, SystemMessage, ResultMessage

async def main():
    options = ClaudeAgentOptions(
        mcp_servers={
            "data-processor": data_server
        }
    )

    async for message in query(prompt="Process data", options=options):
        if isinstance(message, SystemMessage) and message.subtype == "init":
            failed_servers = [
                s for s in message.data.get("mcp_servers", [])
                if s.get("status") != "connected"
            ]

            if failed_servers:
                print(f"Failed to connect: {failed_servers}")

        if isinstance(message, ResultMessage) and message.subtype == "error_during_execution":
            print("Execution failed")

asyncio.run(main())
```

</CodeGroup>

## 故障排除

### 服务器显示"failed"状态

检查 `init` 消息以查看哪些服务器连接失败：

```typescript
if (message.type === "system" && message.subtype === "init") {
  for (const server of message.mcp_servers) {
    if (server.status === "failed") {
      console.error(`Server ${server.name} failed to connect`);
    }
  }
}
```

常见原因：

- **缺少环境变量**：确保已设置所需的令牌和凭据。对于 stdio 服务器，检查 `env` 字段是否与服务器期望的匹配。
- **服务器未安装**：对于 `npx` 命令，验证包是否存在以及 Node.js 是否在您的 PATH 中。
- **无效的连接字符串**：对于数据库服务器，验证连接字符串格式以及数据库是否可访问。
- **网络问题**：对于远程 HTTP/SSE 服务器，检查 URL 是否可达以及防火墙是否允许连接。

### 工具未被调用

如果 Claude 看到工具但不使用它们，请检查您是否已通过 `allowedTools` 或[更改权限模式](#alternative-change-the-permission-mode)授予了权限：

```typescript
options: {
  mcpServers: { /* your servers */ },
  allowedTools: ["mcp__servername__*"]  // Claude 使用工具所必需的
}
```

### 连接超时

MCP SDK 的服务器连接默认超时时间为 60 秒。如果您的服务器启动时间更长，连接将失败。对于需要更多启动时间的服务器，请考虑：

- 如果可用，使用更轻量级的服务器
- 在启动代理之前预热服务器
- 检查服务器日志以查找初始化缓慢的原因

## 相关资源

- **[自定义工具指南](/docs/zh-CN/agent-sdk/custom-tools)**：构建您自己的 MCP 服务器，在 SDK 应用程序中以进程内方式运行
- **[权限](/docs/zh-CN/agent-sdk/permissions)**：使用 `allowedTools` 和 `disallowedTools` 控制代理可以使用哪些 MCP 工具
- **[TypeScript SDK 参考](/docs/zh-CN/agent-sdk/typescript)**：完整的 API 参考，包括 MCP 配置选项
- **[Python SDK 参考](/docs/zh-CN/agent-sdk/python)**：完整的 API 参考，包括 MCP 配置选项
- **[MCP 服务器目录](https://github.com/modelcontextprotocol/servers)**：浏览可用的数据库、API 等 MCP 服务器