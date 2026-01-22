## 技术架构总览（v0.7.1-dev-feat）

> 以当前代码为准，面向技术同事的简版架构说明。

### 1. 整体架构分层

- **前端（`frontend/aigc-frontend`）**
  - React + TypeScript + Vite。
  - 主要模块：
    - `ChatInterface.tsx`：主对话界面，负责会话列表、消息流、工具调用展示、反馈弹框。
    - `SessionHistory.tsx`：历史会话与 Session 级偏好展示。
    - `AdminDashboard.tsx` / `ResourceCenter.tsx`：管理员控制台（场景 / Prompt / Skill / 用户配置管理）。
    - `MessageFeedback.tsx`：单条消息反馈入口。
  - 通过 `services/agentService.ts`、`services/platformService.ts` 调用后端 API。

- **后端（`backend`）**
  - FastAPI + SQLAlchemy + SQLite。
  - 分层：
    - `api/v1/endpoints.py`：会话/对话主入口（`session_query_stream`）。
    - `api/v1/platform.py`：配置与管理类 API（场景、Prompt、Skill、用户配置、偏好、Cron）。
    - `models/database.py`：ORM 模型（User / Session / Message / BusinessScenario / SystemPrompt / Skill / Feedback / Preferences 等）。
    - `models/platform.py`：Pydantic 模型与请求/响应结构。
    - `services/*`：核心业务服务（AgentService / ScenarioMatcher / PromptComposer / PreferenceLearner / PromptEvolver / CronJobs 等）。

- **模型与外部依赖**
  - 通过 `services/agent_service.py` 调用 Claude Agent SDK（或兼容服务）。
  - 文件存储（如 PPTX）通过 MinIO 封装器上传。
  - 定时任务（CronJobs）在 FastAPI lifespan 中启动，周期性运行。

### 2. 核心数据模型（简版）

- **会话与消息**
  - `SessionDB`：会话（session_id、user_id、创建时间等）。
  - `MessageDB`：消息（id、session_id、sender、text、tool_use / tool_result、resultInfo 等）。
  - `ConversationTurnConfigDB`：每轮对话最终配置快照（用于审计与回放）。

- **场景与配置**
  - `BusinessScenarioDB`：
    - `id`（int 主键）、`name`、`description`、`category`、`meta`（JSON）、`system_prompt`、`is_default` 等。
  - `SystemPromptDB`：可复用系统 Prompt 模板。
  - `SkillDB`：技能模板（skill_content + skill_config），使用 int 主键 `id`。
  - `UserConfigDB`：用户级通用配置（包括旧版 `associated_scenario_id` 兼容字段）。
  - `UserScenarioConfigDB`：用户可用场景列表（`scenario_ids: List[int]` + 自定义 Prompt）。

- **自我进化相关**
  - `UserFeedbackDB`：单条反馈记录（like/dislike/correct/regenerate + 关联消息等）。
  - `UserPreferencesCacheDB`：用户级偏好缓存（JSON）。
  - `SessionPreferencesDB`：Session 级偏好缓存（JSON）。
  - `UserBehaviorStatsDB`：按用户聚合的行为统计（会话数、反馈数等）。

### 3. 核心服务模块

- **AgentService（`services/agent_service.py`）**
  - 封装与模型服务的交互（流式输出、工具调用、错误处理）。
  - 暴露给 ScenarioMatcher、PreferenceLearner、PromptComposer 等上层服务使用。

- **ScenarioProvider & ScenarioMatcher**
  - `ScenarioProvider`：根据用户/系统配置 + DB 中场景，计算「当前用户可用场景列表」。
  - `ScenarioMatcher`：
    - 构造紧凑的场景列表描述（包含 name/description/category/meta）。
    - 使用模型选择一个 `id: <场景ID>`，返回对应的场景对象。
    - 若无匹配或异常，兜底为默认场景。

- **ConfigurationManager（`services/configuration_manager.py`）**
  - 将请求参数、用户配置、场景配置、系统默认配置进行合并。
  - 生成统一的 `agent_config`（系统 Prompt、工具列表、参数等）。

- **PromptComposer & PromptEvolver**
  - `PromptComposer`：
    - 负责组合多层 Prompt：系统默认 → 场景 Prompt → 用户自定义 → 偏好。
    - 在有足够反馈时，调用 `PreferenceLearner.learn_session_preferences` 触发 Session 级偏好学习。
  - `PromptEvolver`：
    - 根据用户级与 Session 级偏好，生成附加说明片段插入系统 Prompt。
    - 控制长度与信息密度，避免干扰主任务。

- **PreferenceLearner（`services/preference_learner.py`）**
  - 汇总用户或 Session 最近的反馈记录，生成摘要。
  - 调用模型提取结构化偏好：
    - 用户级：长期偏好、常见纠正类型等。
    - Session 级：本轮会话的纠正内容、上下文偏好、反馈总结等。
  - 将结果写入 `UserPreferencesCacheDB` / `SessionPreferencesDB`。

- **FeedbackCollector（`services/feedback_collector.py`）**
  - 对前端传来的反馈请求进行持久化。
  - 更新用户行为统计，为偏好学习提供数据基础。

- **CronJobs（`services/cron_jobs.py`）**
  - 在应用启动时注册，周期性运行：
    - 选择反馈数达到阈值的用户，批量执行 `PreferenceLearner.learn_user_preferences`。
  - 提供手动触发接口 `POST /api/v1/platform/cron/batch-learn-preferences`。

### 4. 会话请求主链路（文字版架构图）

1. 前端 `ChatInterface` 调用 `agentService.streamAgentQuery` → `POST /api/v1/session/query_stream`。  
2. `endpoints.py`：
   - 校验用户、解析 session_id，必要时新建 Session。  
   - 从 `UserScenarioConfigDB` + `UserConfigDB` + 默认场景中得到候选场景列表。  
   - 若存在多个候选，调用 `ScenarioMatcher.match_scenario` 选出一个场景。  
   - 调用 `ConfigurationManager.merge_agent_config` 合并配置。  
   - 调用 `PromptComposer.compose_base_prompt` 生成最终系统 Prompt（含偏好）。  
   - 通过 `AgentService` 调用模型，流式返回消息与工具使用结果。  
   - 将消息和 `ConversationTurnConfigDB` 写入 DB。
3. 前端订阅流式结果，更新消息列表、工具调用区域、文件事件等。

### 5. 自我进化链路（文字版架构图）

1. 用户在前端对某条 AI 消息进行反馈（like/dislike/correct/regenerate），前端调用反馈 API。  
2. 后端 `FeedbackCollector` 写入 `UserFeedbackDB`、更新 `UserBehaviorStatsDB`。  
3. 定时任务或 PromptComposer 根据反馈数量条件，触发 `PreferenceLearner`：  
   - 聚合反馈数据，调用模型生成偏好 JSON，写入偏好表。  
4. 下一次对话时，`PromptComposer` 读取偏好并通过 `PromptEvolver` 将其写入系统 Prompt，形成“自我进化”效果。

