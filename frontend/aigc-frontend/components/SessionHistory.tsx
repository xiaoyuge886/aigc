import React, { useState, useEffect } from 'react';
import { MessageSquare, Clock, ChevronRight, Loader2, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { getSessionsList, getConversationHistory, SessionInfo } from '../services/agentService';
import { platformService } from '../services/platformService';
import { Message, Sender } from '../types';

interface SessionHistoryProps {
  onSelectSession: (sessionId: string, messages: Message[]) => void;
  onNewSession?: () => void; // 新建会话回调
  currentSessionId: string | null;
  getSessionsListFn?: (limit?: number, offset?: number) => Promise<{
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
  }>; // 自定义获取会话列表函数（用于管理员查看用户日志）
  showNewSessionButton?: boolean; // 是否显示新建会话按钮（默认true）
}

const SESSIONS_PER_PAGE = 20; // 每页加载的会话数

export const SessionHistory: React.FC<SessionHistoryProps> = ({ 
  onSelectSession, 
  onNewSession,
  currentSessionId,
  getSessionsListFn,
  showNewSessionButton = true
}) => {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const [expandedSessionPreferences, setExpandedSessionPreferences] = useState<Set<string>>(new Set());
  const [sessionPreferences, setSessionPreferences] = useState<Map<string, {
    corrections: string[];
    context_preferences: string;
    feedback_summary: string;
  } | null>>(new Map());
  const [loadingSessionPreferences, setLoadingSessionPreferences] = useState<Set<string>>(new Set());

  // 使用自定义函数或默认函数
  const fetchSessionsList = getSessionsListFn || getSessionsList;

  // 加载会话列表
  useEffect(() => {
    const loadSessions = async () => {
      setLoading(true);
      setOffset(0);
      try {
        const response = await fetchSessionsList(SESSIONS_PER_PAGE, 0);
        setSessions(response.sessions);
        setTotal(response.total);
        setHasMore(response.has_more);
        setOffset(response.sessions.length);
        console.log('会话列表加载成功:', {
          count: response.sessions.length,
          total: response.total,
          has_more: response.has_more
        });
      } catch (error) {
        console.error('加载会话列表失败:', error);
      } finally {
        setLoading(false);
      }
    };

    loadSessions();
  }, [fetchSessionsList]);

  // 加载更多会话
  const loadMoreSessions = async () => {
    if (loadingMore || !hasMore) return;
    
    setLoadingMore(true);
    try {
      const response = await fetchSessionsList(SESSIONS_PER_PAGE, offset);
      setSessions(prev => [...prev, ...response.sessions]);
      setHasMore(response.has_more);
      setOffset(prev => prev + response.sessions.length);
      console.log('加载更多会话成功:', {
        new_count: response.sessions.length,
        total: response.total,
        has_more: response.has_more
      });
    } catch (error) {
      console.error('加载更多会话失败:', error);
    } finally {
      setLoadingMore(false);
    }
  };

  // 点击会话，切换会话（不显示详情）
  const handleSessionClick = async (sessionId: string) => {
    // 加载历史记录并通知父组件
    try {
      const history = await getConversationHistory(sessionId);
      if (history && history.messages) {
        onSelectSession(sessionId, history.messages);
      } else {
        onSelectSession(sessionId, []);
      }
    } catch (error) {
      console.error('[SessionHistory] 加载对话详情失败:', error);
      onSelectSession(sessionId, []);
    }
  };

  // 当 currentSessionId 变化时，自动加载对应的会话
  useEffect(() => {
    if (currentSessionId) {
      getConversationHistory(currentSessionId).then(history => {
        if (history && history.messages) {
          onSelectSession(currentSessionId, history.messages);
        } else {
          onSelectSession(currentSessionId, []);
        }
      }).catch(error => {
        console.error('加载对话详情失败:', error);
        onSelectSession(currentSessionId, []);
      });
    }
  }, [currentSessionId]);

  // 格式化日期
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (days === 1) {
      return '昨天';
    } else if (days < 7) {
      return `${days}天前`;
    } else {
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    }
  };

  // 获取会话预览文本
  const getSessionPreview = (sessionId: string): string => {
    // 简化预览文本，不依赖详情消息
    return `会话 ${sessionId.substring(0, 8)}...`;
  };

  // 加载Session偏好
  const loadSessionPreferences = async (sessionId: string) => {
    if (loadingSessionPreferences.has(sessionId) || sessionPreferences.has(sessionId)) {
      return; // 正在加载或已加载
    }

    setLoadingSessionPreferences(prev => new Set(prev).add(sessionId));
    try {
      const preferences = await platformService.getSessionPreferences(sessionId);
      setSessionPreferences(prev => new Map(prev).set(sessionId, preferences));
    } catch (err) {
      console.error(`[SessionHistory] Failed to load preferences for session ${sessionId}:`, err);
      setSessionPreferences(prev => new Map(prev).set(sessionId, null));
    } finally {
      setLoadingSessionPreferences(prev => {
        const newSet = new Set(prev);
        newSet.delete(sessionId);
        return newSet;
      });
    }
  };

  // 切换Session偏好显示
  const toggleSessionPreferences = (sessionId: string) => {
    const newExpanded = new Set(expandedSessionPreferences);
    if (newExpanded.has(sessionId)) {
      newExpanded.delete(sessionId);
    } else {
      newExpanded.add(sessionId);
      // 展开时加载偏好
      if (!sessionPreferences.has(sessionId) && !loadingSessionPreferences.has(sessionId)) {
        loadSessionPreferences(sessionId);
      }
    }
    setExpandedSessionPreferences(newExpanded);
  };

  if (loading) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-5 h-5 text-[#86868B] animate-spin" />
        </div>
      </div>
    );
  }

  if (loading && sessions.length === 0) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-5 h-5 text-[#86868B] animate-spin" />
        </div>
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="space-y-2">
        <div className="text-center py-8 text-[#86868B] text-sm">
          暂无会话记录
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* 显示总数 - 始终显示，即使为0也显示 */}
      <div className="px-4 py-2 text-xs text-[#86868B]">
        共 {total} 个会话
      </div>
      
      {sessions.map((session) => {
        const isCurrent = currentSessionId === session.session_id;
        
        return (
          <div key={session.session_id}>
            {/* 会话行 */}
            <div
              onClick={() => handleSessionClick(session.session_id)}
              className={`
                p-4 bg-[#F5F5F7] rounded-[24px] hover:bg-white hover:shadow-2xl hover:shadow-black/5 
                border border-transparent hover:border-blue-100 transition-all cursor-pointer group
                ${isCurrent ? 'ring-2 ring-blue-500/30' : ''}
              `}
            >
              <div className="flex items-start space-x-3">
                <MessageSquare 
                  size={14} 
                  className={`mt-1 flex-shrink-0 ${
                    isCurrent ? 'text-[#0066CC]' : 'text-[#86868B]'
                  }`} 
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className={`
                      text-[13px] font-bold line-clamp-1 leading-tight transition-colors
                      ${isCurrent ? 'text-[#0066CC]' : 'text-[#1D1D1F]'}
                    `}>
                      {getSessionPreview(session.session_id)}
                    </p>
                    <ChevronRight 
                      size={14} 
                      className="flex-shrink-0 text-[#86868B]" 
                    />
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center space-x-2 text-[10px] text-[#86868B]">
                      <Clock size={10} />
                      <span className="font-medium">{formatDate(session.last_activity)}</span>
                      {session.model && (
                        <>
                          <span>•</span>
                          <span className="font-bold uppercase">{session.model}</span>
                        </>
                      )}
                    </div>
                    {isCurrent && (
                      <span className="text-[9px] font-black text-blue-600 uppercase bg-blue-50 px-2 py-0.5 rounded-md">
                        当前
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Session偏好Tab */}
            <div className="mt-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleSessionPreferences(session.session_id);
                }}
                className="w-full flex items-center justify-between p-2 text-[10px] text-[#86868B] hover:text-[#1D1D1F] hover:bg-gray-50 rounded-lg transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <Sparkles size={12} className="text-purple-600" />
                  <span className="font-bold uppercase tracking-widest">Session偏好</span>
                </div>
                {expandedSessionPreferences.has(session.session_id) ? (
                  <ChevronUp size={12} />
                ) : (
                  <ChevronDown size={12} />
                )}
              </button>
              {expandedSessionPreferences.has(session.session_id) && (
                <div className="mt-2 p-3 bg-white rounded-xl border border-[#D2D2D7]/30">
                  {loadingSessionPreferences.has(session.session_id) ? (
                    <div className="flex items-center justify-center py-2">
                      <div className="w-3 h-3 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
                    </div>
                  ) : (() => {
                    const prefs = sessionPreferences.get(session.session_id);
                    return prefs ? (
                      <div className="space-y-2 text-[10px]">
                        {prefs.corrections.length > 0 && (
                          <div>
                            <span className="font-black text-[#86868B] uppercase tracking-widest">用户纠正:</span>
                            <ul className="list-disc list-inside text-[#1D1D1F] mt-1 space-y-0.5">
                              {prefs.corrections.map((correction, idx) => (
                                <li key={idx}>{correction}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {prefs.context_preferences && (
                          <div>
                            <span className="font-black text-[#86868B] uppercase tracking-widest">上下文偏好:</span>
                            <p className="text-[#1D1D1F] mt-1">{prefs.context_preferences}</p>
                          </div>
                        )}
                        {prefs.feedback_summary && (
                          <div>
                            <span className="font-black text-[#86868B] uppercase tracking-widest">反馈总结:</span>
                            <p className="text-[#1D1D1F] mt-1">{prefs.feedback_summary}</p>
                          </div>
                        )}
                        {prefs.corrections.length === 0 && !prefs.context_preferences && !prefs.feedback_summary && (
                          <p className="text-[#86868B] text-center py-1">暂无偏好数据</p>
                        )}
                      </div>
                    ) : (
                      <p className="text-[#86868B] text-center py-1">暂无偏好数据</p>
                    );
                  })()}
                </div>
              )}
            </div>

          </div>
        );
      })}
      
      {/* 加载更多按钮 */}
      {hasMore && (
        <div className="pt-2 border-t border-gray-100 mt-2">
          <button
            onClick={loadMoreSessions}
            disabled={loadingMore}
            className="w-full py-2.5 px-4 text-sm text-[#0066CC] hover:text-[#0052A3] disabled:text-[#86868B] disabled:cursor-not-allowed transition-colors rounded-lg border border-[#0066CC]/20 hover:border-[#0066CC]/40 hover:bg-blue-50 font-medium"
          >
            {loadingMore ? (
              <span className="flex items-center justify-center">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                加载中...
              </span>
            ) : (
              `加载更多会话 (${sessions.length}/${total})`
            )}
          </button>
        </div>
      )}
    </div>
  );
};

