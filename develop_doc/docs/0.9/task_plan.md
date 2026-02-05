# Task Plan - Agent OS V1.1 Implementation

**Project:** Agent OS V1.1 - 基于 Claude Agent SDK 的业务级智能工作系统

**Goal:** 构建一个面向业务侧的 Agent OS，支持目标理解、规划、Skill 驱动执行、HITL、记忆系统和 A2UI 可视化

**MVP Success Criteria:**
- ✅ 单一业务场景完整闭环
- ✅ 3-5 个核心 Skill 可用
- ✅ mem0 记忆写入与回放
- ✅ A2UI 全流程展示
- ✅ Skill Online Builder + Marketplace 基础功能

---

## Phase 1: 需求分析与技术调研 (COMPLETED)

**Status:** ✅ Complete

**Deliverables:**
- [x] PRD 文档已分析
- [x] 现有系统架构已评估
- [x] Claude Agent SDK 集成方式已确认
- [x] 技术栈决策已记录

**Key Findings:**
- 现有 FastAPI + React + Claude Agent SDK 架构良好
- SDK 支持 can_use_tool callback 和 Hook System（HITL 基础）
- 需要实现：Planning System, mem0 集成, A2UI, Skill Marketplace
- WebSocket/Socket.IO 适合实时事件推送

---

## Phase 2: 核心抽象设计 (IN_PROGRESS)

**Status:** 🔄 In Progress

**Objectives:**
- 定义 Agent Run, Skill, Memory 核心数据模型
- 设计 Agent State Machine
- 定义 A2UI Event Schema
- 设计 mem0 集成接口

**Tasks:**
- [ ] 2.1 设计 Agent Run 数据模型（数据库表）
  - `agent_runs` 表
  - `agent_run_steps` 表
  - `agent_run_artifacts` 表
- [ ] 2.2 设计 Skill Schema
  - `skills` 表（扩展现有）
  - `skill_versions` 表
  - `skill_marketplace` 表
- [ ] 2.3 设计 mem0 集成
  - Episodic Memory 表结构
  - Long-term Memory 表结构
  - 检索接口定义
- [ ] 2.4 设计 Agent State Machine
  - States: idle, planning, acting, waiting_approval, completed, failed
  - Transitions: trigger conditions, actions
- [ ] 2.5 设计 A2UI Event Schema
  - Event types: goal_understood, plan_created, skill_call, etc.
  - Event format: JSON schema

**Files to Create:**
- `backend/models/agent_run.py` - Agent Run 数据模型
- `backend/models/skill.py` - Skill 数据模型
- `backend/models/memory.py` - Memory 数据模型
- `backend/services/agent_state_machine.py` - 状态机实现
- `backend/services/a2ui_event_schema.py` - A2UI 事件定义

---

## Phase 3: 后端核心服务实现 (PENDING)

**Status:** ⏳ Pending

**Objectives:**
- 实现 Agent Run 协调器
- 实现 Planning System（基础版）
- 实现 mem0 集成
- 实现 Skill Runtime
- 实现 A2UI Event Collector

**Tasks:**

### 3.1 Agent Run Coordinator
- [ ] 创建 `AgentRunCoordinator` 类
- [ ] 实现 run 生命周期管理
- [ ] 集成 Claude SDK query
- [ ] 实现状态机驱动

### 3.2 Planning System (基础版)
- [ ] 实现规则基础的 Planner
  - 目标 → Skill 选择
  - 依赖顺序分析
  - 并行执行识别
- [ ] 支持计划调整
- [ ] 计划持久化

### 3.3 mem0 集成
- [ ] 选择 mem0.ai 或自建方案
- [ ] 实现 Episodic Memory 写入
  - 记录每个 Agent Run
  - 保存步骤、决策、结果
- [ ] 实现 Memory 检索
  - 语义搜索
  - 相关性排序
- [ ] 集成到 Planning 和 Skill Selection

### 3.4 Skill Runtime
- [ ] 扩展现有 Skill 系统
- [ ] 实现 Skill Schema 验证
- [ ] 实现 Sandbox 集成（Docker）
- [ ] 实现失败处理与重试
- [ ] 实现热加载

### 3.5 A2UI Event Collector
- [ ] 创建 `A2UICollector` 类
- [ ] 实现事件收集与格式化
- [ ] 集成 Socket.IO 推送
- [ ] 实现事件持久化

**Files to Create:**
- `backend/services/agent_run_coordinator.py`
- `backend/services/planner.py`
- `backend/services/memory_service.py`
- `backend/services/skill_runtime.py`
- `backend/services/a2ui_collector.py`

---

## Phase 4: API 层实现 (PENDING)

**Status:** ⏳ Pending

**Objectives:**
- 暴露 Agent Run 管理 API
- 暴露 Skill Marketplace API
- 集成 WebSocket (Socket.IO)
- 实现 HITL 接口

**Tasks:**

### 4.1 Agent Run APIs
- [ ] `POST /api/v1/agent/runs` - 启动 Agent Run
- [ ] `GET /api/v1/agent/runs/{run_id}` - 获取 Run 状态
- [ ] `POST /api/v1/agent/runs/{run_id}/stop` - 停止 Run
- [ ] `POST /api/v1/agent/runs/{run_id}/approve` - HITL 批准
- [ ] `POST /api/v1/agent/runs/{run_id}/reject` - HITL 拒绝

### 4.2 Skill Marketplace APIs
- [ ] `GET /api/v1/skills` - 列出所有 Skills
- [ ] `POST /api/v1/skills` - 创建 Skill
- [ ] `GET /api/v1/skills/{skill_id}` - 获取 Skill 详情
- [ ] `PUT /api/v1/skills/{skill_id}` - 更新 Skill
- [ ] `DELETE /api/v1/skills/{skill_id}` - 删除 Skill
- [ ] `POST /api/v1/skills/{skill_id}/debug` - 在线调试 Skill
- [ ] `POST /api/v1/skills/{skill_id}/publish` - 发布到 Marketplace

### 4.3 Memory APIs
- [ ] `GET /api/v1/memory/search` - 搜索记忆
- [ ] `POST /api/v1/memory` - 写入记忆
- [ ] `GET /api/v1/memory/{memory_id}` - 获取记忆详情

### 4.4 WebSocket (Socket.IO)
- [ ] 集成 `python-socketio` 到 FastAPI
- [ ] 实现 Socket.IO 事件处理器
  - `join_agent_run` - 加入 Run 房间
  - `leave_agent_run` - 离开 Run 房间
  - `a2ui_event` - 接收 A2UI 事件
  - `hitl_response` - HITL 响应

**Files to Modify:**
- `backend/main.py` - 添加 Socket.IO
- `backend/api/v1/agent_runs.py` - Agent Run APIs
- `backend/api/v1/skills.py` - Skill APIs
- `backend/api/v1/memory.py` - Memory APIs

---

## Phase 5: 前端 A2UI 组件实现 (PENDING)

**Status:** ⏳ Pending

**Objectives:**
- 实现 A2UI Dashboard
- 实现各个可视化组件
- 集成 Socket.IO 客户端
- 实现 HITL 交互界面

**Tasks:**

### 5.1 A2UI 核心组件
- [ ] `A2UIDashboard` - 主容器
- [ ] `AgentStatusCard` - Agent 状态卡片
- [ ] `ExecutionPlan` - 执行计划可视化
- [ ] `SkillTimeline` - Skill 调用时间线
- [ ] `ToolTrace` - 工具调用追踪
- [ ] `ResultArtifacts` - 结果工件展示
- [ ] `MemoryReplay` - 记忆回放

### 5.2 HITL 交互组件
- [ ] `HITLModal` - HITL 确认对话框
- [ ] `ToolApprovalPanel` - 工具批准面板
- [ ] `PlanAdjustmentPanel` - 计划调整面板

### 5.3 Skill Marketplace UI
- [ ] `SkillBrowser` - Skill 浏览器
- [ ] `SkillBuilder` - Skill 在线编辑器
- [ ] `SkillDebugger` - Skill 调试器

### 5.4 Socket.IO 集成
- [ ] 安装 `socket.io-client`
- [ ] 创建 `a2uiService` - Socket.IO 服务封装
- [ ] 实现事件监听与处理

**Files to Create:**
- `frontend/aigc-frontend/components/a2ui/A2UIDashboard.tsx`
- `frontend/aigc-frontend/components/a2ui/AgentStatusCard.tsx`
- `frontend/aigc-frontend/components/a2ui/ExecutionPlan.tsx`
- `frontend/aigc-frontend/components/a2ui/SkillTimeline.tsx`
- `frontend/aigc-frontend/components/a2ui/ToolTrace.tsx`
- `frontend/aigc-frontend/components/a2ui/ResultArtifacts.tsx`
- `frontend/aigc-frontend/components/a2ui/MemoryReplay.tsx`
- `frontend/aigc-frontend/components/a2ui/HITLModal.tsx`
- `frontend/aigc-frontend/services/a2uiService.ts`
- `frontend/aigc-frontend/services/skillService.ts`

---

## Phase 6: Skill 开发 (MVP) (PENDING)

**Status:** ⏳ Pending

**Objectives:**
- 开发 3-5 个核心 Skill
- 验证 Skill Runtime
- 支持在线调试

**Tasks:**

### 6.1 核心 Skill 开发
- [ ] `DocumentAnalyzer` - 文档分析 Skill
- [ ] `DataExtractor` - 数据抽取 Skill
- [ ] `ReportGenerator` - 报告生成 Skill
- [ ] `WebResearcher` - 网络研究 Skill
- [ ] `FileOrganizer` - 文件整理 Skill

### 6.2 Skill 在线工具
- [ ] Skill Builder 可视化编辑器
- [ ] Skill 调试器
- [ ] Skill 测试框架

**Files to Create:**
- `.claude/skills/document_analyzer/`
- `.claude/skills/data_extractor/`
- `.claude/skills/report_generator/`

---

## Phase 7: 测试与集成 (PENDING)

**Status:** ⏳ Pending

**Objectives:**
- 单元测试
- 集成测试
- 端到端测试
- 性能测试

**Tasks:**
- [ ] 7.1 后端服务单元测试
- [ ] 7.2 前端组件测试
- [ ] 7.3 API 集成测试
- [ ] 7.4 E2E 场景测试
- [ ] 7.5 性能压测
- [ ] 7.6 安全测试

---

## Phase 8: 部署与监控 (PENDING)

**Status:** ⏳ Pending

**Objectives:**
- Docker 容器化
- 生产环境部署
- 监控与告警
- 文档完善

**Tasks:**
- [ ] 8.1 更新 docker-compose 配置
- [ ] 8.2 配置环境变量
- [ ] 8.3 部署到生产环境
- [ ] 8.4 配置日志收集
- [ ] 8.5 配置监控指标
- [ ] 8.6 编写用户文档
- [ ] 8.7 编写开发者文档

---

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| | | |

---

## Technical Decisions

| Decision | Options | Choice | Rationale |
|----------|---------|--------|-----------|
| WebSocket 实现 | Socket.IO vs ws vs SSE | Socket.IO | 功能完整，自动重连，房间管理 |
| mem0 实现 | mem0.ai vs 自建 | 待定 | 需要评估 |
| 向量数据库 | ChromaDB vs Qdrant vs Pinecone | ChromaDB | 本地部署简单 |
| 前端状态管理 | Redux vs Zustand vs Context | Zustand | 轻量 |
| DAG 可视化 | React Flow vs ECharts vs D3 | ECharts | 已集成 |

---

## Next Steps

1. **Complete Phase 2** - 设计核心抽象
2. **Start Phase 3** - 实现后端核心服务
3. **Implement MVP Skills** - 开发 3-5 个核心 Skill

---

*Last updated: 2026-01-26*
