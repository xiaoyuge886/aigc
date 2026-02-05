// Agent 服务 - 适配后端流式接口
import { apiClient } from './api';
import { Message, Sender } from '../types';

// 流式响应的数据类型
export interface StreamMessage {
  type: 'data' | 'text_delta';
  data: StreamData;
}

export interface StreamData {
  type: string;
  subtype?: string;
  text?: string;
  thinking?: string | null;
  tool_name?: string | null;
  tool_input?: any;
  tool_use_id?: string | null;
  is_error?: boolean | null;
  data?: any;
  num_turns?: number;
  session_id?: string;
  content?: any[];
  model?: string;
  duration_ms?: number;
  duration_api_ms?: number;
  total_cost_usd?: number | null;
  usage?: Record<string, any> | null;
}

// ResultMessage 信息
export interface ResultInfo {
  subtype?: string;
  duration_ms?: number;
  duration_api_ms?: number;
  is_error?: boolean;
  num_turns?: number;
  session_id?: string;
  total_cost_usd?: number | null;
  usage?: Record<string, any> | null;
}

// 文件事件信息
export interface FileEvent {
  type: 'file_created' | 'file_uploaded';
  file_path?: string;
  file_url?: string;
  file_name?: string;
  file_size?: number;
  file_type?: string;
  conversation_turn_id?: string;
  doc_id?: string; // 添加 doc_id 字段
  file_content?: string; // 🔧 新增：文件内容字段（可选，用于直接从 event 获取文件内容）
}

// 流式响应的 chunk
export interface StreamChunk {
  text: string;
  isThinking?: boolean;
  isComplete?: boolean;
  error?: string;
  sessionId?: string; // 新增：用于返回 session_id
  toolCalls?: any[]; // 新增：工具调用信息
  toolStart?: any; // 新增：工具开始信息
  toolInputDelta?: { // 新增：工具输入增量更新
    tool_use_id: string;
    partial_json: string;
    timestamp?: string;
  };
  messageMetadata?: any; // 新增：消息元数据（token 使用）
  messageStop?: boolean; // 新增：消息结束标记
  resultInfo?: ResultInfo; // 新增：ResultMessage 信息
  fileEvent?: FileEvent; // 新增：文件事件
}

// 创建会话
export async function createSession(incrementalStream: boolean = true): Promise<{ session_id: string } | null> {
  const response = await apiClient.post<{ session_id: string }>('/api/v1/session', {
    incremental_stream: incrementalStream,
  });

  if (response.error) {
    console.error('创建会话失败:', response.error);
    return null;
  }

  return response.data || null;
}

// 删除会话
export async function deleteSession(sessionId: string): Promise<boolean> {
  const response = await apiClient.delete(`/api/v1/session/${sessionId}`);

  // 删除成功后，同时清除 localStorage 中的 session_id
  if (!response.error) {
    localStorage.removeItem('chat_session_id');
    console.log('%c🗑️ localStorage 中的 session_id 已清除', 'color: #FF9500; font-weight: bold');
  }

  return !response.error;
}

// 清除本地存储的 session_id（用于开始新会话）
export function clearLocalSessionId() {
  localStorage.removeItem('chat_session_id');
  console.log('%c🗑️ localStorage 中的 session_id 已手动清除', 'color: #FF9500; font-weight: bold');
}

// 获取本地存储的 session_id
export function getLocalSessionId(): string | null {
  return localStorage.getItem('chat_session_id');
}

// 流式查询 - 返回异步生成器
export interface FileAttachment {
  name: string;
  type: string;
  data: string; // Base64 encoded
}

export async function* streamAgentQuery(
  prompt: string,
  sessionId?: string | null,
  onThinking?: (text: string) => void,
  attachments?: FileAttachment[]
): AsyncGenerator<StreamChunk, void, unknown> {
  // 使用新的统一对话接口
  const endpoint = '/api/v1/session/query/stream';

  // 获取 API 基础 URL
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const token = localStorage.getItem('access_token');

  // 🔒 严格确保 prompt 是字符串，防止 [object Object]
  let safePrompt = '';
  if (typeof prompt === 'string') {
    safePrompt = prompt;
  } else if (prompt) {
    const converted = String(prompt);
    if (converted === '[object Object]') {
      console.error('❌ streamAgentQuery 收到对象类型的 prompt:', prompt);
      throw new Error('Invalid prompt: cannot convert object to string');
    }
    safePrompt = converted;
  }
  
  // 最终验证
  if (safePrompt === '[object Object]') {
    console.error('❌ streamAgentQuery: prompt 仍然是 [object Object]');
    throw new Error('Invalid prompt: [object Object]');
  }

  // 🔑 优先从 localStorage 获取 session_id（如果参数没传）
  const storedSessionId = localStorage.getItem('chat_session_id');
  const effectiveSessionId = sessionId || storedSessionId;

  // 构建 body：如果有 sessionId 就传，没有就传空字符串
  const requestBody: any = {
    prompt: safePrompt,
    incremental_stream: true,
  };

  // 只有当 sessionId 有效时才添加到请求中
  if (effectiveSessionId && effectiveSessionId.trim() !== '') {
    requestBody.session_id = effectiveSessionId;
  }

  // 添加文件附件（如果有）
  if (attachments && attachments.length > 0) {
    requestBody.attachments = attachments.map(att => ({
      name: att.name,
      type: att.type,
      data: att.data, // Base64 data (already encoded)
    }));
  }

  // 🔍 记录请求体（用于调试 session_id 流程）
  console.log('%c📤 发送请求体:', 'color: #FF9500; font-weight: bold');
  console.log('  Endpoint:', endpoint);
  console.log('  Request Body:', JSON.stringify(requestBody, null, 2));
  console.log('  传入的 session_id:', sessionId || '(未传入)');
  console.log('  localStorage 的 session_id:', storedSessionId || '(无)');
  console.log('  实际使用的 session_id:', effectiveSessionId || '(首次对话，不传 session_id)');

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('无法获取响应流');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let hasReceivedTextDelta = false; // 标记是否已收到 text_delta（流式模式下）

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        yield { text: '', isComplete: true };
        break;
      }

      // 解码数据
      buffer += decoder.decode(value, { stream: true });

      // 按行分割
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // 保留最后一个不完整的行

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) {
          continue;
        }

        try {
          const jsonStr = trimmed.slice(6); // 移除 "data: " 前缀
          const message: StreamMessage = JSON.parse(jsonStr);

          // 🔍 调试日志：打印所有收到的消息类型
          console.log('%c🔍 [agentService] 收到消息:', 'color: #007AFF; font-weight: bold', {
            message_type: message.type,
            message_data_type: message.data?.type,
            message_data_keys: message.data ? Object.keys(message.data) : [],
            message_data_tool_use_id: message.data?.tool_use_id,
            message_data_tool_name: message.data?.tool_name,
            full_message: message
          });

          if (message.type === 'text_delta') {
            // 增量文本片段（流式模式）
            hasReceivedTextDelta = true; // 标记已收到流式文本
            const text = message.data.text || '';
            if (text) {
              yield { text };
            }
          } else if (message.type === 'file_uploaded' || message.type === 'file_event' || message.type === 'file_created') {
            // 处理文件事件（file_created 或 file_uploaded）
            // 后端发送格式（StreamChunk）: { type: 'file_uploaded', data: { doc_id: ..., file_name: ..., ... } }
            // 从 message.data 中提取实际的事件数据
            const eventData: any = message.data || {};
            
            const fileEvent: FileEvent = {
              type: (eventData.type || message.type) as 'file_created' | 'file_uploaded',
              file_path: eventData.file_path,
              file_url: eventData.file_url,
              file_name: eventData.file_name,
              file_size: eventData.file_size,
              file_type: eventData.file_type,
              conversation_turn_id: eventData.conversation_turn_id,
              doc_id: eventData.doc_id, // 添加 doc_id 字段（后端直接提供）
              file_content: eventData.file_content, // 🔧 新增：如果 event 中包含文件内容，直接使用
            };
            console.log('%c📁 [agentService] 收到文件事件:', 'color: #5856D6; font-weight: bold', {
              message_type: message.type,
              fileEvent: fileEvent,
              raw_data: eventData,
              has_doc_id: !!eventData.doc_id,
              has_file_path: !!eventData.file_path,
              has_file_name: !!eventData.file_name
            });
            yield {
              text: '',
              fileEvent,
            };
          } else if (message.type === 'data') {
            // 🔧 修复：处理独立的 ContentBlock（如 tool_result, tool_input_delta, tool_start）
            // 后端可能直接发送 ContentBlock 作为 data，而不是包装在 UserMessage 中
            
            // 🔍 调试日志：打印 data 类型的消息详情
            console.log('%c🔍 [agentService] 处理 data 类型消息:', 'color: #5856D6; font-weight: bold', {
              message_type: message.type,
              data_type: message.data?.type,
              data_keys: message.data ? Object.keys(message.data) : [],
              data_tool_use_id: message.data?.tool_use_id,
              data_tool_name: message.data?.tool_name,
              data_text_length: message.data?.text?.length,
              full_data: message.data
            });
            
            if (message.data.type === 'tool_result') {
              // 独立的 tool_result ContentBlock
              const block = message.data;
              console.log('%c✅ 检测到独立的工具结果 (ContentBlock):', 'color: #00BC8C; font-weight: bold', block.tool_use_id);
              yield {
                text: '',
                toolCalls: [{
                  tool_use_id: block.tool_use_id,
                  tool_name: 'Unknown', // 需要和发起配对
                  output: block.text,
                  is_error: block.is_error,
                  timestamp: new Date().toLocaleTimeString('zh-CN')
                }]
              };
              continue;
            } else if (message.data.type === 'tool_start') {
              // 🔧 处理独立的 tool_start ContentBlock（工具调用开始事件）
              const block = message.data;
              console.log('%c🚀 检测到独立的工具开始事件 (ContentBlock):', 'color: #FF9500; font-weight: bold', block.tool_name, block.tool_use_id?.substring(0, 20));
              yield {
                text: '',
                toolStart: {
                  tool_use_id: block.tool_use_id,
                  tool_name: block.tool_name,
                  tool_input: block.tool_input || {},
                  timestamp: new Date().toLocaleTimeString('zh-CN')
                }
              };
              continue;
            } else if (message.data.type === 'tool_input_delta') {
              // 🔧 处理工具调用的流式输入更新（input_json_delta）
              const block = message.data;
              console.log('%c🔄 检测到工具输入增量更新:', 'color: #FF9500; font-weight: bold', block.tool_use_id);
              yield {
                text: '',
                toolInputDelta: {
                  tool_use_id: block.tool_use_id,
                  partial_json: block.text, // partial_json 存储在 text 字段中
                  timestamp: new Date().toLocaleTimeString('zh-CN')
                }
              };
              continue;
            }
            
            const msgType = message.data.type;

            if (msgType === 'system') {
              // 系统消息，提取 session_id（如果存在）
              if (message.data.data && message.data.data.session_id) {
                const newSessionId = message.data.data.session_id;

                // 🔍 记录收到的 session_id
                console.log('%c📥 收到 session_id (from system):', 'color: #FF9500; font-weight: bold', newSessionId);

                // 💾 保存到 localStorage（持久化存储）
                localStorage.setItem('chat_session_id', newSessionId);
                console.log('%c💾 session_id 已保存到 localStorage:', 'color: #FF9500; font-weight: bold', newSessionId);

                // 通过特殊字段返回 session_id
                yield {
                  text: '',
                  isComplete: false,
                  sessionId: newSessionId,
                };
              }
              continue;
            } else if (msgType === 'assistant') {
              // 处理助手消息（包括工具调用和新的事件类型）
              console.log('%c🔍 收到 assistant 消息:', 'color: #007AFF', message.data.content?.length || 0, '个 blocks');
              if (message.data.content) {
                const toolCalls: any[] = [];
                let text = '';

                for (const block of message.data.content) {
                  console.log('  Block type:', block.type);

                  // ⚠️ 重要：在流式模式下，如果已收到 text_delta，忽略 assistant 消息中的 text block
                  // 避免重复显示文本内容
                  if (block.type === 'text' && block.text) {
                    if (!hasReceivedTextDelta) {
                      // 非流式模式：使用完整的 text block
                      text += block.text;
                    } else {
                      // 流式模式：已通过 text_delta 接收，忽略此 text block
                      console.log('%c⚠️ 流式模式下忽略 assistant 消息中的 text block（已通过 text_delta 接收）', 'color: #FF9500');
                    }
                  } else if (block.type === 'tool_use') {
                    // 工具发起
                    // 🔧 关键修复：如果 tool_input.todos 是字符串（JSON字符串），需要解析为数组
                    let processedToolInput = { ...block.tool_input };
                    if (processedToolInput.todos && typeof processedToolInput.todos === 'string') {
                      try {
                        processedToolInput.todos = JSON.parse(processedToolInput.todos);
                        console.log('%c✅ [agentService] 成功解析 tool_use 中的 todos JSON字符串', 'color: #34C759; font-weight: bold', {
                          tool_name: block.tool_name,
                          tool_use_id: block.tool_use_id?.substring(0, 20),
                          todos_count: Array.isArray(processedToolInput.todos) ? processedToolInput.todos.length : 0
                        });
                      } catch (e) {
                        console.warn('%c⚠️ [agentService] 解析 tool_use 中的 todos JSON字符串失败:', 'color: #FF9500; font-weight: bold', e, {
                          todos_string: processedToolInput.todos.substring(0, 100)
                        });
                      }
                    }
                    
                    toolCalls.push({
                      tool_use_id: block.tool_use_id,
                      tool_name: block.tool_name,
                      input: processedToolInput,
                      status: 'running',
                      timestamp: new Date().toLocaleTimeString('zh-CN')
                    });
                    console.log('%c🔧 检测到工具发起:', 'color: #FF9500; font-weight: bold', block.tool_name);
                  } else if (block.type === 'tool_result') {
                    // 工具结果
                    toolCalls.push({
                      tool_use_id: block.tool_use_id,
                      tool_name: 'Unknown', // 需要和发起配对
                      output: block.text,
                      is_error: block.is_error,
                      timestamp: new Date().toLocaleTimeString('zh-CN')
                    });
                    console.log('%c✅ 检测到工具结果:', 'color: #00BC8C; font-weight: bold', block.tool_use_id);
                  } else if (block.type === 'tool_start') {
                    // 工具开始事件（StreamEvent）
                    console.log('%c🚀 检测到工具开始事件:', 'color: #FF9500; font-weight: bold', block.tool_name);
                    yield {
                      text: '',
                      toolStart: {
                        tool_use_id: block.tool_use_id,
                        tool_name: block.tool_name,
                        tool_input: block.tool_input,
                        timestamp: new Date().toLocaleTimeString('zh-CN')
                      }
                    };
                  } else if (block.type === 'message_metadata') {
                    // 消息元数据（token 使用）- 不显示给用户，仅用于内部处理
                    console.log('%c📊 检测到消息元数据（不显示）:', 'color: #007AFF; font-weight: bold', block.text);
                    // 不 yield，避免前端显示
                    continue;
                  } else if (block.type === 'message_stop') {
                    // 消息结束
                    console.log('%c🏁 检测到消息结束事件', 'color: #007AFF; font-weight: bold');
                    yield {
                      text: '',
                      messageStop: true
                    };
                  } else if (block.type === 'file_created' || block.type === 'file_uploaded') {
                    // 文件事件（file_created 或 file_uploaded）
                    const fileEvent: FileEvent = {
                      type: block.type,
                      file_path: block.file_path,
                      file_url: block.file_url,
                      file_name: block.file_name,
                      file_size: block.file_size,
                      file_type: block.file_type,
                      conversation_turn_id: block.conversation_turn_id,
                      doc_id: block.doc_id, // 🔧 新增：添加 doc_id 字段
                      file_content: block.file_content, // 🔧 新增：如果 event 中包含文件内容，直接使用
                    };
                    console.log('%c📁 检测到文件事件 (from assistant):', 'color: #5856D6; font-weight: bold', fileEvent);
                    yield {
                      text: '',
                      fileEvent,
                    };
                  }
                }

                // 只在非流式模式或没有收到 text_delta 时返回文本
                // 流式模式下，文本已通过 text_delta 接收，这里只返回工具调用信息
                if (!hasReceivedTextDelta && text) {
                  yield {
                    text,
                    ...(toolCalls.length > 0 ? { toolCalls } : {})
                  };
                } else if (toolCalls.length > 0) {
                  // 流式模式：只返回工具调用，不返回文本
                  yield {
                    text: '',
                    toolCalls
                  };
                }
              }
            } else if (msgType === 'user') {
              // 处理用户消息（包含工具结果）
              console.log('%c🔍 收到 user 消息, content 长度:', 'color: #007AFF', message.data.content?.length || 0);
              if (message.data.content) {
                const toolCalls: any[] = [];

                for (const block of message.data.content) {
                  console.log('  User block type:', block.type);
                  if (block.type === 'tool_result') {
                    toolCalls.push({
                      tool_use_id: block.tool_use_id,
                      tool_name: 'Unknown',
                      output: block.text,
                      is_error: block.is_error,
                      timestamp: new Date().toLocaleTimeString('zh-CN')
                    });
                    console.log('%c✅ 检测到工具结果 (user):', 'color: #00BC8C; font-weight: bold', block.tool_use_id);
                  }
                }

                if (toolCalls.length > 0) {
                  yield { text: '', toolCalls };
                }
              }
            } else if (msgType === 'result') {
              // 最终结果，提取所有字段信息
              const resultInfo: ResultInfo = {
                subtype: message.data.subtype,
                duration_ms: message.data.duration_ms,
                duration_api_ms: message.data.duration_api_ms,
                is_error: message.data.is_error,
                num_turns: message.data.num_turns,
                session_id: message.data.session_id,
                total_cost_usd: message.data.total_cost_usd,
                usage: message.data.usage,
              };

              if (message.data.session_id) {
                const newSessionId = message.data.session_id;

                // 🔍 记录收到的 session_id
                console.log('%c📥 收到 session_id (from result):', 'color: #FF9500; font-weight: bold', newSessionId);
                console.log('%c📊 Result 信息:', 'color: #007AFF; font-weight: bold', resultInfo);

                // 💾 保存到 localStorage（持久化存储）
                localStorage.setItem('chat_session_id', newSessionId);
                console.log('%c💾 session_id 已保存到 localStorage:', 'color: #FF9500; font-weight: bold', newSessionId);

                // 返回 session_id 和完整的 result 信息
                yield {
                  text: '',
                  isComplete: true,
                  sessionId: newSessionId,
                  resultInfo,
                };
              } else {
                yield {
                  text: '',
                  isComplete: true,
                  resultInfo,
                };
              }
              break;
            }
          }
        } catch (e) {
          console.warn('解析 SSE 数据失败:', e, trimmed);
        }
      }
    }
  } catch (error) {
    console.error('流式请求异常:', error);
    yield {
      text: '',
      error: error instanceof Error ? error.message : '请求失败',
    };
  }
}

// 流式调试技能 - 复用 streamAgentQuery 的逻辑，但调用调试端点
export async function* streamDebugSkill(
  skillName: string,
  skillContent: string,
  testQuery: string,
  skills?: string[],  // 新增：要加载的技能列表，如 ['skill-creator']
  sessionId?: string,  // 新增：会话ID，用于多轮对话
): AsyncGenerator<StreamChunk, void, unknown> {
  const endpoint = '/api/v1/debug/skill/stream';
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  console.log('%c📤 发送调试请求:', 'color: #FF9500; font-weight: bold');
  console.log('  Endpoint:', endpoint);
  console.log('  Skill:', skillName);
  console.log('  Skills to load:', skills || 'none');
  console.log('  Session ID:', sessionId || '(new session)');

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        skill_name: skillName,
        skill_content: skillContent,
        test_query: testQuery,
        skills: skills,  // 传递 skills 参数
        session_id: sessionId,  // 传递 session_id（多轮对话）
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('无法获取响应流');
    }

    const decoder = new TextDecoder();
    let buffer = '';
    let hasReceivedTextDelta = false;

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        yield { text: '', isComplete: true };
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) {
          continue;
        }

        try {
          const jsonStr = trimmed.slice(6);
          const message: StreamMessage = JSON.parse(jsonStr);

          if (message.type === 'text_delta') {
            hasReceivedTextDelta = true;
            const text = message.data.text || '';
            if (text) {
              yield { text };
            }
          } else if (message.type === 'data') {
            const msgType = message.data?.type;

            if (msgType === 'system') {
              if (message.data.data?.session_id) {
                yield {
                  text: '',
                  isComplete: false,
                  sessionId: message.data.data.session_id,
                };
              }
            } else if (msgType === 'assistant') {
              if (message.data.content) {
                const toolCalls: any[] = [];
                let text = '';

                for (const block of message.data.content) {
                  if (block.type === 'text' && block.text && !hasReceivedTextDelta) {
                    text += block.text;
                  } else if (block.type === 'tool_use') {
                    toolCalls.push({
                      tool_use_id: block.tool_use_id,
                      tool_name: block.tool_name,
                      input: block.tool_input,
                      status: 'running',
                      timestamp: new Date().toLocaleTimeString('zh-CN')
                    });
                  }
                }

                if (!hasReceivedTextDelta && text) {
                  yield { text, ...(toolCalls.length > 0 ? { toolCalls } : {}) };
                } else if (toolCalls.length > 0) {
                  yield { text: '', toolCalls };
                }
              }
            } else if (msgType === 'result') {
              const resultInfo: ResultInfo = {
                subtype: message.data.subtype,
                duration_ms: message.data.duration_ms,
                duration_api_ms: message.data.duration_api_ms,
                is_error: message.data.is_error,
                num_turns: message.data.num_turns,
                session_id: message.data.session_id,
                total_cost_usd: message.data.total_cost_usd,
                usage: message.data.usage,
              };

              yield {
                text: '',
                isComplete: true,
                resultInfo,
              };
              break;
            } else if (msgType === 'tool_start') {
              yield {
                text: '',
                toolStart: {
                  tool_use_id: message.data.tool_use_id,
                  tool_name: message.data.tool_name,
                  tool_input: message.data.tool_input,
                  timestamp: new Date().toLocaleTimeString('zh-CN')
                }
              };
            } else if (msgType === 'tool_result') {
              yield {
                text: '',
                toolCalls: [{
                  tool_use_id: message.data.tool_use_id,
                  tool_name: 'Unknown',
                  output: message.data.text,
                  is_error: message.data.is_error,
                  timestamp: new Date().toLocaleTimeString('zh-CN')
                }]
              };
            }
          }
        } catch (e) {
          console.warn('解析 SSE 数据失败:', e, trimmed);
        }
      }
    }
  } catch (error) {
    console.error('流式调试异常:', error);
    yield {
      text: '',
      error: error instanceof Error ? error.message : '请求失败',
    };
  }
}

// 获取会话历史（旧格式）
export async function getSessionHistory(sessionId: string, limit?: number) {
  const response = await apiClient.get(`/api/v1/session/${sessionId}/history${limit ? `?limit=${limit}` : ''}`);
  return response.data;
}

// 获取会话消息（分页）
export async function getSessionMessages(sessionId: string, limit?: number, offset?: number) {
  const params = new URLSearchParams();
  if (limit) params.append('limit', limit.toString());
  if (offset) params.append('offset', offset.toString());

  const response = await apiClient.get(`/api/v1/session/${sessionId}/messages?${params.toString()}`);
  return response.data;
}

// 读取文件内容
export async function getConversationDataFlow(conversationTurnId: string): Promise<any | null> {
  try {
    const response = await apiClient.get(`/api/v1/conversation/${conversationTurnId}/dataflow`);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching conversation dataflow:', error);
    return null;
  }
}

// 获取会话文件列表（用于 @ 提及功能）
export interface SessionFile {
  doc_id: string;
  file_name: string;
  file_type: string;
  file_size: number | null;
  uploaded_at: string | null;
}

export async function getSessionFiles(sessionId: string): Promise<SessionFile[]> {
  try {
    const response = await apiClient.get<{ files: SessionFile[] }>(`/api/v1/files/session/${sessionId}`);
    if (response.error) {
      console.error('获取文件列表失败:', response.error);
      return [];
    }
    return response.data?.files || [];
  } catch (error) {
    console.error('获取文件列表异常:', error);
    return [];
  }
}

export async function getFileContent(filePath: string): Promise<{ file_path: string; content: string; size: number }> {
  try {
    const response = await apiClient.get(`/api/v1/file/content?file_path=${encodeURIComponent(filePath)}`);
    return response.data;
  } catch (error: any) {
    console.error('[getFileContent] 读取文件失败:', error);
    throw error;
  }
}

// 对话历史响应类型
export interface ConversationHistoryResponse {
  session_id: string;
  messages: any[];
  file_events?: any[];
  total?: number | null;
  limit?: number | null;
  offset: number;
  has_more: boolean;
}

// 获取对话历史（前端格式，支持分页）
export async function getConversationHistory(
  sessionId: string, 
  limit?: number, 
  offset: number = 0
): Promise<ConversationHistoryResponse | null> {
  try {
    console.log(`[getConversationHistory] Fetching history for session: ${sessionId}, limit=${limit}, offset=${offset}`);
    
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset > 0) params.append('offset', offset.toString());
    
    const url = `/api/v1/session/${sessionId}/conversation${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await apiClient.get<ConversationHistoryResponse>(url);
    
    console.log(`[getConversationHistory] API response:`, response);
    
    if (response.error) {
      console.error('[getConversationHistory] 获取对话历史失败:', response.error);
      return null;
    }

    if (!response.data) {
      console.warn('[getConversationHistory] No data in response');
      return null;
    }
    
    console.log(`[getConversationHistory] Response data:`, {
      session_id: response.data.session_id,
      message_count: response.data.messages?.length || 0,
      file_events_count: response.data.file_events?.length || 0,
      total: response.data.total,
      limit: response.data.limit,
      offset: response.data.offset,
      has_more: response.data.has_more,
      messages: response.data.messages
    });

    // 转换后端格式到前端格式
    const messages: Message[] = response.data.messages.map((msg, index) => {
      const message: Message = {
        id: msg.id,
        text: msg.text,
        sender: msg.sender === 'user' ? Sender.User : Sender.AI,
        timestamp: new Date(msg.timestamp),
        resultInfo: msg.resultInfo ? {
          subtype: msg.resultInfo.subtype,
          duration_ms: msg.resultInfo.duration_ms,
          duration_api_ms: msg.resultInfo.duration_api_ms,
          is_error: msg.resultInfo.is_error,
          num_turns: msg.resultInfo.num_turns,
          session_id: msg.resultInfo.session_id,
          total_cost_usd: msg.resultInfo.total_cost_usd,
          usage: msg.resultInfo.usage,
        } : undefined,
        conversation_turn_id: msg.conversation_turn_id || undefined,
        parent_message_id: msg.parent_message_id || undefined,
        tool_calls: msg.tool_calls || [],
      };
      
      // 调试：检查每条消息的 conversation_turn_id 和 tool_calls
      if (index < 3 || msg.conversation_turn_id || (msg.tool_calls && msg.tool_calls.length > 0)) {
        console.log(`[getConversationHistory] 消息 #${index}:`, {
          id: msg.id,
          sender: msg.sender,
          conversation_turn_id: msg.conversation_turn_id,
          conversation_turn_id_type: typeof msg.conversation_turn_id,
          has_tool_calls: !!(msg.tool_calls && msg.tool_calls.length > 0),
          tool_calls_count: msg.tool_calls?.length || 0,
          tool_calls_detail: msg.tool_calls?.map((tc: any) => ({
            tool_name: tc.tool_name,
            tool_use_id: tc.tool_use_id?.substring(0, 20),
            has_tool_input: !!tc.tool_input,
            has_todos: !!(tc.tool_input && tc.tool_input.todos),
            todos_count: tc.tool_input?.todos?.length || 0,
            tool_input_keys: tc.tool_input ? Object.keys(tc.tool_input) : []
          })) || []
        });
      }
      
      return message;
    });

    return {
      session_id: response.data.session_id,
      messages,
      file_events: response.data.file_events || [],
    };
  } catch (error) {
    console.error('获取对话历史异常:', error);
    return null;
  }
}

// 会话信息类型
export interface SessionInfo {
  session_id: string;
  created_at: string;
  last_activity: string;
  is_connected: boolean;
  model?: string;
}

// 会话列表响应类型
export interface SessionsListResponse {
  total: number;
  limit?: number | null;
  offset: number;
  has_more: boolean;
  sessions: SessionInfo[];
  stats?: {
    total_sessions: number;
    total_messages: number;
    total_cost_usd: number;
  };
}

// 获取会话列表（支持分页）
export async function getSessionsList(limit?: number, offset: number = 0): Promise<SessionsListResponse> {
  try {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset > 0) params.append('offset', offset.toString());
    
    const url = `/api/v1/sessions${params.toString() ? `?${params.toString()}` : ''}`;
    const response = await apiClient.get<SessionsListResponse>(url);
    
    if (response.error) {
      console.error('获取会话列表失败:', response.error);
      return {
        total: 0,
        limit: limit || null,
        offset: offset,
        has_more: false,
        sessions: []
      };
    }

    return response.data || {
      total: 0,
      limit: limit || null,
      offset: offset,
      has_more: false,
      sessions: []
    };
  } catch (error) {
    console.error('获取会话列表异常:', error);
    return {
      total: 0,
      limit: limit || null,
      offset: offset,
      has_more: false,
      sessions: []
    };
  }
}

// 获取会话统计信息
export async function getSessionsStats(): Promise<{ total_sessions: number; total_messages: number; total_cost_usd: number } | null> {
  try {
    const response = await apiClient.get<SessionsListResponse>('/api/v1/sessions?limit=1&offset=0');
    
    if (response.error || !response.data) {
      return null;
    }

    // 从后端返回的 stats 字段获取统计信息
    if (response.data.stats) {
      return {
        total_sessions: response.data.stats.total_sessions || response.data.total || 0,
        total_messages: response.data.stats.total_messages || 0,
        total_cost_usd: response.data.stats.total_cost_usd || 0
      };
    }

    // 如果没有 stats 字段，使用默认值
    return {
      total_sessions: response.data.total || 0,
      total_messages: 0,
      total_cost_usd: 0
    };
  } catch (error) {
    console.error('获取会话统计异常:', error);
    return null;
  }
}
