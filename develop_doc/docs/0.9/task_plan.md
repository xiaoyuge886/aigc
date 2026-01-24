# Task Plan: Agent OS V1.1 实施计划
<!--
  WHAT: Agent OS 完整实施路线图，基于 v0.9-feat-doc.md PRD 文档
  WHY: 10 个核心功能需求（FR-1 到 FR-10）需要系统性拆解和执行
  WHEN: 创建于 2026-01-24
-->

## Goal
构建一个面向业务的 Agent OS V1.1，基于 Claude Agent SDK，实现目标理解、自主规划、Skill 驱动执行、人在回路、记忆系统和可视化展现的完整闭环。

## Current Phase
Phase 1: Requirements & Discovery

## Phases

### Phase 1: 需求分析与技术准备 ✅
- [x] 理解 PRD 文档（v0.9-feat-doc.md）
- [x] 分析现有系统架构
- [x] 评估 Claude Agent SDK 能力（特别是 HITL 支持）
- [x] 研究 planning-with-files 模式
- [ ] 创建详细技术设计文档
- [ ] 确定技术栈和依赖项
- **Status**: in_progress

### Phase 2: 核心基础设施（2-3周）
- [ ] 数据库设计与迁移
  - [ ] agent_runs 表
  - [ ] memories 表（mem0）
  - [ ] hitl_requests 表
  - [ ] skills_registry 表
  - [ ] agent_instances 表
- [ ] 后端核心模块架构
  - [ ] 创建 `/backend/services/agent_os/` 目录结构
  - [ ] 实现状态机定义（state_machine.py）
  - [ ] 实现基础数据模型（schemas.py）
- [ ] API 端点框架
  - [ ] 创建 `/backend/api/v1/agent_os.py`
  - [ ] 实现基础 CRUD 端点
- [ ] 前端组件架构
  - [ ] 创建 AgentOS 相关组件目录
  - [ ] 设计组件接口
- **Status**: pending
- **Dependencies**: Phase 1 完成

### Phase 3: FR-1 目标理解与澄清（1-2周）
- [ ] 实现 GoalUnderstandingService
  - [ ] 目标结构化提取
  - [ ] 约束条件识别
  - [ ] 成功标准定义
  - [ ] 置信度评估
- [ ] 实现 HITL 确认机制
  - [ ] 目标确认对话框
  - [ ] 用户修正支持
- [ ] API 端点
  - [ ] POST /agent-os/goals/understand
  - [ ] POST /agent-os/goals/confirm
- [ ] 前端组件
  - [ ] GoalUnderstandingDialog
  - [ ] GoalClarificationForm
- **Success Criteria**:
  - ✅ 目标理解准确率 > 85%
  - ✅ 置信度评估误差 < 15%
  - ✅ 用户确认响应时间 < 2s
- **Status**: pending
- **Dependencies**: Phase 2 完成

### Phase 4: FR-2 规划系统（2-3周）
- [ ] 实现 PlannerService
  - [ ] Skill 级计划生成
  - [ ] DAG 执行图构建
  - [ ] 并行执行路径优化
  - [ ] 计划动态调整
- [ ] 数据模型
  - [ ] ExecutionPlan
  - [ ] PlanNode
  - [ ] PlanNodeType（SEQUENTIAL, PARALLEL, CONDITIONAL）
- [ ] 计划可视化
  - [ ] DAG 图生成（ECharts）
  - [ ] 计划导出（JSON/Markdown）
- [ ] API 端点
  - [ ] POST /agent-os/plans/create
  - [ ] GET /agent-os/plans/{plan_id}
  - [ ] PUT /agent-os/plans/{plan_id}/adjust
- [ ] 前端组件
  - [ ] PlanVisualization（DAG 图）
  - [ ] PlanEditPanel
- **Success Criteria**:
  - ✅ 计划生成成功率 > 90%
  - ✅ DAG 构建无循环依赖
  - ✅ 并行优化准确率 > 80%
- **Status**: pending
- **Dependencies**: Phase 3 完成

### Phase 5: FR-5 状态管理与可解释性（1-2周）
- [ ] 实现 AgentRunManager
  - [ ] Agent Run 生命周期管理
  - [ ] 状态机转换（7 种状态）
  - [ ] 运行时状态追踪
- [ ] 状态持久化
  - [ ] 数据库存储
  - [ ] 状态查询 API
- [ ] 可解释性支持
  - [ ] 执行轨迹记录
  - [ ] 决策日志
  - [ ] "为什么"解释生成
- [ ] API 端点
  - [ ] POST /agent-os/runs
  - [ ] GET /agent-os/runs/{run_id}
  - [ ] POST /agent-os/runs/{run_id}/pause
  - [ ] POST /agent-os/runs/{run_id}/resume
- [ ] 前端组件
  - [ ] AgentStateDisplay
  - [ ] ExecutionTimeline
  - [ ] DecisionExplorer
- **Success Criteria**:
  - ✅ 状态转换准确率 100%
  - ✅ 执行轨迹完整性 100%
  - ✅ 状态查询延迟 < 500ms
- **Status**: pending
- **Dependencies**: Phase 2 完成

### Phase 6: FR-4 人在回路 HITL（2-3周）
- [ ] 实现 HITLHandler
  - [ ] HITL 触发规则引擎
  - [ ] 请求创建与路由
  - [ ] 响应处理与执行
- [ ] 集成 Claude Agent SDK HITL
  - [ ] can_use_tool callback 实现
  - [ ] Hook 系统集成（PreToolUse, PostToolUse）
  - [ ] Control Protocol 处理
- [ ] HITL 触发场景
  - [ ] 目标理解确认
  - [ ] 计划确认
  - [ ] 关键决策点
  - [ ] 危险操作
  - [ ] 执行失败
- [ ] API 端点
  - [ ] POST /agent-os/hitl/respond
  - [ ] GET /agent-os/hitl/requests/{request_id}
- [ ] 前端组件
  - [ ] HITLDialog（多种类型）
  - [ ] HITLRequestQueue
  - [ ] WebSocket 实时推送
- [ ] 通信机制
  - [ ] WebSocket 服务器
  - [ ] SSE 支持（备选）
  - [ ] 前端实时监听
- **Success Criteria**:
  - ✅ HITL 请求准确触发率 > 90%
  - ✅ 响应延迟 < 1s
  - ✅ 支持多种 HITL 类型
- **Status**: pending
- **Dependencies**: Phase 3, Phase 5 完成

### Phase 7: FR-6 mem0 记忆系统（2-3周）
- [ ] 技术选型
  - [ ] 评估 mem0.ai vs 自建
  - [ ] 决定实施方案
- [ ] 实现 MemoryService
  - [ ] Episodic Memory（单次 Run）
  - [ ] Long-term Memory（跨任务）
  - [ ] Procedural Memory（Skill 经验）
- [ ] 向量存储
  - [ ] Embedding 生成（OpenAI/Claude）
  - [ ] 向量数据库（ChromaDB/Qdrant）
  - [ ] 相似度检索
- [ ] 记忆参与流程
  - [ ] Planning 时检索相关记忆
  - [ ] Skill 选择时参考经验
  - [ ] Validation 时检查历史
- [ ] API 端点
  - [ ] POST /agent-os/memories
  - [ ] GET /agent-os/memories/search
  - [ ] GET /agent-os/runs/{run_id}/memories
- [ ] 前端组件
  - [ ] MemoryBrowser
  - [ ] MemorySearch
  - [ ] MemoryVisualization
- **Success Criteria**:
  - ✅ 记忆写入成功率 > 99%
  - ✅ 检索准确率 > 75%
  - ✅ 检索延迟 < 2s
- **Status**: pending
- **Dependencies**: Phase 5 完成

### Phase 8: FR-3 Skill 驱动执行（2-3周）
- [ ] 实现 SkillRuntime
  - [ ] Skill Schema 定义
  - [ ] Skill 执行引擎
  - [ ] 输入/输出验证
  - [ ] 失败处理与重试
- [ ] Skill 管理器
  - [ ] Skill 注册表
  - [ ] Skill 发现与加载
  - [ ] Skill 版本管理
- [ ] 集成现有 Skills
  - [ ] .claude/skills/ 目录集成
  - [ ] MCP Servers 集成
  - [ ] SDK MCP Servers 支持
- [ ] API 端点
  - [ ] GET /agent-os/skills
  - [ ] POST /agent-os/skills/execute
  - [ ] GET /agent-os/skills/{skill_id}
- [ ] 前端组件
  - [ ] SkillBrowser
  - [ ] SkillExecutionLog
- **Success Criteria**:
  - ✅ Skill 执行成功率 > 95%
  - ✅ 失败恢复率 > 80%
  - ✅ 支持现有 Skill 无缝集成
- **Status**: pending
- **Dependencies**: Phase 5, Phase 7 完成

### Phase 9: FR-7 多 Agent 协作（2-3周）
- [ ] 实现 AgentCoordinator
  - [ ] Agent 角色定义（PLANNER, EXECUTOR, VALIDATOR, ANALYZER）
  - [ ] Agent 实例管理
  - [ ] 事件驱动协调
- [ ] A2A 通信
  - [ ] Agent 间消息传递
  - [ ] 事件广播
  - [ ] 响应聚合
- [ ] 任务委派
  - [ ] 任务拆分
  - [ ] Agent 选择
  - [ ] 结果合并
- [ ] API 端点
  - [ ] POST /agent-os/agents
  - [ ] GET /agent-os/agents/{agent_id}
  - [ ] POST /agent-os/agents/{agent_id}/delegate
- [ ] 前端组件
  - [ ] MultiAgentView
  - [ ] AgentCommunicationGraph
- **Success Criteria**:
  - ✅ Agent 协作成功率 > 80%
  - ✅ 事件传递延迟 < 500ms
  - ✅ 支持 4+ 并行 Agent
- **Status**: pending
- **Dependencies**: Phase 8 完成

### Phase 10: FR-8 A2UI 展现层（2-3周）
- [ ] 主界面设计
  - [ ] 目标理解展示
  - [ ] 执行计划可视化（DAG）
  - [ ] Skill 轨迹展示
  - [ ] Agent 状态展示
  - [ ] 结果工件展示
  - [ ] 记忆回放
- [ ] 交互设计
  - [ ] HITL 对话框
  - [ ] 计划编辑器
  - [ ] Agent 控制面板
- [ ] 双向映射
  - [ ] UI 事件 → Sub-Intent
  - [ ] Intent → Action
- [ ] 前端组件
  - [ ] AgentOSDashboard
  - [ ] PlanVisualization（React Flow / ECharts）
  - [ ] SkillTrajectoryTimeline
  - [ ] ArtifactViewer
  - [ ] MemoryReplayPlayer
- [ ] WebSocket 集成
  - [ ] 实时状态更新
  - [ ] 事件流推送
- **Success Criteria**:
  - ✅ UI 完整性 100%（所有核心功能可视化）
  - ✅ 实时更新延迟 < 1s
  - ✅ 用户交互响应 < 200ms
- **Status**: pending
- **Dependencies**: Phase 6, Phase 9 完成

### Phase 11: FR-10 Skill Marketplace（2-3周）
- [ ] Skill Online Builder
  - [ ] 可视化 Skill 编辑器
  - [ ] DSL 编辑器（YAML/JSON）
  - [ ] Skill 模板库
- [ ] Skill Debugger
  - [ ] Sandbox 执行环境
  - [ ] 断点调试
  - [ ] 输入/输出测试
  - [ ] HITL 模拟
- [ ] Skill Registry
  - [ ] Skill 注册 API
  - [ ] 版本管理
  - [ ] 依赖管理
  - [ ] 热加载支持
- [ ] Marketplace
  - [ ] Skill 浏览与搜索
  - [ ] 标签与分类
  - [ ] 评分与评论
  - [ ] 权限控制
- [ ] API 端点
  - [ ] POST /agent-os/skills/build
  - [ ] POST /agent-os/skills/debug
  - [ ] POST /agent-os/skills/publish
  - [ ] GET /agent-os/marketplace/skills
  - [ ] POST /agent-os/marketplace/skills/{skill_id}/install
- [ ] 前端组件
  - [ ] SkillBuilder
  - [ ] SkillDebugger
  - [ ] SkillMarketplace
  - [ ] SkillInstaller
- **Success Criteria**:
  - ✅ Skill 构建成功率 > 90%
  - ✅ 热加载成功率 100%
  - ✅ Marketplace 功能完整
- **Status**: pending
- **Dependencies**: Phase 8 完成

### Phase 12: FR-9 安全与可控（1-2周）
- [ ] Sandbox 集成
  - [ ] Docker 容器隔离
  - [ ] 文件系统访问控制
  - [ ] 网络访问控制
- [ ] 权限管理
  - [ ] 用户权限
  - [ ] Skill 权限
  - [ ] 资源配额
- [ ] 审计日志
  - [ ] 全链路日志记录
  - [ ] 敏感操作审计
  - [ ] 日志查询 API
- [ ] API 端点
  - [ ] GET /agent-os/audit/logs
  - [ ] GET /agent-os/permissions
- **Success Criteria**:
  - ✅ Sandbox 隔离有效性 100%
  - ✅ 审计日志完整性 100%
- **Status**: pending
- **Dependencies**: Phase 8, Phase 10 完成

### Phase 13: 集成测试与优化（2-3周）
- [ ] 端到端测试
  - [ ] 完整 Agent Run 流程
  - [ ] 多 Agent 协作流程
  - [ ] HITL 流程
  - [ ] Skill Marketplace 流程
- [ ] 性能优化
  - [ ] 数据库查询优化
  - [ ] API 响应优化
  - [ ] 前端渲染优化
- [ ] 压力测试
  - [ ] 并发 Agent Run
  - [ ] 大量记忆检索
  - [ ] WebSocket 连接
- [ ] 用户验收测试
  - [ ] 业务场景测试
  - [ ] 易用性测试
- **Success Criteria**:
  - ✅ 端到端测试通过率 100%
  - ✅ API 平均响应 < 500ms
  - ✅ 支持 10+ 并发 Agent Run
- **Status**: pending
- **Dependencies**: Phase 12 完成

### Phase 14: MVP 交付与文档（1-2周）
- [ ] MVP 交付
  - [ ] 单一业务场景验证
  - [ ] 3-5 核心 Skill
  - [ ] mem0 记忆完整
  - [ ] A2UI 全流程展示
  - [ ] Skill Marketplace 可用
- [ ] 文档编写
  - [ ] 系统架构文档
  - [ ] API 文档
  - [ ] 部署文档
  - [ ] 用户手册
  - [ ] 开发者指南
- [ ] 部署准备
  - [ ] Docker 镜像
  - [ ] K8s 配置
  - [ ] CI/CD 流程
- **Status**: pending
- **Dependencies**: Phase 13 完成

## Key Questions

1. **mem0 实施方案**：使用 mem0.ai 库还是自建？
   - 优势对比
   - 成本评估
   - 集成复杂度

2. **多 Agent 并发**：如何保证 10+ 并发 Agent 的性能？
   - 资源隔离
   - 负载均衡
   - 降级策略

3. **Skill 热加载**：如何在不停机的情况下动态加载 Skill？
   - 动态导入机制
   - 版本兼容性检查
   - 回滚策略

4. **Sandbox 隔离**：如何平衡安全性与性能？
   - 容器开销
   - 资源限制
   - 通信优化

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 待定 | 待 Phase 1 完成后确定 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (无错误) | - | - |

## Notes
- 本计划遵循 Planning-with-Files 模式
- 每个阶段完成后立即更新 task_plan.md
- 重大决策记录到 findings.md
- 详细执行日志记录到 progress.md
- 使用 3-Strike Error Protocol 处理失败

## MVP Success Criteria (V1)
- ✅ 单一业务场景完整 Run
- ✅ 单 Agent Run 闭环完整
- ✅ 3-5 核心 Skill 可用
- ✅ mem0 记忆写入与回放
- ✅ A2UI 全流程展示
- ✅ Skill 在线生成 / 调试 / Marketplace 可用
