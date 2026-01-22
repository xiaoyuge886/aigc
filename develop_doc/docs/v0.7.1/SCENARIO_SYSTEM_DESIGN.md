# 对话与场景体系设计文档

## 1. 核心概念

### 1.1 会话层级
- **Session（会话）**：用户一次完整对话的容器，包含多轮对话
- **ConversationTurn（对话轮次）**：单次用户提问 + AI 回复的完整交互
- **Message（消息）**：对话中的单条消息（user/ai/tool_use/tool_result）

### 1.2 场景体系
- **BusinessScenario（业务场景）**：业务语境 + 系统 Prompt + 技能组合
- **SystemPrompt（系统提示词）**：可复用的 Prompt 模板
- **Skill（技能）**：可执行的能力单元（如 PPTX 生成、数据分析）

## 2. 场景匹配流程

### 2.1 场景来源优先级
1. **请求显式指定**：`request.scenario_id`
2. **用户场景配置**：`UserScenarioConfigDB.scenario_ids`（多选）
3. **用户关联场景**：`UserConfigDB.associated_scenario_id`（兼容旧版）
4. **系统默认场景**：`is_default = true` 的场景

### 2.2 智能匹配（ScenarioMatcher）
当用户有多个可用场景时：
- 输入：用户问题 + 场景列表（名称/描述/meta）
- 处理：调用模型分析，返回最匹配的场景 ID
- 输出：单个场景配置
- 缓存：相同查询 + 场景列表组合的结果缓存

### 2.3 回退保证
- 匹配失败或无场景 → 使用默认场景
- 默认场景缺失 → 使用硬编码通用场景
- **保证用户始终能得到回复**

## 3. Prompt 组合逻辑

### 3.1 组合层级（PromptComposer）
```
系统默认 Prompt
  ↓
+ 场景描述与可用场景列表
  ↓
+ 场景专属 Prompt（如果匹配到场景）
  ↓
+ 用户自定义 Prompt
  ↓
+ 会话自定义 Prompt
  ↓
+ 用户级偏好（UserPreferences）
  ↓
+ 会话级偏好（SessionPreferences）
  ↓
= 最终 system_prompt
```

### 3.2 场景列表格式
在系统 Prompt 中动态插入：
```
## 可用场景列表
1. [场景名称] - [描述] - 类别：[category] - Meta：[meta]
2. ...
```

## 4. 配置合并优先级

### 4.1 Agent 配置（ConfigurationManager）
优先级：**Request > Session > User > Scenario > Global**

- **Request**：单次请求参数（temperature、max_tokens 等）
- **Session**：会话级配置（会话专属 Prompt、工具列表）
- **User**：用户级配置（用户 Prompt、场景授权）
- **Scenario**：场景配置（场景 Prompt、技能列表、MCP 工具）
- **Global**：系统默认配置

### 4.2 技能与工具
- 场景可配置 `skill_ids`（JSON 数组）
- 场景可配置 `custom_tools`（MCP 工具列表）
- 最终 `allowed_tools` = 场景工具 + 系统默认工具

## 5. 数据流转

### 5.1 对话请求流程
```
用户输入
  ↓
解析 user_id / session_id
  ↓
确定场景（ScenarioMatcher / 配置）
  ↓
合并配置（ConfigurationManager）
  ↓
组合 Prompt（PromptComposer）
  ↓
调用模型（AgentService）
  ↓
工具调用（Skill / MCP）
  ↓
保存结果（MessageDB / ConversationTurnConfigDB）
```

### 5.2 关键数据表
- `sessions`：会话基础信息
- `messages`：消息记录（text/tool_use/tool_result）
- `conversation_turn_configs`：每轮对话的配置快照
- `business_scenarios`：场景定义
- `user_scenario_configs`：用户场景授权
- `user_configs`：用户个性化配置

## 6. 典型用例

### 用例1：PPT 生成
- 用户输入："写一个关于 AI 发展史的 PPT，风格参考 Apple 官网"
- 场景匹配：自动匹配到"文档生成"场景
- 技能调用：PPTX 技能生成文件
- 文件上传：MinIO 存储，前端显示下载链接

### 用例2：代码助手
- 用户输入："写一个 python 爬虫"
- 场景匹配：自动匹配到"开发类"场景
- Prompt 组合：加入开发类系统 Prompt
- 工具调用：根据需求调用相应工具

### 用例3：多场景用户
- 用户配置：同时拥有"开发"、"运营"、"数据分析"场景
- 智能匹配：根据问题自动选择最合适场景
- 回退保证：匹配失败时使用默认场景
