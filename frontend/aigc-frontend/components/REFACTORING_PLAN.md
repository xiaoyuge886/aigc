# ChatInterface 组件重构计划

## 当前状态
- **总行数**: 3601 行
- **ChatInterface 组件**: 3455 行（96%）
- **主要问题**: "上帝组件"（God Component），包含过多职责

## 重构目标
1. 提高代码可维护性
2. 提高代码可测试性
3. 提高代码可复用性
4. 便于开源和协作

## 重构策略

### 1. 目录结构

```
components/
├── chat/
│   ├── ChatInterface.tsx          # 主组件（简化后约 200-300 行）
│   ├── hooks/
│   │   ├── useChatSession.ts      # 会话管理
│   │   ├── useMessages.ts         # 消息管理
│   │   ├── useFileManagement.ts   # 文件管理
│   │   ├── useToolCalls.ts        # 工具调用
│   │   ├── useMentions.ts         # @ 提及功能
│   │   └── useStreamResponse.ts   # 流式响应
│   ├── tabs/
│   │   ├── RealtimeTab.tsx        # 实时对话标签页
│   │   ├── BrowserTab.tsx         # 浏览器标签页
│   │   ├── FilesTab.tsx           # 文件标签页
│   │   ├── ToolsTab.tsx           # 工具标签页
│   │   └── DataFlowTab.tsx        # 数据流标签页
│   ├── components/
│   │   ├── ChatToolbar.tsx        # 工具栏
│   │   ├── ChatInputArea.tsx      # 输入区域
│   │   ├── MessageArea.tsx        # 消息显示区域
│   │   └── RecommendationArea.tsx # 推荐问题区域
│   └── utils/
│       ├── messageUtils.ts        # 消息相关工具函数
│       ├── toolCallUtils.ts       # 工具调用相关工具函数
│       └── fileUtils.ts           # 文件相关工具函数
```

### 2. 功能模块拆分

#### 2.1 自定义 Hooks

**useChatSession.ts** (~150 行)
- 会话 ID 管理
- 会话初始化
- 会话清理
- localStorage 同步

**useMessages.ts** (~200 行)
- 消息状态管理
- 消息加载（分页）
- 消息添加/更新
- 历史消息管理

**useFileManagement.ts** (~150 行)
- 文件列表管理
- 文件上传
- 文件预览
- 文件删除

**useToolCalls.ts** (~200 行)
- 工具调用解析
- 工具调用状态管理
- TodoList 提取
- 工具调用显示

**useMentions.ts** (~100 行)
- @ 提及功能
- 文件下拉菜单
- 提及查询
- 键盘导航

**useStreamResponse.ts** (~300 行)
- 流式响应处理
- 消息实时更新
- 工具调用收集
- 完成处理

#### 2.2 子组件

**RealtimeTab.tsx** (~400 行)
- 消息列表显示
- 推荐问题显示
- 输入区域

**BrowserTab.tsx** (~200 行)
- 浏览器内容显示
- 工具调用详情

**FilesTab.tsx** (~300 行)
- 文件列表
- 文件预览
- 文件操作

**ToolsTab.tsx** (~400 行)
- 工具调用列表
- 工具调用详情
- TodoList 显示

**DataFlowTab.tsx** (~200 行)
- 数据流图显示
- 对话轮次选择

#### 2.3 工具函数

**messageUtils.ts**
- `getMessageDisplay()` - 消息显示逻辑
- `parseToolCalls()` - 工具调用解析
- `extractTodosFromToolCalls()` - TodoList 提取

**toolCallUtils.ts**
- 工具调用格式化
- 工具调用状态判断
- 工具调用合并

**fileUtils.ts**
- 文件类型判断
- 文件预览逻辑
- 文件上传处理

### 3. 重构步骤

1. ✅ 分析当前代码结构
2. ⏳ 创建目录结构
3. ⏳ 提取工具函数
4. ⏳ 创建自定义 hooks
5. ⏳ 创建子组件
6. ⏳ 重构主组件
7. ⏳ 测试和优化

### 4. 预期效果

- **ChatInterface.tsx**: 200-300 行（从 3455 行减少到约 90%）
- **代码可维护性**: 显著提高
- **代码可测试性**: 提高（hooks 和 utils 可单独测试）
- **代码可复用性**: 提高（hooks 和组件可在其他地方复用）

## 注意事项

1. 保持向后兼容，不破坏现有功能
2. 逐步重构，每次提交一个模块
3. 保持类型安全（TypeScript）
4. 添加必要的注释和文档
