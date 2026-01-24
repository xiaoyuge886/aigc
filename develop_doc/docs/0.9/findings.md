# Findings & Decisions - Agent OS V1.1
<!--
  WHAT: Agent OS 实施过程中的研究发现和技术决策
  WHY: 记录关键发现，支持后续决策
-->

## Requirements
- 基于 v0.9-feat-doc.md PRD 文档实施 Agent OS V1.1
- 实现 10 个核心功能需求（FR-1 到 FR-10）
- 集成到现有 FastAPI + React + Claude Agent SDK 架构
- 支持单一业务场景 MVP 验证

## Research Findings

### 现有系统架构分析
**完成时间**: 2026-01-24

**后端架构**:
- FastAPI 0.115.0 + SQLAlchemy 2.0 + Claude Agent SDK
- 数据库: SQLite (可升级至 PostgreSQL)
- 已集成 Claude Agent SDK (无状态 + 有状态两种模式)
- 关键文件:
  - `/backend/services/agent_service.py` - Agent 服务
  - `/backend/services/session_manager.py` - 会话管理
  - `/backend/services/scenario_matcher.py` - 场景匹配

**前端架构**:
- React 19.2.0 + TypeScript + Vite 6.2.0
- 关键文件:
  - `/frontend/aigc-frontend/components/ChatInterface.tsx`
  - `/frontend/aigc-frontend/services/agentService.ts`

**现有能力**:
- ✅ Claude Agent SDK 集成（流式响应、工具调用）
- ✅ 会话管理（多用户、历史记录）
- ✅ 技能系统（.claude/skills/ 目录）
- ✅ 场景匹配引擎
- ✅ 文件上传管理（MinIO）
- ✅ 前端聊天界面

**缺失能力（需实现）**:
- ❌ 目标理解与澄清模块（FR-1）
- ❌ 规划系统（FR-2）
- ❌ mem0 记忆系统（FR-6）
- ❌ 多 Agent 协调机制（FR-7）
- ❌ Agent Run 状态机（FR-5）
- ❌ HITL 机制（FR-4）
- ❌ Skill Marketplace（FR-10）
- ❌ A2UI 可视化（FR-8）

### Claude Agent SDK HITL 支持分析
**完成时间**: 2026-01-24

**核心发现**:
- ✅ **can_use_tool callback**: SDK 原生支持工具权限回调
- ✅ **Hook System**: 支持 PreToolUse, PostToolUse, UserPromptSubmit, Stop 等 6 种钩子
- ✅ **Control Protocol**: 双向控制协议（control_request/control_response）
- ✅ **Permission Modes**: default, acceptEdits, plan, bypassPermissions
- ⚠️ **无内置 HITL UI**: 需自己实现前端 HITL 组件

**HITL 实现方式**:
1. **工具级 HITL**: 基于 can_use_tool callback
2. **钩子级 HITL**: 基于 PreToolUse/PostToolUse hooks
3. **阶段级 HITL**: 基于 UserPromptSubmit hook（完整 Agent OS）

**源码位置**:
- `/Users/hehe/pycharm_projects/aigc/.venv/lib/python3.11/site-packages/claude_agent_sdk/`

### Planning-with-Files Skill 分析
**完成时间**: 2026-01-24

**核心模式**:
```
Context Window = RAM (volatile, limited)
Filesystem = Disk (persistent, unlimited)

→ Anything important gets written to disk.
```

**三个核心文件**:
1. `task_plan.md` - 阶段、进度、决策、错误追踪
2. `findings.md` - 研究发现、技术决策
3. `progress.md` - 会话日志、测试结果

**Hook 自动化**:
- **PreToolUse**: 决策前自动刷新计划（读取 task_plan.md 前 30 行）
- **PostToolUse**: 文件更新后提醒更新状态
- **Stop**: 停止前检查所有阶段是否完成

**Session Recovery**:
- v2.2.0+ 支持 /clear 后自动恢复未同步上下文
- 通过 session-catchup.py 脚本实现

**与 Agent OS 关系**:
- ✅ 支持 FR-2（规划系统）模式
- ✅ 支持 FR-5（状态管理）文件追踪
- ✅ 支持 FR-6（mem0）的长期记忆存储

## Technical Decisions

### 待决策项

| 决策项 | 选项 | 建议 | 状态 |
|--------|------|------|------|
| **mem0 实施** | mem0.ai vs 自建 | 待评估 | pending |
| **向量数据库** | ChromaDB vs Qdrant vs Pinecone | ChromaDB（本地部署简单） | pending |
| **前端状态管理** | Redux vs Zustand vs Context | Zustand（轻量） | pending |
| **WebSocket 实现** | Socket.IO vs ws vs SSE | Socket.IO（功能完整） | pending |
| **多 Agent 并发** | asyncio concurrent.futures | asyncio（原生） | pending |
| **Sandbox 隔离** | Docker vs gVisor vs Firecracker | Docker（成熟） | pending |
| **DAG 可视化** | React Flow vs ECharts vs D3 | ECharts（已集成） | pending |

### 已确定决策

| 决策 | 理由 |
|------|------|
| 使用 FastAPI | 现有系统已集成，异步支持良好 |
| 使用 React + TypeScript | 现有前端技术栈 |
| 使用 Claude Agent SDK | 原生支持 HITL，功能完整 |
| 使用 SQLite → PostgreSQL | MVP 用 SQLite，生产升级 PostgreSQL |
| 使用 Planning-with-Files 模式 | 已验证有效，支持 Agent OS 需求 |

## Issues Encountered
| 问题 | 解决方案 |
|------|----------|
| Claude Agent SDK 文档路径不一致 | 使用绝对路径访问 |
| session-catchup.py 路径问题 | 手动指定完整路径 |

## Resources

### PRD 文档
- `/Users/hehe/pycharm_projects/aigc/develop_doc/docs/0.9/v0.9-feat-doc.md`

### 技术文档
- Agent OS 集成方案: `/Users/hehe/pycharm_projects/aigc/AGENT_OS_INTEGRATION_PLAN.md`
- HITL 实现指南: `/Users/hehe/pycharm_projects/aigc/HITL_IMPLEMENTATION_GUIDE.md`

### 代码位置
- 后端 Agent 服务: `/Users/hehe/pycharm_projects/aigc/backend/services/agent_service.py`
- 前端 Agent 服务: `/Users/hehe/pycharm_projects/aigc/frontend/aigc-frontend/services/agentService.ts`
- 现有 Skills: `/Users/hehe/pycharm_projects/aigc/.claude/skills/`

### SDK 源码
- Claude Agent SDK: `/Users/hehe/pycharm_projects/aigc/.venv/lib/python3.11/site-packages/claude_agent_sdk/`

### 外部资源
- mem0.ai: https://github.com/meetmenai/mem0ai
- ChromaDB: https://www.trychroma.com/
- React Flow: https://reactflow.dev/
- ECharts: https://echarts.apache.org/

## Visual/Browser Findings

### Claude Agent SDK 类型定义
**文件**: `types.py:155-157`

```python
CanUseTool = Callable[
    [str, dict[str, Any], ToolPermissionContext],
    Awaitable[PermissionResult]
]
```

**关键类型**:
- `PermissionResultAllow`: 允许执行，可修改输入
- `PermissionResultDeny`: 拒绝执行，提供原因
- `ToolPermissionContext`: 包含权限建议

### Hook 系统类型
**支持的事件**:
- `PreToolUse`: 工具使用前
- `PostToolUse`: 工具使用后
- `UserPromptSubmit`: 用户提交提示
- `Stop`: 停止时
- `SubagentStop`: 子 Agent 停止
- `PreCompact`: 压缩前

## MVP Priority Matrix

### P0（必须有）
- FR-1: 目标理解与澄清
- FR-2: 规划系统
- FR-3: Skill 驱动执行（基础）
- FR-4: HITL（工具级）
- FR-5: 状态管理

### P1（重要）
- FR-6: mem0 记忆系统
- FR-7: 多 Agent 协作
- FR-8: A2UI 展现层（基础）

### P2（可选）
- FR-9: 安全与可控
- FR-10: Skill Marketplace

## Next Steps

1. **Phase 1 完成**（当前）
   - ✅ 需求分析完成
   - ✅ 技术调研完成
   - [ ] 创建技术设计文档
   - [ ] 确定技术栈决策

2. **Phase 2 准备**
   - 数据库设计
   - 后端架构搭建
   - 前端组件设计

3. **技术选型**
   - mem0 vs 自建
   - 向量数据库选择
   - WebSocket 方案

---
*Last updated: 2026-01-24*
