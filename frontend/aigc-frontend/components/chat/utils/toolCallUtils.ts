// 工具调用数据类型
export interface ToolCall {
  tool_use_id: string;
  tool_name: string;
  input: any;
  output: any;
  timestamp: string;
  duration?: number;
  status: 'success' | 'error' | 'running';
  conversation_turn_id?: string | null; // 对话轮次ID
  message_id?: string; // 所属消息ID
}

/**
 * 完整的工具调用解析（配对追踪）
 * 从文本中解析 ToolUseBlock 和 ToolResultBlock，并配对
 * 
 * @param text - 包含工具调用信息的文本
 * @returns ToolCall[] - 解析后的工具调用列表
 */
export const parseToolCalls = (text: string): ToolCall[] => {
  const calls: ToolCall[] = [];

  console.log('%c🔍 开始解析工具调用，文本长度:', 'color: #FF9500; font-weight: bold', text.length);

  // 步骤 1: 解析 ToolUseBlock（工具发起）
  interface ToolUse {
    id: string;
    name: string;
    input: any;
    timestamp: string;
  }

  const toolUses: ToolUse[] = [];

  // 改进的正则：匹配到 input= 后面任意字符直到括号结束
  // 格式: ToolUseBlock(id='...', name='...', input={...})
  const toolUseRegex = /ToolUseBlock\(\s*id='([^']+)'\s*,\s*name='([^']+)'\s*,\s*input=(.+?)\s*\)/gs;

  let match;
  while ((match = toolUseRegex.exec(text)) !== null) {
    const toolUse: ToolUse = {
      id: match[1],
      name: match[2],
      input: {},
      timestamp: new Date().toLocaleTimeString('zh-CN')
    };

    // 解析 input - 可能是 {'key': 'value'} 或 {'key': "value"}
    try {
      let inputStr = match[3].trim();

      // 查找最外层的配对大括号
      if (inputStr.startsWith('{')) {
        let depth = 0;
        let endPos = 0;
        for (let i = 0; i < inputStr.length; i++) {
          if (inputStr[i] === '{') depth++;
          if (inputStr[i] === '}') depth--;
          if (depth === 0) {
            endPos = i + 1;
            break;
          }
        }
        inputStr = inputStr.substring(0, endPos);

        // 替换单引号为双引号以便 JSON.parse
        const normalized = inputStr.replace(/'/g, '"');
        toolUse.input = JSON.parse(normalized);
      } else {
        toolUse.input = { raw: inputStr };
      }
    } catch (e) {
      console.warn('input 解析失败:', e, '原始值:', match[3]);
      toolUse.input = { raw: match[3] };
    }

    toolUses.push(toolUse);

    console.log(`%c🔧 工具发起 #${toolUses.length}`, 'color: #FF9500; font-weight: bold', {
      id: toolUse.id.substring(0, 20) + '...',
      name: toolUse.name,
      input: toolUse.input,
      timestamp: toolUse.timestamp
    });
  }

  // 步骤 2: 解析 ToolResultBlock（工具结果）
  // 改进的正则：匹配到 is_error=None 或 is_error=True/False
  // 格式: ToolResultBlock(tool_use_id='...', content='...', is_error=None)
  const toolResultRegex = /ToolResultBlock\(\s*tool_use_id='([^']+)'\s*,\s*content='([\s\S]*?)'\s*,\s*is_error=(?:None|True|False)\s*\)/g;

  // 重置正则表达式的 lastIndex
  toolResultRegex.lastIndex = 0;

  while ((match = toolResultRegex.exec(text)) !== null) {
    const tool_use_id = match[1];
    const content = match[2].replace(/\\'/g, "'").replace(/\\n/g, '\n');

    // 查找对应的 ToolUseBlock
    const toolUse = toolUses.find(t => t.id === tool_use_id);

    // 解析输出
    let output: any = content;
    try {
      // 尝试解析 JSON（查找 Links 数组）
      const linksMatch = content.match(/Links: (\[[\s\S]*?\])/);
      if (linksMatch) {
        try {
          const links = JSON.parse(linksMatch[1]);
          output = { links, full_content: content };
        } catch (e) {
          output = content;
        }
      }
    } catch (e) {
      // 保持原始字符串
    }

    const toolCall: ToolCall = {
      tool_use_id,
      tool_name: toolUse?.name || 'Unknown',
      input: toolUse?.input || {},
      output,
      timestamp: toolUse?.timestamp || new Date().toLocaleTimeString('zh-CN'),
      status: 'success'
    };

    calls.push(toolCall);

    console.log(`%c✅ 工具结果 #${calls.length}`, 'color: #00BC8C; font-weight: bold', {
      id: tool_use_id.substring(0, 20) + '...',
      name: toolCall.tool_name,
      output_length: typeof output === 'string' ? output.length : 'object',
      matched: !!toolUse
    });
  }

  if (toolUses.length > 0 || calls.length > 0) {
    console.log(`%c📊 工具调用统计`, 'color: #007AFF; font-weight: bold', {
      发起: toolUses.length,
      完成: calls.length,
      配对成功: calls.filter(c => toolUses.find(t => t.id === c.tool_use_id)).length
    });
  } else {
    console.log('%c⚠️ 未检测到工具调用', 'color: #FF9500');
  }

  return calls;
};
