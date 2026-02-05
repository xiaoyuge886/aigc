# Findings & Technical Decisions - Agent OS V1.1

**Purpose:** 记录技术调研发现、架构决策、关键问题解决方案

---

## 1. 现有系统架构分析

**完成时间:** 2026-01-26

### 后端架构
- **框架:** FastAPI 0.115.0
- **数据库:** SQLAlchemy 2.0 + SQLite (可升级至 PostgreSQL)
- **AI 核心:** Claude Agent SDK (已集成)
- **关键文件:**
  - `backend/services/agent_service.py` - Agent 服务
  - `backend/services/session_manager.py` - 会话管理
  - `backend/services/scenario_matcher.py` - 场景匹配

### 前端架构
- **框架:** React 19.2.0 + TypeScript + Vite 6.2.0
- **关键组件:**
  - `ChatInterface.tsx` - 聊天界面
  - `services/agentService.ts` - Agent 服务封装

### 现有能力
- ✅ Claude Agent SDK 集成（流式响应、工具调用）
- ✅ 会话管理（多用户、历史记录）
- ✅ 技能系统（.claude/skills/ 目录）
- ✅ 场景匹配引擎
- ✅ 文件上传管理（MinIO）

### 缺失能力（需实现）
- ❌ 目标理解与澄清模块（FR-1）
- ❌ 规划系统（FR-2）
- ❌ mem0 记忆系统（FR-6）
- ❌ 多 Agent 协调机制（FR-7）
- ❌ Agent Run 状态机（FR-5）
- ❌ HITL 机制（FR-4）
- ❌ Skill Marketplace（FR-10）
- ❌ A2UI 可视化（FR-8）

---

## 2. Claude Agent SDK HITL 支持分析

**完成时间:** 2026-01-26

### 核心发现

#### ✅ SDK 原生支持 HITL
- **can_use_tool callback:** 工具权限回调
- **Hook System:** 6 种钩子
  - PreToolUse - 工具使用前
  - PostToolUse - 工具使用后
  - UserPromptSubmit - 用户提交提示
  - Stop - 停止时
  - SubagentStop - 子 Agent 停止
  - PreCompact - 压缩前
- **Control Protocol:** 双向控制（control_request/control_response）
- **Permission Modes:** default, acceptEdits, plan, bypassPermissions

#### ⚠️ SDK 限制
- **无内置 HITL UI:** 需要自己实现前端组件
- **停止机制未完全实现:** `control_cancel_request` 标记为 TODO
- **仅支持 Python 级取消:** 通过 `anyio.get_cancelled_exc_class()`

### HITL 实现方式

**1. 工具级 HITL**
```python
async def can_use_tool(
    tool_name: str,
    tool_input: dict,
    context: ToolPermissionContext
) -> PermissionResult:
    # 返回 PermissionResultAllow（允许/修改）
    # 或 PermissionResultDeny（拒绝）
```

**2. 钩子级 HITL**
```python
options = ClaudeAgentOptions(
    hooks={
        HookEvent.PreToolUse: [
            HookMatcher(
                matcher={"name": "bash"},
                hooks=my_approval_function
            )
        ]
    }
)
```

**3. 阶段级 HITL**
- 基于 `UserPromptSubmit` hook
- 支持完整 Agent OS 阶段确认

### 源码位置
- SDK 路径: `.venv/lib/python3.11/site-packages/claude_agent_sdk/`
- 关键文件:
  - `_internal/query.py` - Query 实现
  - `client.py` - ClaudeSDKClient
  - `types.py` - 类型定义

---

## 3. Agent 停止机制调研

**完成时间:** 2026-01-26

### 关键发现

#### ❌ SDK 不支持主动停止
```python
# .venv/lib/python3.11/site-packages/claude_agent_sdk/_internal/query.py:199-202
elif msg_type == "control_cancel_request":
    # Handle cancel requests
    # TODO: Implement cancellation support  ⚠️ 尚未实现
    continue
```

#### ✅ Python 级取消支持
```python
try:
    async for msg in client.receive_response():
        # 处理消息...
except asyncio.CancelledError:
    logger.info("Agent cancelled")
```

### 现有代码限制
- ❌ 没有存储 `asyncio.Task` 对象
- ❌ 没有提供取消令牌（cancellation token）
- ❌ Agent 运行在 `async for` 循环中，无法从外部中断
- ❌ 使用 `async with` 自动管理生命周期

### 解决方案

**方案 1: 使用 `asyncio.create_task`**
```python
running_agents: Dict[str, asyncio.Task] = {}

@router.post("/agent/start")
async def start_agent():
    task = asyncio.create_task(run_agent_async())
    running_agents[agent_run_id] = task

@router.post("/agent/{agent_run_id}/stop")
async def stop_agent(agent_run_id: str):
    task = running_agents[agent_run_id]
    task.cancel()
```

**方案 2: 使用 `stop_event`**
```python
stop_event = asyncio.Event()

async for msg in client.query(prompt, stop_token=stop_event):
    if stop_event.is_set():
        break
```

---

## 4. WebSocket 实现方案对比

**完成时间:** 2026-01-26

### 方案对比

| 方案 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| **Socket.IO** | 功能完整、自动重连、房间管理 | 库较大、协议开销 | 实时协作、Agent OS ⭐ |
| **ws (原生)** | 轻量、标准协议、性能高 | 需自己实现重连、房间管理 | 简单实时通信 |
| **SSE** | 单向推送简单、HTTP 兼容 | 只能单向、不支持二进制 | 单向通知 |

### Agent OS 需求分析

#### ✅ 需要 Socket.IO 的原因
1. **Agent 状态同步**（双向通信）
2. **HITL 人机交互**（房间管理）
3. **自动重连**（长时间执行不中断）
4. **多用户协作**（未来需求）

#### SSE 可以实现打断
- ✅ 可以通过额外 HTTP 请求停止
- ❌ 无法双向通信
- ❌ 无法支持复杂 HITL

### 推荐方案
**Socket.IO** - 功能完整，适合 Agent OS 的复杂交互需求

---

## 5. 数据库设计调研

**完成时间:** 2026-01-26

### 现有表结构
- `users` - 用户表
- `roles` - 角色表
- `sessions` - 会话表
- `messages` - 消息表
- `user_configs` - 用户配置表
- `business_scenarios` - 业务场景表
- `conversation_turn_configs` - 对话轮次配置表

### 需要新增的表

#### 1. Agent Runs 表
```sql
CREATE TABLE agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_run_id VARCHAR(36) UNIQUE NOT NULL,
    user_id INTEGER,
    goal TEXT,
    plan TEXT,  -- JSON
    status VARCHAR(20),  -- running, completed, failed, stopped
    started_at DATETIME,
    completed_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### 2. Agent Run Steps 表
```sql
CREATE TABLE agent_run_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_run_id VARCHAR(36) NOT NULL,
    step_number INTEGER,
    step_type VARCHAR(50),  -- planning, skill_call, hitl, etc.
    step_data JSON,
    status VARCHAR(20),
    started_at DATETIME,
    completed_at DATETIME,
    FOREIGN KEY (agent_run_id) REFERENCES agent_runs(agent_run_id)
);
```

#### 3. Skills 表（扩展）
```sql
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id VARCHAR(36) UNIQUE NOT NULL,
    name VARCHAR(100),
    description TEXT,
    version VARCHAR(20),
    input_schema JSON,
    output_schema JSON,
    is_public BOOLEAN DEFAULT FALSE,
    created_by INTEGER,
    created_at DATETIME,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

#### 4. Memory 表
```sql
CREATE TABLE agent_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id VARCHAR(36) UNIQUE NOT NULL,
    agent_run_id VARCHAR(36),
    memory_type VARCHAR(20),  -- episodic, long_term, procedural
    content TEXT,
    metadata JSON,
    created_at DATETIME,
    FOREIGN KEY (agent_run_id) REFERENCES agent_runs(agent_run_id)
);
```

---

## 6. A2UI 可视化需求分析

**完成时间:** 2026-01-26

### FR-8 需求拆解

#### 展示内容
1. **目标理解**
   - 结构化目标表示
   - 约束条件
   - 成功标准

2. **执行计划**
   - DAG/顺序/并行结构
   - 步骤依赖关系
   - 执行进度

3. **Skill 使用轨迹**
   - 调用时间线
   - 输入/输出
   - 成功/失败状态

4. **Agent 状态**
   - 当前状态（planning/acting/waiting/done）
   - 进度百分比
   - 剩余时间估算

5. **结果工件**
   - 生成的文件
   - 报告
   - 数据可视化

6. **记忆回放**
   - Episodic Memory 展示
   - 关键决策记录
   - 执行历史

### UI 原则
- **UI 不承载智能逻辑** - 只展示，不做决策
- **支持双向映射** - UI 事件 → Sub-Intent

---

## 7. mem0 集成调研

**完成时间:** 2026-01-26

### mem0.ai 评估

#### 优势
- ✅ 专为 AI Agent 设计的记忆系统
- ✅ 支持多种记忆类型（Episodic, Semantic, Procedural）
- ✅ 内置向量检索
- ✅ 与 LangChain/LlamaIndex 集成

#### 劣势
- ⚠️ 项目较新，稳定性待验证
- ⚠️ 依赖外部向量数据库
- ⚠️ 学习成本

### 自建方案评估

#### 优势
- ✅ 完全控制
- ✅ 轻量级
- ✅ 与现有架构无缝集成

#### 劣势
- ❌ 需要自己实现向量检索
- ❌ 需要设计记忆组织机制

### 推荐方案
**MVP 使用简化自建方案**
- Episodic Memory: 直接存储到 SQLite
- Long-term Memory: 使用关键词索引
- Procedural Memory: JSON 记录 Skill 使用经验
- 后续可升级到 mem0.ai 或专业向量数据库

---

## 8. Skill Marketplace 设计

**完成时间:** 2026-01-26

### 核心功能

#### 1. Skill Online Builder
- **可视化编辑器:** 拖拽式 Skill 构建
- **DSL 编辑器:** 代码式 Skill 定义
- **实时预览:** 编辑即预览
- **版本管理:** 支持 Skill 版本控制

#### 2. 在线调试
- **Sandbox 执行:** 在隔离环境中测试
- **HITL 模拟:** 模拟人工干预场景
- **日志查看:** 实时查看执行日志
- **性能分析:** 执行时间、资源使用

#### 3. 注册与版本管理
- **热加载:** 无需重启即可加载新 Skill
- **依赖管理:** Skill 之间依赖关系
- **兼容性检查:** 版本兼容性验证

#### 4. 企业 Marketplace
- **搜索:** 按名称、标签、功能搜索
- **标签:** 自定义标签分类
- **评分:** 用户评分系统
- **权限控制:** 内部/外部可见性

#### 5. 动态调用
- **即时调用:** Planner 可即时调用新 Skill
- **缓存:** 常用 Skill 缓存
- **预热:** 预加载高频 Skill

---

## 9. 技术栈决策总结

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 后端框架 | FastAPI | 现有系统已集成，异步支持良好 |
| 前端框架 | React + TypeScript | 现有前端技术栈 |
| AI SDK | Claude Agent SDK | 原生支持 HITL，功能完整 |
| 数据库 | SQLite → PostgreSQL | MVP 用 SQLite，生产升级 PostgreSQL |
| WebSocket | Socket.IO | 功能完整，自动重连，房间管理 |
| 记忆系统 | 简化自建（MVP）→ mem0.ai | 轻量启动，后续可升级 |
| 向量数据库 | ChromaDB（本地） | 本地部署简单 |
| 状态管理 | Zustand | 轻量 |
| DAG 可视化 | ECharts | 已集成 |

---

## 10. 关键风险与缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| SDK 停止机制未实现 | 无法停止长时间运行的 Agent | 使用 asyncio.Task 包装实现取消 |
| WebSocket 连接不稳定 | 用户看不到实时状态 | Socket.IO 自动重连 + 心跳检测 |
| mem0 性能问题 | 记忆检索慢 | 使用简化自建方案 + 索引优化 |
| Skill Sandbox 安全性 | 恶意 Skill 破坏系统 | Docker 容器隔离 + 资源限制 |
| 前端性能问题 | 大量事件导致卡顿 | 虚拟滚动 + 事件分页 |

---

*Last updated: 2026-01-26*
