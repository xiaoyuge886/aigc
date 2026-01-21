import React, { useState, useEffect } from 'react';
import { X, ChevronDown, ChevronUp } from 'lucide-react';
import { platformService } from '../services/platformService';

interface UserLogsDialogProps {
  userId: number;
  username: string;
  onClose: () => void;
}

export const UserLogsDialog: React.FC<UserLogsDialogProps> = ({ userId, username, onClose }) => {
  const [userLogs, setUserLogs] = useState<any>(null);
  const [loadingUserLogs, setLoadingUserLogs] = useState(false);
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set());
  const [expandedTurns, setExpandedTurns] = useState<Set<string>>(new Set());

  useEffect(() => {
    const loadLogs = async () => {
      setLoadingUserLogs(true);
      try {
        const logs = await platformService.getUserLogs(userId);
        setUserLogs(logs);
      } catch (err) {
        console.error('Failed to load user logs:', err);
      } finally {
        setLoadingUserLogs(false);
      }
    };
    loadLogs();
  }, [userId]);

  const toggleSession = (sessionId: string) => {
    const newExpanded = new Set(expandedSessions);
    if (newExpanded.has(sessionId)) {
      newExpanded.delete(sessionId);
    } else {
      newExpanded.add(sessionId);
    }
    setExpandedSessions(newExpanded);
  };

  const toggleTurn = (turnId: string) => {
    const newExpanded = new Set(expandedTurns);
    if (newExpanded.has(turnId)) {
      newExpanded.delete(turnId);
    } else {
      newExpanded.add(turnId);
    }
    setExpandedTurns(newExpanded);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white rounded-[40px] border border-gray-100 shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col animate-scale-in">
        {/* 对话框头部 */}
        <div className="p-8 border-b border-gray-50 flex items-center justify-between flex-shrink-0">
          <div>
            <h2 className="text-2xl font-black text-gray-900">用户日志详情</h2>
            {userLogs && (
              <p className="text-sm text-gray-500 mt-1">
                {userLogs.username || username} • {userLogs.total_sessions} 个会话 • {userLogs.total_conversation_turns} 轮对话 • ${userLogs.total_cost_usd?.toFixed(4) || '0.0000'}
              </p>
            )}
          </div>
          <button
            onClick={() => {
              onClose();
              setExpandedSessions(new Set());
              setExpandedTurns(new Set());
            }}
            className="p-2 text-gray-400 hover:text-gray-900 hover:bg-gray-50 rounded-xl transition-all"
          >
            <X size={20} />
          </button>
        </div>

        {/* 对话框内容 */}
        <div className="flex-1 overflow-y-auto p-8 space-y-4 custom-scrollbar">
          {loadingUserLogs ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : userLogs && userLogs.sessions && userLogs.sessions.length > 0 ? (
            userLogs.sessions.map((session: any) => (
              <div key={session.session_id} className="bg-gray-50 rounded-2xl border border-gray-100 overflow-hidden">
                {/* Session Header */}
                <div
                  className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => toggleSession(session.session_id)}
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <span className="text-xs font-black text-gray-400 uppercase tracking-widest">Session</span>
                      <span className="text-sm font-black text-gray-900">{session.session_id.substring(0, 8)}...</span>
                      {session.model && (
                        <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-full">{session.model}</span>
                      )}
                    </div>
                    <div className="mt-1 text-xs text-gray-500">
                      {new Date(session.created_at).toLocaleString('zh-CN')} • {session.total_turns} 轮 • ${session.total_cost_usd?.toFixed(4) || '0.0000'} • {session.total_tokens?.toLocaleString() || 0} tokens
                    </div>
                  </div>
                  {expandedSessions.has(session.session_id) ? (
                    <ChevronUp size={20} className="text-gray-400" />
                  ) : (
                    <ChevronDown size={20} className="text-gray-400" />
                  )}
                </div>

                {/* Session Content */}
                {expandedSessions.has(session.session_id) && (
                  <div className="px-4 pb-4 space-y-3">
                    {session.conversation_turns && session.conversation_turns.length > 0 ? (
                      session.conversation_turns.map((turn: any) => (
                        <div key={turn.conversation_turn_id} className="bg-white rounded-xl border border-gray-200 p-4">
                          {/* Turn Header */}
                          <div
                            className="flex items-center justify-between cursor-pointer mb-3"
                            onClick={() => toggleTurn(turn.conversation_turn_id)}
                          >
                            <div className="flex items-center space-x-2">
                              <span className="text-xs font-black text-gray-400 uppercase tracking-widest">Turn</span>
                              <span className="text-xs font-black text-gray-900">{turn.conversation_turn_id.substring(0, 8)}...</span>
                              {turn.total_cost_usd && (
                                <span className="text-xs text-green-600">${turn.total_cost_usd.toFixed(4)}</span>
                              )}
                              {turn.total_tokens && (
                                <span className="text-xs text-gray-500">{turn.total_tokens.toLocaleString()} tokens</span>
                              )}
                            </div>
                            {expandedTurns.has(turn.conversation_turn_id) ? (
                              <ChevronUp size={16} className="text-gray-400" />
                            ) : (
                              <ChevronDown size={16} className="text-gray-400" />
                            )}
                          </div>

                          {/* Turn Details */}
                          {expandedTurns.has(turn.conversation_turn_id) && (
                            <div className="space-y-3 text-xs">
                              {/* User Message */}
                              {turn.user_message && (
                                <div className="bg-blue-50 rounded-lg p-3">
                                  <div className="font-black text-blue-600 mb-1">用户消息</div>
                                  <div className="text-gray-700 whitespace-pre-wrap">
                                    {turn.user_message.content || JSON.stringify(turn.user_message, null, 2)}
                                  </div>
                                </div>
                              )}

                              {/* Tool Calls */}
                              {turn.tool_calls && turn.tool_calls.length > 0 && (
                                <div className="bg-purple-50 rounded-lg p-3">
                                  <div className="font-black text-purple-600 mb-2">工具调用 ({turn.tool_calls.length})</div>
                                  {turn.tool_calls.map((tool: any, idx: number) => (
                                    <div key={idx} className="mb-2 last:mb-0 bg-white rounded p-2">
                                      <div className="font-bold text-gray-900">{tool.name || tool.tool_name || 'Unknown Tool'}</div>
                                      <pre className="text-[10px] text-gray-600 mt-1 overflow-x-auto">
                                        {JSON.stringify(tool.input || tool.tool_input || tool, null, 2)}
                                      </pre>
                                    </div>
                                  ))}
                                </div>
                              )}

                              {/* Tool Results */}
                              {turn.tool_results && turn.tool_results.length > 0 && (
                                <div className="bg-green-50 rounded-lg p-3">
                                  <div className="font-black text-green-600 mb-2">工具结果 ({turn.tool_results.length})</div>
                                  {turn.tool_results.map((result: any, idx: number) => (
                                    <div key={idx} className="mb-2 last:mb-0 bg-white rounded p-2">
                                      <pre className="text-[10px] text-gray-600 overflow-x-auto">
                                        {typeof result.content === 'string' ? result.content : JSON.stringify(result, null, 2)}
                                      </pre>
                                    </div>
                                  ))}
                                </div>
                              )}

                              {/* Assistant Messages */}
                              {turn.assistant_messages && turn.assistant_messages.length > 0 && (
                                <div className="bg-gray-50 rounded-lg p-3">
                                  <div className="font-black text-gray-600 mb-2">助手回复 ({turn.assistant_messages.length})</div>
                                  {turn.assistant_messages.map((msg: any, idx: number) => (
                                    <div key={idx} className="mb-2 last:mb-0 text-gray-700 whitespace-pre-wrap">
                                      {msg.content || JSON.stringify(msg, null, 2)}
                                    </div>
                                  ))}
                                </div>
                              )}

                              {/* Config Used */}
                              {turn.config_used && (
                                <div className="bg-amber-50 rounded-lg p-3">
                                  <div className="font-black text-amber-600 mb-2">使用的配置</div>
                                  <pre className="text-[10px] text-gray-600 overflow-x-auto">
                                    {JSON.stringify(turn.config_used, null, 2)}
                                  </pre>
                                </div>
                              )}

                              {/* Config Sources */}
                              {turn.config_sources && (
                                <div className="bg-indigo-50 rounded-lg p-3">
                                  <div className="font-black text-indigo-600 mb-2">配置来源</div>
                                  <pre className="text-[10px] text-gray-600 overflow-x-auto">
                                    {JSON.stringify(turn.config_sources, null, 2)}
                                  </pre>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-4 text-gray-400 text-xs">该会话暂无对话轮次</div>
                    )}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-12 text-gray-400">
              暂无日志数据
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
