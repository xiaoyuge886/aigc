import React, { useState, useEffect } from 'react';
import { ArrowLeft, ChevronRight, Calendar, DollarSign, Hash } from 'lucide-react';
import { platformService } from '../services/platformService';

interface UserLogsPageProps {
  userId: number;
  username: string;
  onBack: () => void;
}

type ViewMode = 'sessions' | 'turns' | 'turn-detail';

export const UserLogsPage: React.FC<UserLogsPageProps> = ({ userId, username, onBack }) => {
  const [userLogs, setUserLogs] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('sessions');
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);
  
  // 分页状态
  const [sessionPage, setSessionPage] = useState(1);
  const [turnPage, setTurnPage] = useState(1);
  const [pageSize] = useState(20); // 每页显示数量

  useEffect(() => {
    const loadLogs = async () => {
      setLoading(true);
      try {
        const logs = await platformService.getUserLogs(userId);
        setUserLogs(logs);
      } catch (err) {
        console.error('Failed to load user logs:', err);
      } finally {
        setLoading(false);
      }
    };
    loadLogs();
  }, [userId]);

  const selectedSession = userLogs?.sessions?.find((s: any) => s.session_id === selectedSessionId);
  const selectedTurn = selectedSession?.conversation_turns?.find((t: any) => t.conversation_turn_id === selectedTurnId);

  const handleSessionClick = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setViewMode('turns');
  };

  const handleTurnClick = (turnId: string) => {
    setSelectedTurnId(turnId);
    setViewMode('turn-detail');
  };

  const handleBack = () => {
    if (viewMode === 'turn-detail') {
      setViewMode('turns');
      setSelectedTurnId(null);
    } else if (viewMode === 'turns') {
      setViewMode('sessions');
      setSelectedSessionId(null);
    } else {
      onBack();
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[#FBFBFD] custom-scrollbar">
      <div className="max-w-7xl mx-auto p-6 md:p-12 space-y-6">
        {/* Header */}
        <div className="flex items-center space-x-4 mb-8">
          <button
            onClick={handleBack}
            className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
            title="返回"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-3xl font-black text-gray-900 tracking-tight">
              {viewMode === 'sessions' && '会话列表'}
              {viewMode === 'turns' && '对话轮次列表'}
              {viewMode === 'turn-detail' && '对话详情'}
            </h1>
            <p className="text-gray-500 font-medium mt-1">
              {username}
              {viewMode === 'turns' && selectedSession && ` • ${selectedSession.session_id.substring(0, 8)}...`}
              {viewMode === 'turn-detail' && selectedTurn && ` • ${selectedTurn.conversation_turn_id.substring(0, 8)}...`}
            </p>
          </div>
        </div>

        {/* Breadcrumb */}
        <div className="flex items-center space-x-2 text-sm text-gray-500 mb-6">
          <button
            onClick={() => {
              setViewMode('sessions');
              setSelectedSessionId(null);
              setSelectedTurnId(null);
            }}
            className={`hover:text-gray-900 ${viewMode === 'sessions' ? 'font-black text-gray-900' : ''}`}
          >
            会话列表
          </button>
          {viewMode !== 'sessions' && (
            <>
              <ChevronRight size={16} />
              <button
                onClick={() => {
                  setViewMode('turns');
                  setSelectedTurnId(null);
                }}
                className={`hover:text-gray-900 ${viewMode === 'turns' ? 'font-black text-gray-900' : ''}`}
              >
                对话轮次
              </button>
            </>
          )}
          {viewMode === 'turn-detail' && (
            <>
              <ChevronRight size={16} />
              <span className="font-black text-gray-900">详情</span>
            </>
          )}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : viewMode === 'sessions' ? (
          /* Session List */
          <div className="space-y-4">
            {userLogs?.sessions && userLogs.sessions.length > 0 ? (
              userLogs.sessions.map((session: any) => (
                <div
                  key={session.session_id}
                  onClick={() => handleSessionClick(session.session_id)}
                  className="bg-white rounded-2xl border border-gray-100 p-6 hover:shadow-lg cursor-pointer transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-3">
                        <Hash size={18} className="text-gray-400" />
                        <span className="text-sm font-black text-gray-900">{session.session_id.substring(0, 8)}...</span>
                        {session.model && (
                          <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-full">{session.model}</span>
                        )}
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                        <div className="flex items-center space-x-2 text-gray-600">
                          <Calendar size={14} />
                          <span>{new Date(session.created_at).toLocaleString('zh-CN')}</span>
                        </div>
                        <div className="text-gray-600">
                          <span className="font-bold">{session.total_turns}</span> 轮对话
                        </div>
                        <div className="flex items-center space-x-2 text-green-600">
                          <DollarSign size={14} />
                          <span className="font-bold">${session.total_cost_usd?.toFixed(4) || '0.0000'}</span>
                        </div>
                        <div className="text-gray-600">
                          <span className="font-bold">{session.total_tokens?.toLocaleString() || 0}</span> tokens
                        </div>
                      </div>
                    </div>
                    <ChevronRight size={20} className="text-gray-400 ml-4" />
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-24 text-gray-400">
                暂无会话数据
              </div>
            )}
          </div>
        ) : viewMode === 'turns' ? (
          /* Turn List */
          <div className="space-y-4">
            {selectedSession?.conversation_turns && selectedSession.conversation_turns.length > 0 ? (
              selectedSession.conversation_turns.map((turn: any) => (
                <div
                  key={turn.conversation_turn_id}
                  onClick={() => handleTurnClick(turn.conversation_turn_id)}
                  className="bg-white rounded-2xl border border-gray-100 p-6 hover:shadow-lg cursor-pointer transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-3">
                        <Hash size={18} className="text-gray-400" />
                        <span className="text-sm font-black text-gray-900">{turn.conversation_turn_id.substring(0, 8)}...</span>
                        {turn.total_cost_usd && (
                          <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded-full">
                            ${turn.total_cost_usd.toFixed(4)}
                          </span>
                        )}
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs mb-3">
                        <div className="flex items-center space-x-2 text-gray-600">
                          <Calendar size={14} />
                          <span>{new Date(turn.created_at).toLocaleString('zh-CN')}</span>
                        </div>
                        {turn.total_tokens && (
                          <div className="text-gray-600">
                            <span className="font-bold">{turn.total_tokens.toLocaleString()}</span> tokens
                          </div>
                        )}
                        {turn.duration_ms && (
                          <div className="text-gray-600">
                            <span className="font-bold">{(turn.duration_ms / 1000).toFixed(2)}</span> 秒
                          </div>
                        )}
                        {turn.tool_calls && turn.tool_calls.length > 0 && (
                          <div className="text-purple-600">
                            <span className="font-bold">{turn.tool_calls.length}</span> 个工具调用
                          </div>
                        )}
                      </div>
                      {turn.user_message && (
                        <div className="bg-blue-50 rounded-lg p-3 text-xs">
                          <div className="font-black text-blue-600 mb-1">用户消息</div>
                          <div className="text-gray-700 line-clamp-2">
                            {turn.user_message.content || JSON.stringify(turn.user_message).substring(0, 100)}...
                          </div>
                        </div>
                      )}
                    </div>
                    <ChevronRight size={20} className="text-gray-400 ml-4" />
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-24 text-gray-400">
                该会话暂无对话轮次
              </div>
            )}
          </div>
        ) : (
          /* Turn Detail */
          selectedTurn && (
            <div className="space-y-6">
              {/* Turn Info */}
              <div className="bg-white rounded-2xl border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-black text-gray-900 mb-2">对话轮次详情</h3>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>ID: {selectedTurn.conversation_turn_id}</span>
                      <span>创建时间: {new Date(selectedTurn.created_at).toLocaleString('zh-CN')}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4 text-xs">
                    {selectedTurn.total_cost_usd && (
                      <div className="text-green-600">
                        <span className="font-bold">${selectedTurn.total_cost_usd.toFixed(4)}</span>
                      </div>
                    )}
                    {selectedTurn.total_tokens && (
                      <div className="text-gray-600">
                        <span className="font-bold">{selectedTurn.total_tokens.toLocaleString()}</span> tokens
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* User Message */}
              {selectedTurn.user_message && (
                <div className="bg-blue-50 rounded-2xl border border-blue-100 p-6">
                  <div className="font-black text-blue-600 mb-3 text-sm uppercase tracking-wider">用户消息</div>
                  <div className="text-gray-700 whitespace-pre-wrap text-sm">
                    {selectedTurn.user_message.content || JSON.stringify(selectedTurn.user_message, null, 2)}
                  </div>
                </div>
              )}

              {/* Tool Calls */}
              {selectedTurn.tool_calls && selectedTurn.tool_calls.length > 0 && (
                <div className="bg-purple-50 rounded-2xl border border-purple-100 p-6">
                  <div className="font-black text-purple-600 mb-3 text-sm uppercase tracking-wider">
                    工具调用 ({selectedTurn.tool_calls.length})
                  </div>
                  <div className="space-y-3">
                    {selectedTurn.tool_calls.map((tool: any, idx: number) => (
                      <div key={idx} className="bg-white rounded-lg p-4">
                        <div className="font-bold text-gray-900 mb-2">{tool.name || tool.tool_name || 'Unknown Tool'}</div>
                        <pre className="text-xs text-gray-600 overflow-x-auto">
                          {JSON.stringify(tool.input || tool.tool_input || tool, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tool Results */}
              {selectedTurn.tool_results && selectedTurn.tool_results.length > 0 && (
                <div className="bg-green-50 rounded-2xl border border-green-100 p-6">
                  <div className="font-black text-green-600 mb-3 text-sm uppercase tracking-wider">
                    工具结果 ({selectedTurn.tool_results.length})
                  </div>
                  <div className="space-y-3">
                    {selectedTurn.tool_results.map((result: any, idx: number) => (
                      <div key={idx} className="bg-white rounded-lg p-4">
                        <pre className="text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap">
                          {typeof result.content === 'string' ? result.content : JSON.stringify(result, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Assistant Messages */}
              {selectedTurn.assistant_messages && selectedTurn.assistant_messages.length > 0 && (
                <div className="bg-gray-50 rounded-2xl border border-gray-100 p-6">
                  <div className="font-black text-gray-600 mb-3 text-sm uppercase tracking-wider">
                    助手回复 ({selectedTurn.assistant_messages.length})
                  </div>
                  <div className="space-y-3">
                    {selectedTurn.assistant_messages.map((msg: any, idx: number) => (
                      <div key={idx} className="bg-white rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap">
                        {msg.content || JSON.stringify(msg, null, 2)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Config Used */}
              {selectedTurn.config_used && (
                <div className="bg-amber-50 rounded-2xl border border-amber-100 p-6">
                  <div className="font-black text-amber-600 mb-3 text-sm uppercase tracking-wider">使用的配置</div>
                  <pre className="text-xs text-gray-600 overflow-x-auto bg-white rounded-lg p-4">
                    {JSON.stringify(selectedTurn.config_used, null, 2)}
                  </pre>
                </div>
              )}

              {/* Config Sources */}
              {selectedTurn.config_sources && (
                <div className="bg-indigo-50 rounded-2xl border border-indigo-100 p-6">
                  <div className="font-black text-indigo-600 mb-3 text-sm uppercase tracking-wider">配置来源</div>
                  <pre className="text-xs text-gray-600 overflow-x-auto bg-white rounded-lg p-4">
                    {JSON.stringify(selectedTurn.config_sources, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )
        )}
      </div>
    </div>
  );
};
