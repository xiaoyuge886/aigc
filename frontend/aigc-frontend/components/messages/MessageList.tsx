import React, { useState, useRef } from 'react';
import { Loader2, RefreshCw, Copy, Check, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp } from 'lucide-react';
import { Message, Sender } from '../../types';
import { TodoList, TodoItem } from '../TodoList';
import { MarkdownRendererWithCharts } from '../markdown/MarkdownComponents';

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

export interface MessageListProps {
  messages: Message[];
  historyTotal: number | null;
  historyHasMore: boolean;
  loadingMoreHistory: boolean;
  loadMoreHistory: () => void;
  getMessageDisplay: (text: string | undefined) => { fullContent: string; isLong: boolean; chatContent: string };
  setSelectedTurnId: (turnId: string) => void;
  setWorkspaceMessageId: (id: string) => void;
  setIsWorkspaceOpen: (open: boolean) => void;
  setActiveTab: (tab: 'realtime' | 'browser' | 'files' | 'tools' | 'dataflow') => void;
  isWorkspaceOpen: boolean;
  handleRegenerate: (aiMessageId: string) => void;
  handleCopy: (text: string, id: string) => void;
  copiedId: string | null;
  latestHistoryMessageIdWithTodos: string | null;
  shouldAutoExpandTodos: boolean;
  msgEnd: React.RefObject<HTMLDivElement>;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  historyTotal,
  historyHasMore,
  loadingMoreHistory,
  loadMoreHistory,
  getMessageDisplay,
  setSelectedTurnId,
  setWorkspaceMessageId,
  setIsWorkspaceOpen,
  setActiveTab,
  isWorkspaceOpen,
  handleRegenerate,
  handleCopy,
  copiedId,
  latestHistoryMessageIdWithTodos,
  shouldAutoExpandTodos,
  msgEnd,
}) => {
  const [expandedStats, setExpandedStats] = useState<Set<string>>(new Set());

  return (
    <>
      {/* 显示总数和加载更多按钮（在消息列表顶部） */}
      {historyTotal !== null && (
        <div className="text-center py-4 border-b border-gray-100 mb-4">
          <div className="text-xs text-[#86868B] mb-3">
            共 {historyTotal} 条消息，已加载 {messages.length} 条
          </div>
          {historyHasMore && (
            <button
              onClick={loadMoreHistory}
              disabled={loadingMoreHistory}
              className="px-4 py-2 text-sm text-[#0066CC] hover:text-[#0052A3] disabled:text-[#86868B] disabled:cursor-not-allowed transition-colors rounded-lg border border-[#0066CC]/20 hover:border-[#0066CC]/40 hover:bg-blue-50"
            >
              {loadingMoreHistory ? (
                <span className="flex items-center justify-center">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  加载中...
                </span>
              ) : (
                `加载更多历史消息 (还有 ${historyTotal - messages.length} 条)`
              )}
            </button>
          )}
        </div>
      )}
      
      {messages.map((m, index) => {
        const hasTodoWrite = m.tool_calls && m.tool_calls.some(tc => isTodoTool(tc.tool_name));
        
        return (
          <div key={m.id} className={`flex flex-col ${m.sender === Sender.User ? 'items-end' : 'items-start'} animate-apple-slide group/msg`}>
            <div className="flex items-start space-x-3 max-w-[95%]">
              {/* AI 消息使用 MarkdownRenderer 渲染，用户消息直接显示 */}
              {m.sender === Sender.AI ? (() => {
                const display = getMessageDisplay(m.text || '');
                return (
                  <div className="px-4 py-3 text-[14px] leading-relaxed shadow-sm bg-white border border-black/[0.03] text-apple-gray rounded-[24px] rounded-tl-sm">
                    {display.isLong ? (
                      // 长消息（>100字符）：只显示提示，可点击
                      <button
                        onClick={() => {
                          if (m.conversation_turn_id) {
                            const turnId = String(m.conversation_turn_id);
                            setSelectedTurnId(turnId);
                            localStorage.setItem('selected_conversation_turn_id', turnId);
                            setWorkspaceMessageId(m.id);
                          } else {
                            setWorkspaceMessageId(m.id);
                          }
                          if (!isWorkspaceOpen) {
                            setIsWorkspaceOpen(true);
                          }
                          setActiveTab('realtime');
                        }}
                        className="text-center py-2 w-full hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                      >
                        <span className="text-[11px] text-blue-600 font-semibold hover:text-blue-700">
                          数据已经同步到工作区 →
                        </span>
                      </button>
                    ) : (
                      // 短消息（≤100字符）：显示完整内容，但也可以点击设置轮次
                      <div 
                        onClick={() => {
                          if (m.conversation_turn_id) {
                            const turnId = String(m.conversation_turn_id);
                            setSelectedTurnId(turnId);
                            localStorage.setItem('selected_conversation_turn_id', turnId);
                            setWorkspaceMessageId(m.id);
                          } else {
                            setWorkspaceMessageId(m.id);
                          }
                        }}
                        className="cursor-pointer"
                      >
                        <MarkdownRendererWithCharts content={display.chatContent} isStreaming={false} />
                      </div>
                    )}
                  </div>
                );
              })() : (
                // 用户消息也可以点击设置轮次
                <div 
                  onClick={() => {
                    if (m.conversation_turn_id) {
                      const turnId = String(m.conversation_turn_id);
                      setSelectedTurnId(turnId);
                      localStorage.setItem('selected_conversation_turn_id', turnId);
                      setWorkspaceMessageId(m.id);
                    } else {
                      setWorkspaceMessageId(m.id);
                    }
                  }}
                  className="px-4 py-3 text-[14px] font-semibold leading-relaxed shadow-sm bg-apple-blue text-white rounded-[24px] rounded-tr-sm shadow-blue-500/10 cursor-pointer hover:opacity-90 transition-opacity"
                >
                  {typeof m.text === 'string' ? m.text : String(m.text)}
                </div>
              )}
            </div>
            
            {/* Todo 列表显示 - 每个有 TodoWrite 的 AI 消息都显示对应的 TodoList */}
            {(() => {
              const isAIMessage = m.sender === Sender.AI;
              const hasTodoWrite = isAIMessage && m.tool_calls && m.tool_calls.some(tc => isTodoTool(tc.tool_name));
              
              if (hasTodoWrite) {
                // 🔧 修复：选择最新的 enhanced_todo_write 调用（数组中的最后一个）
                // 因为模型会多次调用 enhanced_todo_write 更新状态，我们需要最新的状态
                const todoWriteCalls = m.tool_calls?.filter(tc => isTodoTool(tc.tool_name)) || [];
                const todoWriteCall = todoWriteCalls.length > 0 ? todoWriteCalls[todoWriteCalls.length - 1] : null;
                if (todoWriteCall) {
                  // 尝试从 tool_output 中解析 enhanced_todos（包含更新后的父任务状态）
                  let enhanced_todos = null;
                  if (todoWriteCall.tool_output) {
                    try {
                      // 从 HTML 注释中提取 JSON
                      const match = todoWriteCall.tool_output.match(/<!-- ENHANCED_TODOS_JSON:(.+?) -->/);
                      if (match && match[1]) {
                        enhanced_todos = JSON.parse(match[1]);
                      }
                    } catch (e) {
                      // 解析失败，使用 tool_input
                      console.warn('Failed to parse enhanced_todos from tool_output:', e);
                    }
                  }

                  // 使用 enhanced_todos 或回退到 tool_input
                  let todosSource = enhanced_todos
                                 || todoWriteCall.tool_input?.todos
                                 || [];

                  const todos = parseTodosData(todosSource).map((todo: any, idx: number) => {
                    const status = todo.status || 'pending';
                    const activeForm = status === 'completed' ? undefined : todo.activeForm;
                    return {
                      id: todo.id || `todo-${index}-${idx}-${Math.random().toString(36).substr(2, 9)}`,
                      content: todo.content || '',
                      status: status,
                      activeForm: activeForm,
                      level: todo.level,
                      parentLevel: todo.parentLevel,
                      completed_subtasks: todo.completed_subtasks,
                      total_subtasks: todo.total_subtasks,
                    };
                  });
                  
                  const isLatestHistoryMessage = m.id === latestHistoryMessageIdWithTodos;
                  const shouldAutoExpand = shouldAutoExpandTodos || isLatestHistoryMessage;
                  
                  return (
                    <TodoList 
                      todos={todos}
                      defaultExpanded={false}
                      autoExpand={shouldAutoExpand}
                    />
                  );
                }
              }
              
              return null;
            })()}
            
            {/* ResultMessage 信息显示 */}
            {m.sender === Sender.AI && m.resultInfo && (() => {
              const isExpanded = expandedStats.has(m.id);
              const toggleExpanded = () => {
                setExpandedStats(prev => {
                  const next = new Set(prev);
                  if (next.has(m.id)) {
                    next.delete(m.id);
                  } else {
                    next.add(m.id);
                  }
                  return next;
                });
              };
              return (
                <div className="mt-2 max-w-[95%] w-full">
                  <div className="bg-[#F5F5F7] rounded-[16px] border border-black/[0.03] overflow-hidden">
                    {/* 可点击的标题栏 */}
                    <button
                      onClick={toggleExpanded}
                      className="w-full px-3 py-2 flex items-center justify-between hover:bg-[#EBEBED] transition-colors duration-200"
                    >
                      <span className="text-[11px] text-[#1D1D1F] font-semibold">统计信息</span>
                      {isExpanded ? (
                        <ChevronUp size={14} className="text-[#86868B]" />
                      ) : (
                        <ChevronDown size={14} className="text-[#86868B]" />
                      )}
                    </button>
                    
                    {/* 折叠内容 */}
                    {isExpanded && (
                      <div className="px-3 pb-3">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
                          {m.resultInfo.subtype && (
                            <div className="flex flex-col">
                              <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">类型</span>
                              <span className="text-[#1D1D1F] font-semibold">{m.resultInfo.subtype}</span>
                            </div>
                          )}
                          {m.resultInfo.duration_ms !== undefined && (
                            <div className="flex flex-col">
                              <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">总耗时</span>
                              <span className="text-[#1D1D1F] font-semibold">{(m.resultInfo.duration_ms / 1000).toFixed(2)}秒</span>
                            </div>
                          )}
                          {m.resultInfo.duration_api_ms !== undefined && (
                            <div className="flex flex-col">
                              <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">API耗时</span>
                              <span className="text-[#1D1D1F] font-semibold">{(m.resultInfo.duration_api_ms / 1000).toFixed(2)}秒</span>
                            </div>
                          )}
                          {m.resultInfo.num_turns !== undefined && (
                            <div className="flex flex-col">
                              <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">轮次</span>
                              <span className="text-[#1D1D1F] font-semibold">{m.resultInfo.num_turns}</span>
                            </div>
                          )}
                          {m.resultInfo.total_cost_usd !== null && m.resultInfo.total_cost_usd !== undefined && (
                            <div className="flex flex-col">
                              <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">费用</span>
                              <span className="text-[#1D1D1F] font-semibold">${m.resultInfo.total_cost_usd.toFixed(6)}</span>
                            </div>
                          )}
                          {m.resultInfo.is_error !== undefined && (
                            <div className="flex flex-col">
                              <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">状态</span>
                              <span className={`font-semibold ${m.resultInfo.is_error ? 'text-red-600' : 'text-green-600'}`}>
                                {m.resultInfo.is_error ? '错误' : '成功'}
                              </span>
                            </div>
                          )}
                          {m.resultInfo.usage && (
                            <div className="flex flex-col col-span-2 md:col-span-4">
                              <span className="text-[#86868B] font-bold uppercase tracking-wider mb-2">使用情况</span>
                              <div className="bg-white rounded-lg p-3 border border-black/[0.03] space-y-2">
                                {/* Token 使用情况 */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                  {m.resultInfo.usage.input_tokens !== undefined && (
                                    <div className="flex flex-col">
                                      <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider mb-0.5">输入Token</span>
                                      <span className="text-[12px] text-[#1D1D1F] font-semibold">{m.resultInfo.usage.input_tokens.toLocaleString()}</span>
                                    </div>
                                  )}
                                  {m.resultInfo.usage.output_tokens !== undefined && (
                                    <div className="flex flex-col">
                                      <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider mb-0.5">输出Token</span>
                                      <span className="text-[12px] text-[#1D1D1F] font-semibold">{m.resultInfo.usage.output_tokens.toLocaleString()}</span>
                                    </div>
                                  )}
                                  {m.resultInfo.usage.cache_read_input_tokens !== undefined && m.resultInfo.usage.cache_read_input_tokens > 0 && (
                                    <div className="flex flex-col">
                                      <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider mb-0.5">缓存读取</span>
                                      <span className="text-[12px] text-[#1D1D1F] font-semibold">{m.resultInfo.usage.cache_read_input_tokens.toLocaleString()}</span>
                                    </div>
                                  )}
                                  {m.resultInfo.usage.cache_creation_input_tokens !== undefined && m.resultInfo.usage.cache_creation_input_tokens > 0 && (
                                    <div className="flex flex-col">
                                      <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider mb-0.5">缓存创建</span>
                                      <span className="text-[12px] text-[#1D1D1F] font-semibold">{m.resultInfo.usage.cache_creation_input_tokens.toLocaleString()}</span>
                                    </div>
                                  )}
                                </div>
                                
                                {/* 服务层级和工具使用 */}
                                <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                                  {m.resultInfo.usage.service_tier && (
                                    <div className="flex items-center space-x-2">
                                      <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider">层级:</span>
                                      <span className="text-[11px] text-[#1D1D1F] font-semibold bg-blue-50 px-2 py-0.5 rounded-md">{m.resultInfo.usage.service_tier}</span>
                                    </div>
                                  )}
                                  {m.resultInfo.usage.server_tool_use && (
                                    <div className="flex items-center space-x-2">
                                      <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider">工具:</span>
                                      <span className="text-[11px] text-[#1D1D1F] font-semibold">
                                        {Object.entries(m.resultInfo.usage.server_tool_use)
                                          .filter(([_, value]) => typeof value === 'number' && value > 0)
                                          .map(([key, value]) => `${key}: ${value}`)
                                          .join(', ') || '无'}
                                      </span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })()}
            
            {m.sender === Sender.AI && (
              <div className="flex items-center space-x-4 mt-2 px-2 opacity-0 group-hover/msg:opacity-100 transition-opacity duration-300 transform translate-y-1 group-hover/msg:translate-y-0">
                <button onClick={() => handleRegenerate(m.id)} className="text-gray-300 hover:text-blue-600 transition-colors p-1" title="重新生成">
                  <RefreshCw size={13} />
                </button>
                <button onClick={() => handleCopy(m.text, m.id)} className="text-gray-300 hover:text-gray-900 transition-colors p-1" title="复制">
                  {copiedId === m.id ? <Check size={13} className="text-green-500" /> : <Copy size={13} />}
                </button>
                <div className="w-px h-3 bg-gray-200" />
                <button className="text-gray-300 hover:text-green-600 transition-colors p-1" title="有帮助">
                  <ThumbsUp size={13} />
                </button>
                <button className="text-gray-300 hover:text-red-500 transition-colors p-1" title="无帮助">
                  <ThumbsDown size={13} />
                </button>
              </div>
            )}
            
            <span className={`text-[8px] text-gray-400 font-black uppercase mt-1 px-1 tracking-[0.2em] opacity-40 ${m.sender === Sender.AI ? 'group-hover/msg:hidden' : ''}`}>{m.sender === Sender.User ? 'Identity' : 'X AI Core'}</span>
          </div>
        );
      })}
      <div ref={msgEnd} />
    </>
  );
};
