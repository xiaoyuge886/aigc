# 待办事项列表

使用 Claude Agent SDK 跟踪和显示待办事项，实现有组织的任务管理

---

待办事项跟踪提供了一种结构化的方式来管理任务并向用户显示进度。Claude Agent SDK 包含内置的待办事项功能，有助于组织复杂的工作流程并让用户了解任务进展情况。

### 待办事项生命周期

待办事项遵循可预测的生命周期：
1. **创建** 为 `pending` 状态，当任务被识别时
2. **激活** 为 `in_progress` 状态，当工作开始时
3. **完成** 当任务成功完成时
4. **移除** 当组中的所有任务都完成时

### 何时使用待办事项

SDK 会自动为以下情况创建待办事项：
- **复杂的多步骤任务** 需要 3 个或更多不同的操作
- **用户提供的任务列表** 当提到多个项目时
- **非平凡的操作** 受益于进度跟踪
- **明确请求** 当用户要求待办事项组织时

## 示例

### 监控待办事项变化

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

for await (const message of query({
  prompt: "优化我的 React 应用性能并使用待办事项跟踪进度",
  options: { maxTurns: 15 }
})) {
  // 待办事项更新会反映在消息流中
  if (message.type === "tool_use" && message.name === "TodoWrite") {
    const todos = message.input.todos;
    
    console.log("待办事项状态更新：");
    todos.forEach((todo, index) => {
      const status = todo.status === "completed" ? "✅" : 
                    todo.status === "in_progress" ? "🔧" : "❌";
      console.log(`${index + 1}. ${status} ${todo.content}`);
    });
  }
}
```

```python Python
from claude_agent_sdk import query

async for message in query(
    prompt="优化我的 React 应用性能并使用待办事项跟踪进度",
    options={"max_turns": 15}
):
    # 待办事项更新会反映在消息流中
    if message.get("type") == "tool_use" and message.get("name") == "TodoWrite":
        todos = message["input"]["todos"]
        
        print("待办事项状态更新：")
        for i, todo in enumerate(todos):
            status = "✅" if todo["status"] == "completed" else \
                    "🔧" if todo["status"] == "in_progress" else "❌"
            print(f"{i + 1}. {status} {todo['content']}")
```

</CodeGroup>

### 实时进度显示

<CodeGroup>

```typescript TypeScript
import { query } from "@anthropic-ai/claude-agent-sdk";

class TodoTracker {
  private todos: any[] = [];
  
  displayProgress() {
    if (this.todos.length === 0) return;
    
    const completed = this.todos.filter(t => t.status === "completed").length;
    const inProgress = this.todos.filter(t => t.status === "in_progress").length;
    const total = this.todos.length;
    
    console.log(`\n进度：${completed}/${total} 已完成`);
    console.log(`当前正在处理：${inProgress} 个任务\n`);
    
    this.todos.forEach((todo, index) => {
      const icon = todo.status === "completed" ? "✅" : 
                  todo.status === "in_progress" ? "🔧" : "❌";
      const text = todo.status === "in_progress" ? todo.activeForm : todo.content;
      console.log(`${index + 1}. ${icon} ${text}`);
    });
  }
  
  async trackQuery(prompt: string) {
    for await (const message of query({
      prompt,
      options: { maxTurns: 20 }
    })) {
      if (message.type === "tool_use" && message.name === "TodoWrite") {
        this.todos = message.input.todos;
        this.displayProgress();
      }
    }
  }
}

// 使用方法
const tracker = new TodoTracker();
await tracker.trackQuery("构建一个完整的身份验证系统并使用待办事项");
```

```python Python
from claude_agent_sdk import query
from typing import List, Dict

class TodoTracker:
    def __init__(self):
        self.todos: List[Dict] = []
    
    def display_progress(self):
        if not self.todos:
            return
        
        completed = len([t for t in self.todos if t["status"] == "completed"])
        in_progress = len([t for t in self.todos if t["status"] == "in_progress"])
        total = len(self.todos)
        
        print(f"\n进度：{completed}/{total} 已完成")
        print(f"当前正在处理：{in_progress} 个任务\n")
        
        for i, todo in enumerate(self.todos):
            icon = "✅" if todo["status"] == "completed" else \
                  "🔧" if todo["status"] == "in_progress" else "❌"
            text = todo["activeForm"] if todo["status"] == "in_progress" else todo["content"]
            print(f"{i + 1}. {icon} {text}")
    
    async def track_query(self, prompt: str):
        async for message in query(
            prompt=prompt,
            options={"max_turns": 20}
        ):
            if message.get("type") == "tool_use" and message.get("name") == "TodoWrite":
                self.todos = message["input"]["todos"]
                self.display_progress()

# 使用方法
tracker = TodoTracker()
await tracker.track_query("构建一个完整的身份验证系统并使用待办事项")
```

</CodeGroup>

## 相关文档

- [TypeScript SDK 参考](/docs/zh-CN/agent-sdk/typescript)
- [Python SDK 参考](/docs/zh-CN/agent-sdk/python) 
- [流式与单次模式](/docs/zh-CN/agent-sdk/streaming-vs-single-mode)
- [自定义工具](/docs/zh-CN/agent-sdk/custom-tools)