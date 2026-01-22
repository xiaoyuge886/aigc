import { Message, Sender } from '../../../types';
import { TodoItem } from '../../TodoList';

/**
 * 检查工具调用是否是 TodoWrite 或 enhanced_todo_write
 */
const isTodoTool = (toolName: string): boolean => {
  return toolName === 'TodoWrite' || toolName === 'enhanced_todo_write' || toolName === 'mcp__custom_tools__enhanced_todo_write';
};

/**
 * 解析任务层级（从 content 中提取）
 * 返回 { level: string | null, parentLevel: string | null }
 */
const parseTaskLevel = (content: string): { level: string | null; parentLevel: string | null } => {
  if (!content) return { level: null, parentLevel: null };

  const trimmed = content.trim();
  // 匹配 "1", "1.1", "1.2.3" 这样的层级编号
  const match = trimmed.match(/^(\d+(?:\.\d+)*)(?:\.\s|\s)/);

  if (match) {
    const level = match[1];
    const parts = level.split('.');
    const parentLevel = parts.length > 1 ? parts.slice(0, -1).join('.') : null;
    return { level, parentLevel };
  }

  return { level: null, parentLevel: null };
};

/**
 * 解析 todos 数据（可能是数组或 JSON 字符串）
 * 同时为每个 todo 添加 level 和 parentLevel 字段
 */
const parseTodosData = (todos: any): any[] => {
  if (!todos) return [];
  if (Array.isArray(todos)) {
    // 为每个 todo 解析 level
    return todos.map((todo: any) => {
      const content = todo.content || '';
      const level = parseTaskLevel(content);
      return {
        ...todo,
        level: level.level,
        parentLevel: level.parentLevel
      };
    });
  }
  if (typeof todos === 'string') {
    try {
      const parsed = JSON.parse(todos);
      if (Array.isArray(parsed)) {
        return parsed.map((todo: any) => {
          const content = todo.content || '';
          const level = parseTaskLevel(content);
          return {
            ...todo,
            level: level.level,
            parentLevel: level.parentLevel
          };
        });
      }
      return parsed;
    } catch (e) {
      console.warn('Failed to parse todos JSON string:', e);
      return [];
    }
  }
  return [];
};

/**
 * 消息显示逻辑
 * 根据消息长度决定在对话框和工作区的显示方式
 */
export const getMessageDisplay = (text: string) => {
  const cleanText = typeof text === 'string' ? text : String(text);
  const textLength = cleanText.length;

  // 短消息（≤100字符）：对话框和工作区都显示完整内容
  if (textLength <= 100) {
    return {
      isLong: false,
      chatContent: cleanText,
      fullContent: cleanText
    };
  }

  // 长消息（>100字符）：对话框只显示提示，工作区显示完整内容
  return {
    isLong: true,
    chatContent: '', // 对话框不显示内容
    fullContent: cleanText // 工作区显示完整内容
  };
};

/**
 * 从消息中提取 TodoWrite 的待办事项列表
 * 返回最新的待办事项列表（如果有多个 TodoWrite 调用，使用最新的）
 * 
 * @param messages - 消息数组
 * @returns TodoItem[] - 待办事项列表
 */
export const extractTodosFromToolCalls = (messages: Message[]): TodoItem[] => {
  if (!messages || messages.length === 0) {
    console.log('%c📋 [extractTodosFromToolCalls] 没有消息', 'color: #FF9500');
    return [];
  }

  // 🔍 调试：检查所有消息的 tool_calls
  console.log('%c🔍 [extractTodosFromToolCalls] 检查所有消息:', 'color: #007AFF; font-weight: bold', {
    total_messages: messages.length,
    messages_with_tool_calls: messages.filter(m => m.tool_calls && m.tool_calls.length > 0).length,
    messages_detail: messages.map((m, idx) => ({
      index: idx,
      id: m.id,
      sender: m.sender,
      has_tool_calls: !!(m.tool_calls && m.tool_calls.length > 0),
      tool_calls_count: m.tool_calls?.length || 0,
      tool_calls_detail: m.tool_calls?.map((tc: any) => ({
        tool_name: tc.tool_name,
        tool_use_id: tc.tool_use_id?.substring(0, 20),
        has_tool_input: !!tc.tool_input,
        has_todos: !!(tc.tool_input && tc.tool_input.todos),
        todos_count: tc.tool_input?.todos?.length || 0
      })) || []
    }))
  });

  // 从所有消息中查找 TodoWrite 工具调用
  // 注意：需要记录消息索引和工具调用在数组中的索引，以便正确排序
  const allTodoWriteCalls: Array<{ 
    input: any; 
    timestamp: Date | string;
    messageIndex: number;
    toolCallIndex: number;
    tool_use_id?: string;
  }> = [];
  
  messages.forEach((msg, msgIndex) => {
    if (msg.tool_calls && msg.tool_calls.length > 0) {
      // 🔧 在同一个消息中，如果有多个 TodoWrite 调用，只保留最后一个（最新的）
      const todoWriteCallsInMessage = msg.tool_calls
        .map((toolCall, toolCallIndex) => ({ toolCall, toolCallIndex }))
        .filter(({ toolCall }) => isTodoTool(toolCall.tool_name));
      
      if (todoWriteCallsInMessage.length > 0) {
        // 🔧 关键修复：前端通过 toolInputDelta 更新时，新的调用会被 push 到数组末尾
        // 所以 toolCallIndex 最大的（数组中的最后一个）是最新的调用
        // 但是，为了确保选择的是真正最新的，我们需要检查 todos 的完成状态和更新时间
        // 优先选择所有任务都完成的 TodoWrite，如果没有，再选择 toolCallIndex 最大的（最新的）
        
        // 🔧 额外检查：如果有多个 TodoWrite，优先选择所有任务都完成的
        const completedTodos = todoWriteCallsInMessage.filter(({ toolCall }) => {
          const todos = parseTodosData(toolCall.tool_input?.todos);
          return todos.length > 0 && todos.every((todo: any) => todo.status === 'completed');
        });
        
        let latestInMessage: { toolCall: any; toolCallIndex: number };
        
        if (completedTodos.length > 0) {
          // 如果有完成的 TodoWrite，选择其中 toolCallIndex 最大的（最新的）
          latestInMessage = completedTodos.reduce((latest, current) => 
            current.toolCallIndex > latest.toolCallIndex ? current : latest
          );
          console.log('%c🎯 [extractTodosFromToolCalls] 找到所有任务都完成的 TodoWrite，优先选择', 'color: #34C759; font-weight: bold', {
            message_id: msg.id,
            selected_tool_call_index: latestInMessage.toolCallIndex,
            completed_count: completedTodos.length,
            total_todoWrite_count: todoWriteCallsInMessage.length
          });
        } else {
          // 如果没有完成的，选择 toolCallIndex 最大的（数组中的最后一个，最新的）
          latestInMessage = todoWriteCallsInMessage.reduce((latest, current) => 
            current.toolCallIndex > latest.toolCallIndex ? current : latest
          );
        }
        
        console.log('%c✅ [extractTodosFromToolCalls] 找到 TodoWrite 工具调用', 'color: #34C759; font-weight: bold', {
          message_id: msg.id,
          message_index: msgIndex,
          tool_call_index: latestInMessage.toolCallIndex,
          tool_use_id: latestInMessage.toolCall.tool_use_id,
          tool_input: latestInMessage.toolCall.tool_input,
          has_todos: !!(latestInMessage.toolCall.tool_input && latestInMessage.toolCall.tool_input.todos),
          todos_status: parseTodosData(latestInMessage.toolCall.tool_input?.todos).map((t: any) => t.status) || [],
          total_todoWrite_in_message: todoWriteCallsInMessage.length,
          note: todoWriteCallsInMessage.length > 1 ? '同一消息中有多个 TodoWrite，只保留最新的' : '只有一个 TodoWrite'
        });
        
        allTodoWriteCalls.push({
          input: latestInMessage.toolCall.tool_input || {},
          timestamp: msg.timestamp,
          messageIndex: msgIndex,
          toolCallIndex: latestInMessage.toolCallIndex,
          tool_use_id: latestInMessage.toolCall.tool_use_id
        });
      }
    }
  });

  if (allTodoWriteCalls.length === 0) {
    console.log('%c⚠️ [extractTodosFromToolCalls] 没有找到 TodoWrite 工具调用', 'color: #FF9500', {
      messages_count: messages.length,
      messages_with_tool_calls: messages.filter(m => m.tool_calls && m.tool_calls.length > 0).length
    });
    return [];
  }

  // 使用最新的 TodoWrite 调用
  // 🔧 关键修复：前端通过 toolInputDelta 更新时，新的调用会被 push 到数组末尾
  // 排序规则：
  // 1. 优先选择所有任务都完成的 TodoWrite（如果有的话）
  // 2. 然后按消息索引（越新越大）
  // 3. 再按工具调用在数组中的索引（越大越新，因为新调用被 push 到末尾）
  // 4. 最后按时间戳（越新越大）
  const sortedCalls = allTodoWriteCalls.sort((a, b) => {
    // 🔧 优先选择所有任务都完成的 TodoWrite
    const aTodos = parseTodosData(a.input?.todos);
    const bTodos = parseTodosData(b.input?.todos);
    const aAllCompleted = aTodos.length > 0 && aTodos.every((todo: any) => todo.status === 'completed');
    const bAllCompleted = bTodos.length > 0 && bTodos.every((todo: any) => todo.status === 'completed');
    
    if (aAllCompleted && !bAllCompleted) {
      return -1; // a 优先
    }
    if (!aAllCompleted && bAllCompleted) {
      return 1; // b 优先
    }
    
    // 如果完成状态相同，按消息索引排序（消息索引越大，说明越新）
    if (a.messageIndex !== b.messageIndex) {
      return b.messageIndex - a.messageIndex;
    }
    // 如果消息索引相同，按工具调用索引排序（索引越大，说明越新，因为新调用被 push 到数组末尾）
    if (a.toolCallIndex !== b.toolCallIndex) {
      return b.toolCallIndex - a.toolCallIndex; // 降序：大的在前（最新的）
    }
    // 如果消息索引和工具调用索引都相同，按时间戳排序（越新越大）
    const timeA = a.timestamp instanceof Date ? a.timestamp.getTime() : new Date(a.timestamp).getTime();
    const timeB = b.timestamp instanceof Date ? b.timestamp.getTime() : new Date(b.timestamp).getTime();
    return timeB - timeA;
  });
  
  const latestCall = sortedCalls[0];
  
  console.log('%c📋 [extractTodosFromToolCalls] 使用最新的 TodoWrite 调用', 'color: #007AFF; font-weight: bold', {
    total_calls: allTodoWriteCalls.length,
    latest_call_message_index: latestCall.messageIndex,
    latest_call_tool_index: latestCall.toolCallIndex,
    latest_call_tool_use_id: latestCall.tool_use_id,
    latest_call_input: latestCall.input,
    has_todos: !!(latestCall.input && latestCall.input.todos),
    all_calls_summary: allTodoWriteCalls.map(c => ({
      message_index: c.messageIndex,
      tool_index: c.toolCallIndex,
      tool_use_id: c.tool_use_id?.substring(0, 20)
    }))
  });
  
  // 从 tool_input 中提取 todos
  const parsedTodos = parseTodosData(latestCall.input?.todos);

  if (parsedTodos && parsedTodos.length > 0) {
    const todos = parsedTodos.map((todo: any, index: number) => {
      const status = todo.status || 'pending';
      // 🔧 修复：如果任务状态是 completed，清除 activeForm 字段
      // 因为 activeForm 只在 in_progress 状态时才有意义
      const activeForm = status === 'completed' ? undefined : todo.activeForm;
      return {
        id: todo.id || `todo-${index}-${Math.random().toString(36).substr(2, 9)}`,
        content: todo.content || '',
        status: status,
        activeForm: activeForm,
        level: todo.level,
        parentLevel: todo.parentLevel,
      };
    });
    
    console.log('%c✅ [extractTodosFromToolCalls] 成功提取 todos', 'color: #34C759; font-weight: bold', {
      todos_count: todos.length,
      todos: todos
    });
    
    return todos;
  }

  console.warn('%c⚠️ [extractTodosFromToolCalls] latestCall.input 中没有 todos 数组', 'color: #FF9500', {
    latest_call_input: latestCall.input,
    input_type: typeof latestCall.input
  });

  return [];
};
