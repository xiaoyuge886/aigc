# 自我进化功能技术说明

## 1. 整体架构

**核心设计原则**：
- 模型驱动：使用 AI 模型智能提取偏好，不依赖硬编码规则
- 数据摘要：只加载关键数据，避免全量历史数据加载
- 缓存机制：通过 hash 判断是否需要重新分析
- 分级学习：用户级（长期偏好）+ Session 级（临时偏好）

## 2. 数据层

### 2.1 核心表结构

**`user_feedback`** - 用户反馈表
- 存储所有显式/隐式反馈（like/dislike/correct/regenerate）
- 关联：user_id, session_id, message_id, conversation_turn_id

**`user_preferences_cache`** - 用户偏好缓存
- 缓存分析后的用户偏好（JSON）
- `data_summary_hash`：数据摘要 hash，用于判断是否需要重新分析

**`session_preferences`** - 会话偏好
- 会话级临时偏好（JSON）
- 包含：feedback_stats, corrections, context_preferences, feedback_summary

**`user_behavior_stats`** - 用户行为统计
- 轻量级聚合数据（会话数、消息数、反馈数、场景使用统计）

## 3. 服务层

### 3.1 FeedbackCollector（反馈收集器）
**职责**：
- 收集显式反馈（点赞/点踩/纠正/重新生成）
- 收集隐式反馈（重新提问、修改问题）
- 实时更新会话级偏好统计
- 更新用户行为统计

**调用位置**：
- `POST /api/v1/feedback` - 用户提交反馈时

### 3.2 PreferenceLearner（偏好学习引擎）
**职责**：
- 获取用户数据摘要（最近50条反馈、场景统计、问题类型）
- 使用模型智能提取用户偏好
- 缓存机制（hash 判断是否需要重新分析）

**用户级偏好结构**：
```json
{
  "preferred_scenarios": ["场景1", "场景2"],
  "preferred_style": "detailed|concise|professional|casual",
  "common_question_types": ["类型1", "类型2"],
  "learned_rules": ["规则1", "规则2"],
  "work_pattern": "工作模式描述"
}
```

**Session 级偏好结构**：
```json
{
  "corrections": ["纠正内容1", "纠正内容2"],
  "context_preferences": "上下文偏好描述",
  "feedback_summary": "反馈总结",
  "feedback_stats": {"like": 3, "dislike": 1}
}
```

**调用位置**：
- `GET /api/v1/users/{user_id}/preferences` - 获取用户偏好
- `CronJobs.batch_learn_user_preferences()` - 批量学习

### 3.3 PromptEvolver（Prompt 进化器）
**职责**：
- 将用户偏好和 Session 偏好格式化为文本
- 融入最终系统 Prompt

**格式化规则**：
- 用户偏好：优先显示 preferred_style、learned_rules
- Session 偏好：优先显示 corrections、context_preferences、feedback_summary
- 限制长度，避免 Prompt 过长

### 3.4 CronJobs（定时任务）
**职责**：
- 每小时批量学习用户偏好（`batch_learn_user_preferences`）
- 只分析有足够反馈的用户（默认 ≥5 条）
- 支持手动触发（`POST /api/v1/platform/cron/batch-learn-preferences`）

## 4. 工作流程

### 4.1 反馈收集流程
```
用户点击反馈按钮
  ↓
FeedbackCollector.collect_feedback()
  ↓
写入 user_feedback 表
  ↓
更新 session_preferences（反馈统计）
  ↓
更新 user_behavior_stats（行为统计）
```

### 4.2 偏好学习流程（用户级）
```
CronJob 触发 / 手动触发
  ↓
PreferenceLearner.get_user_data_summary()
  ↓
检查 data_summary_hash（是否需要重新分析）
  ↓
使用模型提取偏好（_extract_preferences_with_model）
  ↓
保存到 user_preferences_cache
```

### 4.3 偏好学习流程（Session 级）
```
PromptComposer.compose_base_prompt() 调用
  ↓
检查 session_preferences 是否存在/完整
  ↓
检查反馈数量（≥2 条）
  ↓
PreferenceLearner.learn_session_preferences()
  ↓
使用模型分析会话反馈
  ↓
保存到 session_preferences
```

### 4.4 Prompt 进化流程
```
PromptComposer.compose_base_prompt()
  ↓
加载用户偏好（UserPreferencesCacheDB）
  ↓
加载 Session 偏好（SessionPreferencesDB）
  ↓
PromptEvolver.evolve_prompt()
  ↓
格式化偏好并融入 system_prompt
  ↓
返回最终 Prompt
```

## 5. 触发机制

### 5.1 用户级偏好学习
- **定时触发**：每小时（CronJobs）
- **手动触发**：`POST /api/v1/platform/cron/batch-learn-preferences`
- **条件**：用户反馈数 ≥ 5（可配置）

### 5.2 Session 级偏好学习
- **按需触发**：PromptComposer 需要时
- **条件**：
  - Session 偏好为空或只有基础统计
  - Session 反馈数 ≥ 2
  - agent_service 可用

## 6. 性能优化

### 6.1 数据摘要
- 只加载最近50条反馈，不加载全量历史
- 使用聚合统计（场景使用、问题类型）

### 6.2 缓存机制
- 用户级：通过 `data_summary_hash` 判断是否需要重新分析
- Session 级：直接查询 `session_preferences` 表

### 6.3 异步处理
- 偏好学习在 CronJob 或按需触发，不阻塞主对话流程
- 模型分析异常时记录 Warning，不阻断主流程

## 7. 典型用例

### 用例1：用户长期偏好学习
- 用户多次反馈"回答太详细"
- 系统学习到用户偏好"简洁风格"
- 后续对话自动融入"请用简洁风格回答"

### 用例2：Session 临时偏好
- 用户在会话中多次纠正"使用专业术语"
- 系统学习到 Session 级偏好
- 本次会话后续回答自动融入"使用专业术语"

### 用例3：偏好进化
- 用户反馈数据变化（新反馈、新场景使用）
- `data_summary_hash` 变化
- 系统重新分析并更新偏好缓存
