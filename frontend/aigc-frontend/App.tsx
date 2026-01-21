
import React, { useState, useEffect } from 'react';
import {
  User, LogOut, MessageSquare, DollarSign, BarChart3, Menu, X, Plus, Search
} from 'lucide-react';
import { ChatInterface } from './components/ChatInterface';
import { ChatWrapper } from './components/ChatWrapper';
import { LandingPage } from './components/LandingPage';
import { SkillMarket } from './components/SkillMarket';
import { Editor } from './components/Editor';
import { LoginPage } from './components/LoginPage';
import { AdminDashboard } from './components/AdminDashboard';
import { SessionHistory } from './components/SessionHistory';
import { ScenarioEditor } from './components/ScenarioEditor';
import { UserLogsPage } from './components/UserLogsPage';
import { AdminUserLogsPage } from './components/AdminUserLogsPage';
import { HistoryItem, UserRole, Message } from './types';
import { authService } from './services/authService';
import { getLocalSessionId, clearLocalSessionId, getSessionsStats } from './services/agentService';

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState<{username: string, role: UserRole} | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('首页');
  const [isWorkspaceOpen, setIsWorkspaceOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [editingScenarioId, setEditingScenarioId] = useState<string | null>(null); // 正在编辑的业务场景ID，null表示创建模式
  const [adminDefaultSubTab, setAdminDefaultSubTab] = useState<'users' | 'usage' | 'audit' | 'resources'>('users'); // 管理中心的默认子标签
  const [resourceDefaultTab, setResourceDefaultTab] = useState<'prompts' | 'skills' | 'scenarios'>('prompts'); // 资源配置中心的默认标签
  const [viewingUserLogs, setViewingUserLogs] = useState<{ userId: number; username: string } | null>(null); // 正在查看的用户日志
  const [stats, setStats] = useState([
    { label: '总会话', value: '0', icon: <MessageSquare size={16} /> },
    { label: '总消息', value: '0', icon: <BarChart3 size={16} /> },
    { label: '总花费', value: '$0.00', icon: <DollarSign size={16} /> },
  ]);

  // 导航定义
  const baseNavItems = [
    { label: '首页', id: 'home' },
    { label: 'AI 助手', id: 'ai' },
    { label: '编辑器',id: 'editor' },
    { label: '技能市场', id: 'market' },
  ];

  const adminNavItems = [
    { label: '首页', id: 'home' },
    { label: 'AI 助手', id: 'ai' },
    { label: '编辑器',id: 'editor' },
    { label: '技能市场', id: 'market' },
    { label: '管理中心', id: 'admin' },
  ];

  // Admin 用户显示"管理中心"，普通用户显示基础导航
  const isAdmin = isLoggedIn && currentUser?.role === UserRole.Admin;
  const navItems = isAdmin ? adminNavItems : baseNavItems;
  
  // 调试：输出导航项信息（开发环境）- 已移除 console.log

  const historyItems: HistoryItem[] = [
    {
      id: '1',
      title: 'Aigc 2025',
      date: '2025/12/26 11:47:45',
      status: '已完成',
      tokenCount: '12339tok',
      cost: '$0.0477',
      messageCount: '1条'
    }
  ];

  const handleStartChat = () => {
    setActiveTab('AI 助手');
  };

  // 初始化：检查登录状态和当前会话
  useEffect(() => {
    const checkAuthStatus = async () => {
      const token = authService.getToken();
      const savedUser = authService.getUser();

      if (token && savedUser) {
        // 验证 token 是否仍然有效
        const result = await authService.getCurrentUser();
        if (result.success && result.data) {
          // 判断角色：role_id === 1 或 role_id === '1' 都视为 Admin
          // 备用方案：如果 role_id 为 null 但用户名是 "admin"，也视为 Admin
          const roleId = result.data.role_id;
          const username = result.data.username;
          const isAdminRole = roleId === 1 || String(roleId) === '1' || 
                             (roleId == null && username?.toLowerCase() === 'admin');
          const role = isAdminRole ? UserRole.Admin : UserRole.User;
          
          setCurrentUser({
            username: result.data.username,
            role
          });
          setIsLoggedIn(true);
        } else {
          // Token 无效，清除本地数据
          authService.logout();
        }
      }
      
      // 初始化当前会话ID
      const savedSessionId = getLocalSessionId();
      if (savedSessionId) {
        setCurrentSessionId(savedSessionId);
      }
      
      setIsLoading(false);
    };

    checkAuthStatus();
  }, []);

  // 加载统计数据
  useEffect(() => {
    if (isLoggedIn && activeTab === 'AI 助手') {
      const loadStats = async () => {
        try {
          const statsData = await getSessionsStats();
          if (statsData) {
            setStats([
              { label: '总会话', value: statsData.total_sessions.toString(), icon: <MessageSquare size={16} /> },
              { label: '总消息', value: statsData.total_messages.toString(), icon: <BarChart3 size={16} /> },
              { label: '总花费', value: `$${statsData.total_cost_usd.toFixed(4)}`, icon: <DollarSign size={16} /> },
            ]);
          }
        } catch (error) {
          // 静默处理错误
        }
      };
      loadStats();
    }
  }, [isLoggedIn, activeTab]);

  const handleLogin = (user: { username: string; role: string }) => {
    // 将字符串角色转换为 UserRole 枚举
    let userRole: UserRole;
    if (user.role === 'ADMIN' || user.role === UserRole.Admin) {
      userRole = UserRole.Admin;
    } else {
      userRole = UserRole.User;
    }
    setCurrentUser({ username: user.username, role: userRole });
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    authService.logout();
    setIsLoggedIn(false);
    setCurrentUser(null);
    setActiveTab('首页');
    setIsWorkspaceOpen(false);
  };

  const handleTabSwitch = (label: string) => {
    setActiveTab(label);
    setIsMobileMenuOpen(false);
  };

  const isPublicTab = activeTab === '首页';
  // 判断当前 Tab 是否需要侧边栏（对话相关）
  const isChatTab = activeTab === 'AI 助手';
  // 决定侧边栏是否应该在桌面端占据空间
  const shouldShowDesktopSidebar = isLoggedIn && isChatTab && !isWorkspaceOpen;

  const renderContent = () => {
    // 如果正在查看用户日志，显示日志页面
    if (viewingUserLogs) {
      return (
        <AdminUserLogsPage
          userId={viewingUserLogs.userId}
          username={viewingUserLogs.username}
          onBack={() => {
            setViewingUserLogs(null);
            setActiveTab('管理中心');
          }}
        />
      );
    }

    switch (activeTab) {
      case '首页':
        return <LandingPage onStartChat={handleStartChat} />;
      case '技能市场':
        return <SkillMarket />;
      case '编辑器':
        return <Editor />;
      case '管理中心':
        // 只有 Admin 用户才能访问管理中心
        if (!isLoggedIn || currentUser?.role !== UserRole.Admin) {
          return (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <h2 className="text-2xl font-black text-gray-900 mb-2">访问被拒绝</h2>
                <p className="text-gray-500">您没有权限访问管理中心</p>
              </div>
            </div>
          );
        }
        // 如果正在编辑业务场景，显示编辑页面
        if (editingScenarioId !== null) {
          return (
            <ScenarioEditor
              scenarioId={editingScenarioId === '' ? undefined : editingScenarioId}
              onBack={() => {
                setEditingScenarioId(null);
                setActiveTab('管理中心');
                // 返回时自动切换到业务场景列表
                setAdminDefaultSubTab('resources');
                setResourceDefaultTab('scenarios');
              }}
              onSave={() => {
                // 保存成功后刷新数据（由 ResourceCenter 处理）
                // 返回时自动切换到业务场景列表
                setAdminDefaultSubTab('resources');
                setResourceDefaultTab('scenarios');
              }}
            />
          );
        }
        return (
          <AdminDashboard
            onEditScenario={(scenarioId: string) => {
              setEditingScenarioId(scenarioId);
            }}
            onCreateScenario={() => {
              setEditingScenarioId(''); // 空字符串表示创建模式
            }}
            defaultSubTab={adminDefaultSubTab}
            defaultResourceTab={resourceDefaultTab}
            onViewUserLogs={(userId: number, username: string) => {
              setViewingUserLogs({ userId, username });
            }}
          />
        );
      case 'AI 助手':
        return (
          <ChatInterface 
            isWorkspaceOpen={isWorkspaceOpen} 
            setIsWorkspaceOpen={setIsWorkspaceOpen}
            onSessionChange={setCurrentSessionId}
          />
        );
      default:
        return <LandingPage onStartChat={handleStartChat} />;
    }
  };

  // 显示加载状态
  if (isLoading) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-[#FBFBFD]">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin" />
          <p className="text-sm font-bold text-[#86868B]">加载中...</p>
        </div>
      </div>
    );
  }

  if (!isLoggedIn && !isPublicTab) {
    return <LoginPage onLoginSuccess={handleLogin} onBackToHome={() => setActiveTab('首页')} />;
  }

  return (
    <div className="flex flex-col h-screen w-full bg-[#FBFBFD] font-sans overflow-hidden text-[#1D1D1F]">
      {/* Top Header - Apple Blur Effect */}
      <header className="h-14 md:h-16 bg-white/80 backdrop-blur-xl border-b border-[#D2D2D7]/30 px-4 md:px-6 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-2">
          <button 
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 md:hidden text-[#1D1D1F] hover:bg-[#F5F5F7] rounded-lg transition-colors"
          >
            {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          
          <div className="flex items-center">
            <div 
              className="flex items-center justify-center w-8 h-8 bg-[#1D1D1F] rounded-lg text-white ml-2 md:ml-0 cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => handleTabSwitch('首页')}
            >
              <span className="text-xs font-black italic tracking-tighter">X</span>
            </div>
            
          </div>
        </div>

        {/* Desktop Nav */}
        <nav className="hidden md:flex space-x-1 h-full items-center">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleTabSwitch(item.label)}
              className={`flex flex-col items-center justify-center px-4 h-full transition-all relative group ${
                activeTab === item.label 
                  ? 'text-[#0066CC]' 
                  : 'text-[#86868B] hover:text-[#1D1D1F]'
              }`}
            >
              <span className="text-[12px] font-black tracking-tight uppercase whitespace-nowrap">{item.label}</span>
              {activeTab === item.label && (
                <div className="absolute bottom-0 left-3 right-3 h-[2px] bg-[#0066CC] rounded-full" />
              )}
            </button>
          ))}
        </nav>

        <div className="flex items-center space-x-2 md:space-x-4">
          {isLoggedIn ? (
            <div className="flex items-center space-x-2 md:space-x-4">
              <div className="flex items-center space-x-2.5 px-3 py-1.5 rounded-full hover:bg-[#F5F5F7] transition-all cursor-pointer border border-transparent">
                <div className={`w-8 h-8 rounded-full ${currentUser?.role === UserRole.Admin ? 'bg-red-500' : 'bg-[#1D1D1F]'} flex items-center justify-center text-white shadow-sm ring-1 ring-white/10`}>
                  <User size={16} />
                </div>
                <div className="hidden sm:flex flex-col text-left">
                  <span className="text-[10px] font-black tracking-tight leading-none">{currentUser?.username}</span>
                  <span className="text-[8px] font-bold text-gray-400 tracking-widest uppercase mt-0.5">{currentUser?.role}</span>
                </div>
              </div>
              <button 
                onClick={handleLogout}
                className="hidden sm:flex items-center space-x-2 border border-[#D2D2D7] bg-white px-3 py-1.5 rounded-xl text-xs font-bold text-[#1D1D1F] hover:bg-[#F5F5F7] transition-all active:scale-95"
              >
                <LogOut size={14} className="text-[#86868B]" />
              </button>
            </div>
          ) : (
            <button 
              onClick={() => handleTabSwitch('AI 助手')} 
              className="px-6 py-1.5 bg-[#1D1D1F] text-white rounded-full text-[11px] font-black uppercase tracking-widest hover:bg-black transition-all active:scale-95"
            >
              登录
            </button>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden relative">
        {/* 精简侧边栏 - 仅在对话相关页面显示，或者移动端开启菜单时显示 */}
        <aside 
          className={`
            fixed inset-y-0 left-0 z-40 bg-white border-r border-[#D2D2D7]/30 transform transition-all duration-500 ease-in-out lg:relative lg:translate-x-0
            ${isMobileMenuOpen ? 'w-[280px] translate-x-0 shadow-2xl' : '-translate-x-full w-0 lg:w-0 overflow-hidden'}
            ${shouldShowDesktopSidebar ? 'lg:w-[300px] lg:translate-x-0' : ''}
            flex flex-col overflow-y-auto custom-scrollbar
          `}
        >
          <div className="p-6 w-full min-w-[280px]">
            {/* Mobile Navigation Section - 仅在移动端菜单模式下显示 */}
            <div className={`${isMobileMenuOpen ? 'block' : 'hidden'} lg:hidden mb-8 space-y-2`}>
              <h2 className="text-[11px] font-black text-[#86868B] mb-4 uppercase tracking-[0.2em]">主导航</h2>
              <div className="grid grid-cols-1 gap-1">
                {navItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleTabSwitch(item.label)}
                    className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
                      activeTab === item.label 
                        ? 'bg-blue-50 text-blue-600 font-bold' 
                        : 'text-gray-500 hover:bg-gray-50'
                    }`}
                  >
                    <span className="text-[13px] uppercase tracking-tight">{item.label}</span>
                  </button>
                ))}
              </div>
              <div className="h-px bg-gray-100 my-6" />
            </div>

            {/* 对话列表与统计 - 仅在对话标签页显示 */}
            <div className={`transition-opacity duration-300 ${isChatTab ? 'opacity-100' : 'opacity-0'}`}>
              {/* 1. 新建对话按钮（最顶部） */}
              <div
                onClick={() => {
                  clearLocalSessionId();
                  localStorage.removeItem('selected_conversation_turn_id');
                  window.dispatchEvent(new StorageEvent('storage', {
                    key: 'chat_session_id',
                    newValue: null,
                    storageArea: localStorage
                  }));
                  setCurrentSessionId(null);
                }}
                className="
                  p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-[24px] 
                  hover:from-blue-100 hover:to-blue-200 hover:shadow-xl hover:shadow-blue-500/10
                  border border-blue-200 transition-all cursor-pointer group
                  flex items-center justify-center space-x-2 mb-6
                "
              >
                <Plus 
                  size={16} 
                  className="text-blue-600 group-hover:scale-110 transition-transform" 
                />
                <span className="text-[13px] font-bold text-blue-600">
                  新建对话
                </span>
              </div>

              {/* 分割线 */}
              <div className="h-px bg-[#D2D2D7]/30 mb-6" />

              {/* 2. 最近对话标题 */}
              <h2 className="text-[14px] font-black tracking-tight text-[#1D1D1F] uppercase mb-6">最近对话</h2>

              {/* 3. 统计 */}
              <div className="grid grid-cols-2 gap-3 mb-6">
                {stats.slice(0, 2).map((s, idx) => (
                  <div key={idx} className="bg-[#F5F5F7] p-4 rounded-2xl flex flex-col items-center border border-transparent hover:border-[#D2D2D7]/30 transition-all">
                    <span className="text-xl font-black tracking-tight">{s.value}</span>
                    <span className="text-[10px] text-[#86868B] font-black uppercase tracking-widest mt-1">{s.label}</span>
                  </div>
                ))}
              </div>

              {/* 分割线 */}
              <div className="h-px bg-[#D2D2D7]/30 mb-6" />

              {/* 4. 历史对话列表 */}
              <SessionHistory 
                onSelectSession={(sessionId, messages) => {
                  // 当选择会话时，更新当前会话ID并加载消息到ChatInterface
                  setCurrentSessionId(sessionId);
                  // 保存到 localStorage（触发 storage 事件，让 ChatInterface 响应）
                  localStorage.setItem('chat_session_id', sessionId);
                  // 手动触发 storage 事件（因为同页面不会自动触发）
                  window.dispatchEvent(new StorageEvent('storage', {
                    key: 'chat_session_id',
                    newValue: sessionId,
                    storageArea: localStorage
                  }));
                }}
                onNewSession={() => {
                  // 新建对话：清除当前会话ID
                  setCurrentSessionId(null);
                }}
                currentSessionId={currentSessionId}
              />
            </div>

            {/* Mobile Footer Action */}
            <div className="mt-8 md:hidden">
                {isLoggedIn ? (
                  <button 
                    onClick={handleLogout}
                    className="w-full flex items-center justify-center space-x-2 border border-red-100 bg-red-50/30 px-4 py-3 rounded-xl text-xs font-bold text-red-600 hover:bg-red-50 transition-all"
                  >
                    <LogOut size={14} />
                    <span>退出登录</span>
                  </button>
                ) : (
                  <button 
                    onClick={() => handleTabSwitch('AI 助手')}
                    className="w-full py-3 bg-[#1D1D1F] text-white rounded-xl text-xs font-black uppercase tracking-widest"
                  >
                    立即登录
                  </button>
                )}
            </div>
          </div>
        </aside>

        {/* Mask Overlay for Mobile Menu */}
        {isMobileMenuOpen && (
          <div 
            className="fixed inset-0 z-30 bg-black/10 backdrop-blur-sm lg:hidden transition-opacity"
            onClick={() => setIsMobileMenuOpen(false)}
          />
        )}

        <main className="flex-1 flex flex-col relative overflow-hidden bg-white w-full transition-all duration-500">
           {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default App;
