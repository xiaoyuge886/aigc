# 前端交互说明文档

## 1. 整体架构

### 1.1 技术栈
- **框架**：React 19 + TypeScript
- **路由**：单页应用，通过 Tab 切换
- **状态管理**：React Hooks（useState、useContext）
- **UI 库**：Tailwind CSS + Lucide Icons

### 1.2 页面结构
```
App.tsx（主入口）
  ├── 首页（LandingPage）
  ├── AI 助手（ChatInterface + SessionHistory）
  ├── 编辑器（Editor）
  ├── 技能市场（SkillMarket）
  └── 管理中心（AdminDashboard，仅管理员）
```

## 2. 核心页面

### 2.1 AI 助手（ChatInterface）
**主要功能**：
- 对话界面：用户输入、AI 回复、流式显示
- 消息展示：Markdown 渲染、代码高亮、图表展示
- 工具调用可视化：TodoList、文件事件、工具调用链
- 反馈功能：点赞/点踩/纠正/重新生成
- 工作区面板：实时追踪、工具调用、文件列表、数据流

**关键组件**：
- `ChatInputArea`：输入框（支持文件上传、@提及文件）
- `MessageFeedback`：反馈按钮组（稳定弹框，无抖动）
- `TodoList`：任务列表展示
- `WorkspacePanel`：右侧工作区（realtime/tools/files/dataflow 标签页）

**交互流程**：
1. 用户输入问题 → 发送请求
2. 流式接收 AI 回复 → 实时渲染
3. 工具调用展示 → TodoList / 文件事件
4. 用户反馈 → 提交到后端

### 2.2 会话历史（SessionHistory）
**主要功能**：
- 会话列表：显示所有历史会话
- 会话详情：消息历史、工具调用、文件事件
- Session 偏好：显示会话级偏好（纠正、上下文偏好、反馈总结）

**关键信息**：
- 会话统计：总会话数、总消息数
- 会话偏好：模型分析的会话级偏好数据

### 2.3 管理中心（AdminDashboard）
**主要功能**：
- **用户管理**：用户列表、用户配置、场景授权
- **资源配置**：场景/Prompt/技能管理
- **使用统计**：会话量、消息量、费用统计
- **审计日志**：用户操作记录

**子页面**：
- `ResourceCenter`：场景/Prompt/技能的统一管理界面
- `ScenarioEditor`：场景创建/编辑
- `UserSettings`：用户配置管理
- `AdminUserLogsPage`：用户日志查看

### 2.4 资源配置中心（ResourceCenter）
**主要功能**：
- **场景管理**：列表、创建、编辑、删除
- **Prompt 管理**：系统 Prompt 模板管理
- **技能管理**：技能列表、创建、编辑

**关键操作**：
- 场景：设置默认场景（`is_default`）、配置 meta 信息
- Prompt：创建可复用的 Prompt 模板
- 技能：设置公开性（`is_public`）、绑定创建者

## 3. 关键交互

### 3.1 反馈弹框（MessageFeedback）
**交互设计**：
- 四个按钮：👍 点赞 / 👎 点踩 / ✏️ 纠正 / 🔄 重新生成
- 纠正弹框：固定居中、遮罩层、只在 X/取消/提交时关闭
- **已解决抖动问题**：移除 hover 动画、固定布局

**数据流**：
```
用户点击反馈按钮
  ↓
MessageFeedback 组件处理
  ↓
调用 submitFeedback API
  ↓
后端 FeedbackCollector 收集
```

### 3.2 场景选择（ScenarioSelector）
**交互设计**：
- 管理员可为用户配置多个场景
- 用户提问时系统自动匹配场景
- 前端不显示场景选择界面（对用户透明）

### 3.3 文件上传与提及
**交互设计**：
- 输入框支持文件上传（Paperclip 图标）
- 支持 `@文件名` 提及已上传文件
- 文件列表显示在 Files 标签页

### 3.4 工作区面板（WorkspacePanel）
**标签页**：
- **Realtime**：实时追踪对话流程
- **Tools**：工具调用详情
- **Files**：文件列表（上传/生成）
- **DataFlow**：数据流时间线

## 4. 数据流

### 4.1 对话请求
```
ChatInterface
  ↓
agentService.streamAgentQuery()
  ↓
POST /api/v1/session/query_stream
  ↓
流式接收响应
  ↓
实时渲染消息
```

### 4.2 会话历史加载
```
SessionHistory
  ↓
agentService.getSessions()
  ↓
GET /api/v1/sessions
  ↓
agentService.getConversationHistory()
  ↓
GET /api/v1/sessions/{session_id}/history
```

### 4.3 反馈提交
```
MessageFeedback
  ↓
api.submitFeedback()
  ↓
POST /api/v1/feedback
  ↓
后端 FeedbackCollector 处理
```

## 5. 状态管理

### 5.1 全局状态（App.tsx）
- `isLoggedIn`：登录状态
- `currentUser`：当前用户信息
- `activeTab`：当前激活的 Tab
- `currentSessionId`：当前会话 ID

### 5.2 本地状态（各组件）
- `ChatInterface`：messages、isLoading、toolCalls
- `SessionHistory`：sessions、selectedSession
- `AdminDashboard`：users、scenarios、prompts、skills

## 6. 关键优化

### 6.1 性能优化
- 消息列表虚拟滚动（大量消息时）
- 工具调用结果懒加载
- 会话历史分页加载

### 6.2 用户体验优化
- 反馈弹框稳定（无抖动、无意外消失）
- 消息 hover 动画已移除（避免布局抖动）
- 流式响应实时显示
- 错误提示友好

### 6.3 响应式设计
- 移动端适配（侧边栏折叠）
- 工作区面板可展开/收起
- 自适应布局

## 7. 典型交互流程

### 流程1：用户提问并反馈
1. 用户在 ChatInterface 输入问题
2. 系统自动匹配场景，返回 AI 回复
3. 用户点击 👍 或 ✏️ 纠正
4. 反馈弹框稳定显示，用户提交反馈
5. 后端收集反馈，触发偏好学习（异步）

### 流程2：管理员配置场景
1. 管理员进入"管理中心" → "资源配置"
2. 创建/编辑业务场景
3. 为用户配置可用场景列表
4. 用户下次提问时自动使用新场景

### 流程3：查看会话偏好
1. 用户在 SessionHistory 查看会话列表
2. 点击会话查看详情
3. 查看"Session 偏好"标签页
4. 显示模型分析的会话级偏好（纠正、上下文偏好等）
