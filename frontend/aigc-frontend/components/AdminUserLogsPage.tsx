import React, { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { SessionHistory } from './SessionHistory';
import { ChatInterface } from './ChatInterface';
import { platformService } from '../services/platformService';
import { Message } from '../types';

interface AdminUserLogsPageProps {
  userId: number;
  username: string;
  onBack: () => void;
}

export const AdminUserLogsPage: React.FC<AdminUserLogsPageProps> = ({ userId, username, onBack }) => {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [stats, setStats] = useState<{
    total_sessions: number;
    total_messages: number;
    total_cost_usd: number;
  } | null>(null);
  const [userPreferences, setUserPreferences] = useState<{
    preferred_scenarios: string[];
    preferred_style: string;
    common_question_types: string[];
    learned_rules: string[];
    work_pattern: string;
    reasoning: string;
  } | null>(null);
  const [loadingPreferences, setLoadingPreferences] = useState(false);
  const [showUserPreferences, setShowUserPreferences] = useState(false);

  // 初始化加载统计信息和用户偏好
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const result = await platformService.getUserSessionsList(userId, 1, 0);
        if (result.stats) {
          setStats(result.stats);
          console.log('[AdminUserLogsPage] Loaded stats:', result.stats);
        }
      } catch (err) {
        console.error('[AdminUserLogsPage] Failed to load initial stats:', err);
      }

      // 加载用户偏好
      setLoadingPreferences(true);
      try {
        const preferences = await platformService.getUserPreferences(userId);
        setUserPreferences(preferences);
      } catch (err) {
        console.error('[AdminUserLogsPage] Failed to load user preferences:', err);
        setUserPreferences(null);
      } finally {
        setLoadingPreferences(false);
      }
    };
    loadInitialData();
  }, [userId]);

  // 自定义的获取会话列表函数（适配 SessionHistory 组件）
  const getUserSessionsList = useCallback(async (limit?: number, offset: number = 0) => {
    const result = await platformService.getUserSessionsList(userId, limit, offset);
    // 从返回结果中获取统计信息（更新统计）
    if (result.stats) {
      setStats(result.stats);
    }
    return result;
  }, [userId]);

  // 处理会话选择
  const handleSelectSession = useCallback((sessionId: string, sessionMessages: Message[]) => {
    setCurrentSessionId(sessionId);
    // 设置 localStorage，触发 ChatInterface 自动加载历史
    localStorage.setItem('chat_session_id', sessionId);
    // 手动触发 storage 事件（因为同页面不会自动触发）
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'chat_session_id',
      newValue: sessionId,
      storageArea: localStorage
    }));
  }, []);

  return (
    <div className="flex h-screen bg-white overflow-hidden">
      {/* 左侧边栏 - 复用 SessionHistory 组件 */}
      <aside className="w-80 bg-[#F5F5F7] border-r border-[#D2D2D7]/30 flex flex-col h-full overflow-hidden">
        <div className="flex-1 overflow-y-auto custom-scrollbar px-4 py-6">
          {/* 返回按钮和标题 */}
          <div className="mb-6">
            <button
              onClick={onBack}
              className="flex items-center space-x-2 text-[#0066CC] hover:text-[#0052A3] transition-colors mb-4"
            >
              <ArrowLeft size={16} />
              <span className="text-[13px] font-bold">返回管理中心</span>
            </button>
            <h2 className="text-[14px] font-black tracking-tight text-[#1D1D1F] uppercase mb-2">
              用户日志
            </h2>
            <p className="text-[12px] text-[#86868B] font-medium">{username}</p>
          </div>

          {/* 分割线 */}
          <div className="h-px bg-[#D2D2D7]/30 mb-6" />
          
          {/* 注意：这里不显示"新建对话"按钮，因为管理员查看的是历史记录 */}

          {/* 用户级别偏好 */}
          <div className="mb-6">
            <button
              onClick={() => setShowUserPreferences(!showUserPreferences)}
              className="w-full flex items-center justify-between p-4 bg-white rounded-2xl border border-[#D2D2D7]/30 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center space-x-2">
                <Sparkles size={16} className="text-purple-600" />
                <span className="text-[12px] font-black text-[#1D1D1F] uppercase tracking-widest">
                  用户级别偏好
                </span>
              </div>
              {showUserPreferences ? (
                <ChevronUp size={16} className="text-[#86868B]" />
              ) : (
                <ChevronDown size={16} className="text-[#86868B]" />
              )}
            </button>
            {showUserPreferences && (
              <div className="mt-3 p-4 bg-white rounded-2xl border border-[#D2D2D7]/30">
                {loadingPreferences ? (
                  <div className="flex items-center justify-center py-4">
                    <div className="w-4 h-4 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                ) : userPreferences ? (
                  <div className="space-y-3 text-xs">
                    <div>
                      <span className="font-black text-[#86868B] uppercase tracking-widest">常用场景:</span>
                      <p className="text-[#1D1D1F] mt-1">
                        {userPreferences.preferred_scenarios && Array.isArray(userPreferences.preferred_scenarios) && userPreferences.preferred_scenarios.length > 0
                          ? userPreferences.preferred_scenarios.join(', ')
                          : '暂无'}
                      </p>
                    </div>
                    <div>
                      <span className="font-black text-[#86868B] uppercase tracking-widest">回答风格:</span>
                      <p className="text-[#1D1D1F] mt-1">{userPreferences.preferred_style || '暂无'}</p>
                    </div>
                    <div>
                      <span className="font-black text-[#86868B] uppercase tracking-widest">常见问题类型:</span>
                      <p className="text-[#1D1D1F] mt-1">
                        {userPreferences.common_question_types && Array.isArray(userPreferences.common_question_types) && userPreferences.common_question_types.length > 0
                          ? userPreferences.common_question_types.join(', ')
                          : '暂无'}
                      </p>
                    </div>
                    {userPreferences.learned_rules && Array.isArray(userPreferences.learned_rules) && userPreferences.learned_rules.length > 0 && (
                      <div>
                        <span className="font-black text-[#86868B] uppercase tracking-widest">学习到的规则:</span>
                        <ul className="list-disc list-inside text-[#1D1D1F] mt-1 space-y-1">
                          {userPreferences.learned_rules.map((rule, idx) => (
                            <li key={idx}>{rule}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {userPreferences.work_pattern && (
                      <div>
                        <span className="font-black text-[#86868B] uppercase tracking-widest">工作模式:</span>
                        <p className="text-[#1D1D1F] mt-1">{userPreferences.work_pattern}</p>
                      </div>
                    )}
                    {userPreferences.reasoning && (
                      <div>
                        <span className="font-black text-[#86868B] uppercase tracking-widest">AI 分析推理:</span>
                        <p className="text-[#1D1D1F] mt-1 whitespace-pre-wrap">{userPreferences.reasoning}</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-[#86868B] text-center py-2">暂无偏好数据</p>
                )}
              </div>
            )}
          </div>

          {/* 分割线 */}
          <div className="h-px bg-[#D2D2D7]/30 mb-6" />

          {/* 统计信息 */}
          {stats && (
            <>
              <div className="grid grid-cols-2 gap-3 mb-6">
                <div className="bg-white p-4 rounded-2xl flex flex-col items-center border border-[#D2D2D7]/30">
                  <span className="text-xl font-black tracking-tight">{stats.total_sessions}</span>
                  <span className="text-[10px] text-[#86868B] font-black uppercase tracking-widest mt-1">
                    总会话
                  </span>
                </div>
                <div className="bg-white p-4 rounded-2xl flex flex-col items-center border border-[#D2D2D7]/30">
                  <span className="text-xl font-black tracking-tight">{stats.total_messages}</span>
                  <span className="text-[10px] text-[#86868B] font-black uppercase tracking-widest mt-1">
                    总消息
                  </span>
                </div>
              </div>
              <div className="h-px bg-[#D2D2D7]/30 mb-6" />
            </>
          )}

          {/* 最近对话标题 */}
          <h2 className="text-[14px] font-black tracking-tight text-[#1D1D1F] uppercase mb-6">
            最近对话
          </h2>

          {/* 会话列表 - 使用自定义的获取函数 */}
          <SessionHistory
            onSelectSession={handleSelectSession}
            currentSessionId={currentSessionId}
            getSessionsListFn={getUserSessionsList}
            showNewSessionButton={false}
          />
        </div>
      </aside>

      {/* 右侧主内容区 - 复用 ChatInterface 组件，但支持工作区功能 */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-white">
        <ChatInterface
          isWorkspaceOpen={true}
          setIsWorkspaceOpen={(open) => {
            // 允许切换工作区状态，但不影响原有功能
            console.log('[AdminUserLogsPage] Workspace state changed:', open);
          }}
          backendProvider="claude"
          onSessionChange={(sessionId) => {
            setCurrentSessionId(sessionId);
          }}
        />
      </main>
    </div>
  );
};
