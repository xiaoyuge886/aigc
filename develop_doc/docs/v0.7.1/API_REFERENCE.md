# API 参考文档

## 1. 认证

所有 API 请求需要 JWT Token（除登录/注册外）：
```
Authorization: Bearer <token>
```

## 2. 核心对话接口

### 2.1 流式对话查询
**POST** `/api/v1/session/query/stream`

**请求体**：
```json
{
  "prompt": "用户问题",
  "session_id": "会话ID，可选",
  "scenario_id": 1,
  "temperature": 0.7,
  "max_tokens": 4096
}
```

**响应**：Server-Sent Events (SSE) 流式响应

**说明**：
- 自动场景匹配（如果未指定 scenario_id）
- 自动组合 Prompt（系统默认 + 场景 + 用户偏好）
- 支持工具调用（Skill、MCP）

### 2.2 获取会话历史
**GET** `/api/v1/session/{session_id}/history?offset=0&limit=50`

**响应**：
```json
{
  "messages": [
    {
      "id": "消息ID",
      "text": "消息内容",
      "sender": "user|ai",
      "timestamp": "时间戳",
      "tool_calls": [...],
      "resultInfo": {...}
    }
  ],
  "total": 100,
  "has_more": true
}
```

## 3. 反馈接口

### 3.1 提交反馈
**POST** `/api/v1/feedback`

**请求体**：
```json
{
  "message_id": 123,
  "session_id": "会话ID",
  "conversation_turn_id": "轮次ID",
  "feedback_type": "like|dislike|correct|regenerate",
  "feedback_data": {
    "reason": "原因（dislike时）",
    "correct_text": "纠正内容（correct时）"
  },
  "user_prompt": "用户问题",
  "assistant_response": "AI回答",
  "scenario_ids": [1, 2]
}
```

**说明**：
- 触发偏好学习（异步）
- 更新会话级偏好统计

## 4. 场景管理接口（管理员）

### 4.1 创建场景
**POST** `/api/v1/platform/scenarios`

**请求体**：
```json
{
  "name": "场景名称",
  "description": "场景描述",
  "category": "类别",
  "meta": "Meta信息（JSON字符串）",
  "system_prompt": "场景专属Prompt",
  "is_default": false,
  "is_public": true
}
```

### 4.2 获取可用场景
**GET** `/api/v1/platform/scenarios/available?user_id=1`

**响应**：
```json
[
  {
    "id": 1,
    "name": "场景名称",
    "description": "描述",
    "category": "类别",
    "meta": {...},
    "is_default": false
  }
]
```

### 4.3 更新用户场景配置
**PUT** `/api/v1/platform/users/{user_id}/scenario-config`

**请求体**：
```json
{
  "scenario_ids": [1, 2, 3],
  "user_custom_prompt": "用户自定义Prompt（可选）"
}
```

## 5. 偏好查询接口

### 5.1 获取用户偏好
**GET** `/api/v1/platform/users/{user_id}/preferences`

**响应**：
```json
{
  "preferences": {
    "preferred_style": "detailed",
    "preferred_scenarios": ["场景1"],
    "learned_rules": ["规则1"]
  }
}
```

### 5.2 获取会话偏好
**GET** `/api/v1/platform/sessions/{session_id}/preferences`

**响应**：
```json
{
  "preferences": {
    "corrections": ["纠正内容1"],
    "context_preferences": "上下文偏好",
    "feedback_summary": "反馈总结"
  }
}
```

## 6. 定时任务接口（管理员）

### 6.1 手动触发偏好学习
**POST** `/api/v1/platform/cron/batch-learn-preferences?min_feedback_count=5&max_users_per_batch=10`

**请求体**（可选）：
```json
{
  "user_ids": [1, 2, 3]
}
```

**说明**：
- 如果提供 `user_ids`，忽略 `min_feedback_count` 限制
- 默认每小时自动执行

## 7. 文件接口

### 7.1 获取会话文件
**GET** `/api/v1/files/session/{session_id}`

**响应**：
```json
[
  {
    "file_id": "文件ID",
    "file_name": "文件名",
    "file_path": "文件路径",
    "file_type": "文件类型",
    "created_at": "时间戳"
  }
]
```

### 7.2 获取文件内容
**GET** `/api/v1/file/content?file_path=xxx`

**响应**：文件内容（文本）或下载链接

## 8. 数据流接口

### 8.1 获取对话轮次数据流
**GET** `/api/v1/conversation/{conversation_turn_id}/dataflow`

**响应**：
```json
{
  "conversation_turn_id": "轮次ID",
  "events": [
    {
      "type": "tool_call|tool_result|message",
      "timestamp": "时间戳",
      "data": {...}
    }
  ]
}
```

## 9. 错误码

- `200`：成功
- `201`：创建成功
- `204`：删除成功（无响应体）
- `400`：请求参数错误
- `401`：未认证
- `403`：无权限（非管理员）
- `404`：资源不存在
- `500`：服务器错误

## 10. 典型调用流程

### 流程1：用户提问
```
1. POST /api/v1/session/query/stream
   → 流式接收 AI 回复

2. POST /api/v1/feedback
   → 用户提交反馈
```

### 流程2：管理员配置
```
1. POST /api/v1/platform/scenarios
   → 创建场景

2. PUT /api/v1/platform/users/{user_id}/scenario-config
   → 为用户配置场景

3. GET /api/v1/platform/users/{user_id}/preferences
   → 查看用户偏好
```
