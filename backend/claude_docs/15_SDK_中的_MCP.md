# SDK 中的 MCP

使用模型上下文协议服务器通过自定义工具扩展 Claude Code

## 概述

模型上下文协议(MCP)服务器通过自定义工具和功能扩展 Claude Code。MCP 可以作为外部进程运行，通过 HTTP/SSE 连接，或直接在您的 SDK 应用程序中执行。

## 配置

### 基本配置

在项目根目录的 `.mcp.json` 中配置 MCP 服务器：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem"],
      "env": {
        "ALLOWED_PATHS": "/Users/me/projects"
      }
    }
  }
}
```

### 在 SDK 中使用 MCP 服务器

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "List files in my project",
  options: {
    mcpServers: {
      "filesystem": {
        command: "npx",
        args: ["@modelcontextprotocol/server-filesystem"],
        env: {
          ALLOWED_PATHS: "/Users/me/projects"
        }
      }
    },
    allowedTools: ["mcp__filesystem__list_files"]
  }
})) {
  if (message.type === "result" && message.subtype === "success") {
    console.log(message.result);
  }
}
```

## 传输类型

### stdio 服务器

通过 stdin/stdout 通信的外部进程：

```json
// .mcp.json 配置
{
  "mcpServers": {
    "my-tool": {
      "command": "node",
      "args": ["./my-mcp-server.js"],
      "env": {
        "DEBUG": "${DEBUG:-false}"
      }
    }
  }
}
```

### HTTP/SSE 服务器

具有网络通信的远程服务器：

```json
// SSE 服务器配置
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

// HTTP 服务器配置
{
  "mcpServers": {
    "http-service": {
      "type": "http",
      "url": "https://api.example.com/mcp",
      "headers": {
        "X-API-Key": "${API_KEY}"
      }
    }
  }
}
```

### SDK MCP 服务器

在您的应用程序中运行的进程内服务器。有关创建自定义工具的详细信息，请参阅自定义工具指南。

## 资源管理

MCP 服务器可以公开 Claude 可以列出和读取的资源：

```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

// 列出可用资源
for await (const message of query({
  prompt: "What resources are available from the database server?",
  options: {
    mcpServers: {
      "database": {
        command: "npx",
        args: ["@modelcontextprotocol/server-database"]
      }
    },
    allowedTools: ["mcp__list_resources", "mcp__read_resource"]
  }
})) {
  if (message.type === "result") console.log(message.result);
}
```

## 身份验证

### 环境变量

```typescript
// 带有环境变量的 .mcp.json
{
  "mcpServers": {
    "secure-api": {
      "type": "sse",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}",
        "X-API-Key": "${API_KEY:-default-key}"
      }
    }
  }
}

// 设置环境变量
process.env.API_TOKEN = "your-token";
process.env.API_KEY = "your-key";
```

### OAuth2 身份验证

目前不支持客户端内的 OAuth2 MCP 身份验证。

## 错误处理

优雅地处理 MCP 连接失败：

```typescript
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
    // 检查 MCP 服务器状态
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

## 相关资源

- 自定义工具指南 - 创建 SDK MCP 服务器的详细指南
- TypeScript SDK 参考
- Python SDK 参考
- SDK 权限
- 常见工作流程
