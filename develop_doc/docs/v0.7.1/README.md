# v0.7.1 开发文档索引

## 📚 文档列表

### 1. [产品概览](./PRODUCT_OVERVIEW.md)
**面向对象**：产品经理、业务方、领导

**内容**：
- 产品定位与目标
- 目标用户与典型场景
- 功能清单（用户/管理员）
- 核心业务流程
- 版本状态与规划

**适用场景**：产品汇报、需求评审、对外介绍

---

### 2. [技术架构概览](./ARCHITECTURE_OVERVIEW.md)
**面向对象**：技术团队、架构师

**内容**：
- 整体架构（前端/后端/模型层）
- 核心数据表结构
- 主要服务模块
- 自我进化链路
- 会话主链路

**适用场景**：技术评审、新人 onboarding、架构讨论

---

### 3. [对话与场景体系设计](./SCENARIO_SYSTEM_DESIGN.md)
**面向对象**：后端开发、系统设计

**内容**：
- Session / ConversationTurn / Message 关系
- 场景匹配流程（ScenarioMatcher）
- Prompt 组合逻辑（PromptComposer）
- 配置合并优先级
- 数据流转

**适用场景**：功能开发、问题排查、设计评审

---

### 4. [自我进化功能技术说明](./SELF_EVOLUTION_DESIGN.md)
**面向对象**：后端开发、算法工程师

**内容**：
- 整体架构（数据层/服务层）
- FeedbackCollector / PreferenceLearner / PromptEvolver
- 工作流程（反馈收集、偏好学习、Prompt 进化）
- 触发机制
- 性能优化

**适用场景**：功能开发、算法优化、问题排查

---

### 5. [前端交互说明](./FRONTEND_INTERACTION.md)
**面向对象**：前端开发、UI/UX

**内容**：
- 整体架构（技术栈、页面结构）
- 核心页面（ChatInterface、SessionHistory、AdminDashboard）
- 关键交互（反馈弹框、场景选择、文件上传）
- 数据流
- 状态管理

**适用场景**：前端开发、交互优化、问题排查

---

### 6. [API 参考文档](./API_REFERENCE.md)
**面向对象**：前后端开发、测试

**内容**：
- 认证方式
- 核心对话接口
- 反馈接口
- 场景管理接口
- 偏好查询接口
- 定时任务接口
- 错误码

**适用场景**：接口联调、API 测试、集成开发

---

### 7. [部署与运维文档](./DEPLOYMENT.md)
**面向对象**：运维、DevOps

**内容**：
- 环境要求
- 本地开发部署
- 生产环境部署（Docker）
- 数据库迁移
- 定时任务
- 监控与日志
- 备份与恢复
- 故障排查
- 性能优化
- 安全建议

**适用场景**：环境搭建、生产部署、问题排查

---

## 🎯 快速导航

### 按角色查找

**产品/业务方**：
1. [产品概览](./PRODUCT_OVERVIEW.md)

**技术负责人/架构师**：
1. [产品概览](./PRODUCT_OVERVIEW.md)
2. [技术架构概览](./ARCHITECTURE_OVERVIEW.md)

**后端开发**：
1. [技术架构概览](./ARCHITECTURE_OVERVIEW.md)
2. [对话与场景体系设计](./SCENARIO_SYSTEM_DESIGN.md)
3. [自我进化功能技术说明](./SELF_EVOLUTION_DESIGN.md)
4. [API 参考文档](./API_REFERENCE.md)

**前端开发**：
1. [技术架构概览](./ARCHITECTURE_OVERVIEW.md)
2. [前端交互说明](./FRONTEND_INTERACTION.md)
3. [API 参考文档](./API_REFERENCE.md)

**运维/DevOps**：
1. [部署与运维文档](./DEPLOYMENT.md)
2. [技术架构概览](./ARCHITECTURE_OVERVIEW.md)

---

## 📝 文档更新说明

- **版本**：v0.7.1-dev-feat
- **最后更新**：2025-01-05
- **基于代码**：当前仓库 `dev` 分支，tag `v0.7.1-dev-feat`

**文档原则**：
- 以**当前代码实现**为准
- 参考 `devolop_doc` 历史文档
- 保持**言简意赅**，便于快速查阅

---

## 🔗 相关资源

- **代码仓库**：当前项目根目录
- **历史文档**：`/devolop_doc/docs/`（可能包含过时内容）
- **架构设计**：`/SYSTEM_EVOLUTION_ARCHITECTURE.md`
- **部署配置**：`/deploy/`

---

## 💡 使用建议

1. **首次阅读**：建议按顺序阅读 1 → 2 → 3 → 4
2. **功能开发**：根据功能模块选择对应文档
3. **问题排查**：先看相关设计文档，再看部署文档
4. **对外汇报**：使用产品概览 + 技术架构概览
