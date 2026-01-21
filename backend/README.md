# Claude Agent Server

基于 Claude Agent SDK 和 FastAPI 的通用 Agent 服务。

## 功能特性

- **单次查询** - 一次性任务，无需对话历史
- **会话模式** - 维护对话上下文的多轮对话
- **流式响应** - 支持 SSE 流式输出
- **自定义工具** - 使用 `@tool` 装饰器扩展功能
- **会话管理** - 自动清理过期会话
- **并发支持** - 多会话并发处理
- **模块化架构** - 清晰的分层设计，易于扩展

## 项目结构

```
backend/
├── api/                    # API 路由层
│   ├── __init__.py
│   └── v1/                # API v1 版本
│       ├── __init__.py
│       └── endpoints.py   # 所有路由端点
├── core/                   # 核心配置
│   ├── __init__.py
│   └── config.py          # 配置管理
├── models/                 # 数据模型
│   ├── __init__.py
│   └── schemas.py         # Pydantic 请求/响应模型
├── services/               # 业务逻辑层
│   ├── __init__.py
│   ├── agent_service.py   # Agent 服务核心
│   └── session_manager.py # 会话管理器
├── tools/                  # 自定义工具
│   ├── __init__.py
│   └── custom_tools.py    # MCP 工具示例
├── utils/                  # 工具函数（预留扩展）
│   └── __init__.py
├── main.py                 # FastAPI 应用入口
├── requirements.txt        # 依赖清单
├── .env.example            # 环境变量配置示例
├── .gitignore
└── README.md
```

### 架构说明

| 模块 | 职责 |
|------|------|
| `api/` | HTTP 路由层，处理请求/响应 |
| `core/` | 核心配置和常量 |
| `models/` | Pydantic 数据模型定义 |
| `services/` | 业务逻辑层，Agent 和会话管理 |
| `tools/` | 自定义 MCP 工具 |
| `utils/` | 通用工具函数 |

## 安装

### 1. 安装依赖

```bash
cd /Users/hehe/pycharm_projects/aigc/backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API key
```

### 3. 启动服务

```bash
python main.py
```

或使用 uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API 文档

启动服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 单次查询

**POST** `/api/v1/agent/query`

一次性查询，每次创建新会话，适合无状态任务。

```bash
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, Claude!",
    "model": "sonnet"
  }'
```

### 流式查询

**POST** `/api/v1/agent/query/stream`

SSE 流式响应，实时返回结果。

```bash
curl -N -X POST http://localhost:8000/api/v1/agent/query/stream \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Count from 1 to 10"
  }'
```

### 创建会话

**POST** `/api/v1/session`

创建一个可以维持对话上下文的会话。

```bash
curl -X POST http://localhost:8000/api/v1/session \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt": "You are a helpful assistant",
    "model": "sonnet"
  }'
```

响应:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-01T12:00:00"
}
```

### 会话查询

**POST** `/api/v1/session/{session_id}/query`

在已有会话中发送消息，Claude 会记住上下文。

```bash
curl -X POST http://localhost:8000/api/v1/session/{session_id}/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What did I just ask you?"
  }'
```

### 会话流式查询

**POST** `/api/v1/session/{session_id}/query/stream`

流式会话查询。

### 删除会话

**DELETE** `/api/v1/session/{session_id}`

### 列出会话

**GET** `/api/v1/sessions`

### 健康检查

**GET** `/api/v1/health`

## 自定义工具

在 `tools/custom_tools.py` 中添加自定义工具:

```python
from claude_agent_sdk import tool
from typing import Any

@tool("my_tool", "Tool description", {"param": str})
async def my_tool(args: dict[str, Any]) -> dict[str, Any]:
    result = do_something(args["param"])
    return {
        "content": [{
            "type": "text",
            "text": f"Result: {result}"
        }]
    }
```

然后在 `services/agent_service.py` 中启用:

```python
from tools.custom_tools import get_custom_tools_server
from claude_agent_sdk import ClaudeAgentOptions

def create_options(self, ...):
    return ClaudeAgentOptions(
        allowed_tools=[
            "Read", "Write", "Edit",
            "mcp__custom_tools__my_tool"  # 添加自定义工具
        ],
        mcp_servers={
            "custom_tools": get_custom_tools_server()
        }
    )
```

## 配置选项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `ANTHROPIC_API_KEY` | - | Anthropic API 密钥 |
| `HOST` | 0.0.0.0 | 服务监听地址 |
| `PORT` | 8000 | 服务端口 |
| `DEBUG` | false | 调试模式 |
| `DEFAULT_MODEL` | sonnet | 默认模型 (sonnet/opus/haiku) |
| `MAX_TURNS` | 20 | 最大对话轮数 |
| `PERMISSION_MODE` | acceptEdits | 权限模式 |
| `WORK_DIR` | ./ | 工作目录 |
| `SESSION_TIMEOUT_SECONDS` | 3600 | 会话超时(秒) |
| `MAX_CONCURRENT_SESSIONS` | 100 | 最大并发会话 |

## 权限模式

- `default` - 标准权限行为
- `acceptEdits` - 自动接受文件编辑
- `plan` - 规划模式，不执行
- `bypassPermissions` - 跳过所有权限检查

## 可用工具

内置工具:
- `Read` - 读取文件
- `Write` - 写入文件
- `Edit` - 编辑文件
- `Bash` - 执行命令
- `Glob` - 文件匹配
- `Grep` - 内容搜索
- `WebSearch` - 网页搜索
- `WebFetch` - 网页获取

自定义工具 (见 `tools/custom_tools.py`):
- `get_current_time` - 获取当前时间
- `calculate` - 数学计算
- `string_operations` - 字符串操作
- `get_system_info` - 系统信息

## Python 客户端示例

```python
import httpx

async def query_agent(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/agent/query",
            json={"prompt": prompt}
        )
        return response.json()

# 使用
result = await query_agent("Create a hello.py file")
print(result)
```

## JavaScript 客户端示例

```javascript
async function queryAgent(prompt) {
  const response = await fetch('http://localhost:8000/api/v1/agent/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({prompt})
  });
  return await response.json();
}

// 使用
const result = await queryAgent('Create a hello.py file');
console.log(result);
```

## 流式响应示例 (JavaScript)

```javascript
async function streamQuery(prompt) {
  const response = await fetch('http://localhost:8000/api/v1/agent/query/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({prompt})
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const {done, value} = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        console.log(data);
      }
    }
  }
}
```

## 扩展开发

### 添加新的 API 端点

1. 在 `api/v1/endpoints.py` 添加路由函数
2. 在 `models/schemas.py` 添加对应的请求/响应模型
3. 重启服务自动生效

### 添加新的业务逻辑

1. 在 `services/` 创建新的服务文件
2. 在 `api/v1/endpoints.py` 中导入并使用
3. 通过依赖注入获取服务实例

### 添加新的自定义工具

1. 在 `tools/` 创建新的工具文件
2. 使用 `@tool` 装饰器定义工具
3. 在 `services/agent_service.py` 中注册工具

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black .
ruff check .
```

## 许可

MIT
