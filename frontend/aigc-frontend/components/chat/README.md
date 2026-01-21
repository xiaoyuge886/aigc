# Chat 模块

这是 ChatInterface 组件的重构版本，采用模块化设计，提高代码可维护性和可测试性。

## 目录结构

```
chat/
├── ChatInterface.tsx          # 主组件（简化后约 200-300 行）
├── hooks/                     # 自定义 Hooks
│   ├── useChatSession.ts      # 会话管理
│   ├── useMessages.ts         # 消息管理
│   ├── useFileManagement.ts   # 文件管理
│   ├── useToolCalls.ts        # 工具调用
│   ├── useMentions.ts         # @ 提及功能
│   └── useStreamResponse.ts   # 流式响应
├── tabs/                      # 标签页组件
│   ├── RealtimeTab.tsx        # 实时对话标签页
│   ├── BrowserTab.tsx         # 浏览器标签页
│   ├── FilesTab.tsx           # 文件标签页
│   ├── ToolsTab.tsx           # 工具标签页
│   └── DataFlowTab.tsx        # 数据流标签页
├── components/                # 子组件
│   ├── ChatToolbar.tsx        # 工具栏
│   ├── ChatInputArea.tsx      # 输入区域
│   ├── MessageArea.tsx        # 消息显示区域
│   └── RecommendationArea.tsx # 推荐问题区域
└── utils/                     # 工具函数
    ├── messageUtils.ts        # 消息相关工具函数
    ├── toolCallUtils.ts       # 工具调用相关工具函数
    └── fileUtils.ts           # 文件相关工具函数
```

## 重构原则

1. **单一职责原则**：每个模块只负责一个功能
2. **可测试性**：Hooks 和 Utils 可单独测试
3. **可复用性**：组件和 Hooks 可在其他地方复用
4. **类型安全**：使用 TypeScript 确保类型安全

## 使用方式

重构完成后，主组件将使用这些模块：

```tsx
import { useChatSession } from './hooks/useChatSession';
import { useMessages } from './hooks/useMessages';
import { RealtimeTab } from './tabs/RealtimeTab';
// ...

export const ChatInterface: React.FC<ChatInterfaceProps> = (props) => {
  const session = useChatSession(props);
  const messages = useMessages(session.sessionId);
  // ...
  
  return (
    <div>
      <RealtimeTab {...realtimeProps} />
      {/* ... */}
    </div>
  );
};
```
