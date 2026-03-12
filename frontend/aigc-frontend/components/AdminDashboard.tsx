
import React, { useState, useEffect } from 'react';
import {
  Users, BarChart, History, Shield, MoreHorizontal, Search,
  ArrowUpRight, ArrowDownRight, UserPlus, Filter, Download,
  Activity, Cpu, CreditCard, ChevronRight, Settings, X, HelpCircle, FileText, ChevronDown, ChevronUp, Package
} from 'lucide-react';
import { SystemUser, UserRole, UsageLog } from '../types';
import { GlassCard } from './GlassCard';
import { ResourceCenter } from './ResourceCenter';
import { UserLogsDialog } from './UserLogsDialog';
import { UserPromptEditor } from './UserPromptEditor';
import { ToolSelector } from './ToolSelector';
import { authService, User, RegisterRequest } from '../services/authService';
import { platformService, UserConfig, UserConfigCreate } from '../services/platformService';

interface AdminDashboardProps {
  onEditPackage?: (packageId: number) => void;  // 编辑能力包
  onCreatePackage?: () => void;  // 创建能力包
  defaultSubTab?: 'users' | 'usage' | 'audit' | 'resources'; // 默认显示的子标签
  defaultResourceTab?: 'prompts' | 'skills' | 'packages'; // 资源配置中心的默认标签
  onViewUserLogs?: (userId: number, username: string) => void; // 查看用户日志回调
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({
  onEditPackage,
  onCreatePackage,
  defaultSubTab = 'users',
  defaultResourceTab,
  onViewUserLogs
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'users' | 'usage' | 'audit' | 'resources'>(defaultSubTab || 'users');
  
  // 当 defaultSubTab 改变时，更新 activeSubTab
  useEffect(() => {
    if (defaultSubTab) {
      setActiveSubTab(defaultSubTab);
    }
  }, [defaultSubTab]);
  const [users, setUsers] = useState<SystemUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAddUserDialog, setShowAddUserDialog] = useState(false);
  const [addingUser, setAddingUser] = useState(false);
  const [addUserError, setAddUserError] = useState<string | null>(null);
  const [newUserForm, setNewUserForm] = useState<RegisterRequest & { role_id?: number }>({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role_id: undefined,
  });
  
  // 用户设置对话框状态
  const [showUserSettingsDialog, setShowUserSettingsDialog] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedUserName, setSelectedUserName] = useState<string>('');
  const [userConfig, setUserConfig] = useState<UserConfig | null>(null);
  const [loadingUserSettings, setLoadingUserSettings] = useState(false);
  const [savingUserSettings, setSavingUserSettings] = useState(false);
  const [userSettingsError, setUserSettingsError] = useState<string | null>(null);
  const [showUserLogsDialog, setShowUserLogsDialog] = useState(false);
  const [selectedUserForLogs, setSelectedUserForLogs] = useState<{ id: number; username: string } | null>(null);

  // 用户插件绑定对话框状态
  const [showUserPluginsDialog, setShowUserPluginsDialog] = useState(false);
  const [userPlugins, setUserPlugins] = useState<{bindings: any[], available_packages: any[]}>({bindings: [], available_packages: []});
  const [loadingUserPlugins, setLoadingUserPlugins] = useState(false);
  const [configForm, setConfigForm] = useState<UserConfigCreate>({
    default_system_prompt: '',
    default_allowed_tools: [],
    default_model: 'sonnet',
    permission_mode: 'acceptEdits',
    max_turns: 100,
    work_dir: '',
    custom_tools: undefined,
    custom_skills: [],
  });

  // 加载用户列表
  useEffect(() => {
    if (activeSubTab === 'users') {
      loadUsers();
    }
  }, [activeSubTab]);

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await authService.getAllUsers();
      if (result.success && result.data) {
        // 将后端返回的 User 格式转换为前端的 SystemUser 格式
        const systemUsers: SystemUser[] = result.data.map((user: User) => {
          // 根据 role_id 判断角色
          let role: UserRole = UserRole.User;
          if (user.role_id === 1) {
            role = UserRole.Admin;
          } else if (user.role_id === 2) {
            role = UserRole.Developer;
          }
          
          return {
            id: user.id,
            username: user.username,
            role: role,
            email: user.email,
            full_name: user.full_name,
            avatar_url: user.avatar_url,
            role_id: user.role_id,
            is_active: user.is_active,
            is_verified: user.is_verified,
            created_at: user.created_at,
            last_login: user.last_login,
            // 这些字段暂时使用默认值，后续可以从其他 API 获取
            status: user.is_active ? 'active' : 'suspended',
            tokenLimit: 100000, // TODO: 从用户配置或配额 API 获取
            tokenUsed: 0, // TODO: 从使用统计 API 获取
            joinDate: user.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN') : '',
          };
        });
        setUsers(systemUsers);
      } else {
        setError(result.error || '加载用户列表失败');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理新增用户
  const handleAddUser = async () => {
    // 表单验证
    if (!newUserForm.username || !newUserForm.email || !newUserForm.password) {
      setAddUserError('请填写必填字段：用户名、邮箱和密码');
      return;
    }

    if (newUserForm.username.length < 3) {
      setAddUserError('用户名至少需要3个字符');
      return;
    }

    if (newUserForm.password.length < 6) {
      setAddUserError('密码至少需要6个字符');
      return;
    }

    setAddingUser(true);
    setAddUserError(null);

    try {
      const result = await authService.register({
        username: newUserForm.username,
        email: newUserForm.email,
        password: newUserForm.password,
        full_name: newUserForm.full_name || undefined,
      });

      if (result.success) {
        // 如果指定了角色，需要更新用户角色（这需要额外的 API）
        // TODO: 如果需要设置角色，可以调用更新用户 API
        
        // 关闭对话框并重置表单
        setShowAddUserDialog(false);
        setNewUserForm({
          username: '',
          email: '',
          password: '',
          full_name: '',
          role_id: undefined,
        });
        
        // 刷新用户列表
        await loadUsers();
      } else {
        setAddUserError(result.error || '创建用户失败');
      }
    } catch (err) {
      setAddUserError(err instanceof Error ? err.message : '创建用户失败');
    } finally {
      setAddingUser(false);
    }
  };

  // 加载用户设置
  const loadUserSettings = async (userId: number) => {
    setLoadingUserSettings(true);
    setUserSettingsError(null);
    try {
      // 加载用户配置
      const config = await platformService.getUserConfig(userId);
      setUserConfig(config);
      if (config) {
        setConfigForm({
          default_system_prompt: config.default_system_prompt || '',
          default_allowed_tools: config.default_allowed_tools || [],
          default_model: config.default_model || 'sonnet',
          permission_mode: config.permission_mode || 'acceptEdits',
          max_turns: config.max_turns || 100,
          work_dir: config.work_dir || '',
          custom_tools: config.custom_tools,
          custom_skills: config.custom_skills || [],
        });
      } else {
        // 重置为默认值
        setConfigForm({
          default_system_prompt: '',
          default_allowed_tools: [],
          default_model: 'sonnet',
          permission_mode: 'acceptEdits',
          max_turns: 100,
          work_dir: '',
          custom_tools: undefined,
          custom_skills: [],
        });
      }
    } catch (err) {
      setUserSettingsError(err instanceof Error ? err.message : '加载用户设置失败');
    } finally {
      setLoadingUserSettings(false);
    }
  };

  // 加载用户插件绑定
  const loadUserPackages = async (userId: number) => {
    setLoadingUserPlugins(true);
    try {
      const data = await platformService.getUserPackages(userId);
      setUserPlugins(data);
    } catch (err) {
      console.error('Failed to load user packages:', err);
    } finally {
      setLoadingUserPlugins(false);
    }
  };

  // 绑定插件到用户
  const handleBindPackage = async (packageId: number) => {
    if (!selectedUserForPlugins) return;
    try {
      await platformService.bindPackageToUser(selectedUserForPlugins.id, packageId);
      await loadUserPackages(selectedUserForPlugins.id);
    } catch (err) {
      console.error('Failed to bind package:', err);
    }
  };

  // 解绑用户插件
  const handleUnbindPackage = async (packageId: number) => {
    if (!selectedUserForPlugins) return;
    try {
      await platformService.unbindPackageFromUser(selectedUserForPlugins.id, packageId);
      await loadUserPackages(selectedUserForPlugins.id);
    } catch (err) {
      console.error('Failed to unbind package:', err);
    }
  };

  // 保存用户设置
  const handleSaveUserSettings = async () => {
    if (!selectedUserId) return;

    setSavingUserSettings(true);
    setUserSettingsError(null);

    try {
      // 保存用户配置
      const configToSave = {
        ...configForm,
      };

      if (userConfig) {
        await platformService.updateUserConfig(selectedUserId, configToSave);
      } else {
        await platformService.createUserConfig(selectedUserId, configToSave);
      }

      // 关闭对话框
      setShowUserSettingsDialog(false);
      setSelectedUserId(null);
      setSelectedUserName('');

      // 刷新用户列表
      await loadUsers();
    } catch (err) {
      setUserSettingsError(err instanceof Error ? err.message : '保存用户设置失败');
    } finally {
      setSavingUserSettings(false);
    }
  };

  // Mock Logs
  const mockLogs: UsageLog[] = [
    { id: 'L1', userId: '2', username: 'zhangsan', model: 'gemini-3-flash', tokens: 1240, cost: 0.012, timestamp: '2025-05-20 14:30' },
    { id: 'L2', userId: '1', username: 'admin', model: 'gemini-3-pro', tokens: 4500, cost: 0.15, timestamp: '2025-05-20 15:10' },
    { id: 'L3', userId: '3', username: 'dev_expert', model: 'gemini-3-flash', tokens: 800, cost: 0.008, timestamp: '2025-05-20 16:45' },
  ];

  const StatCard = ({ title, value, trend, icon, color }: any) => (
    <div className="flex-1 min-w-[220px] bg-white rounded-[32px] p-6 border border-gray-100 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.02)] hover:shadow-[0_12px_40px_-8px_rgba(0,0,0,0.06)] transition-all duration-500 group">
      <div className="flex justify-between items-start mb-6">
        <div className={`p-4 rounded-2xl ${color} bg-opacity-10 ${color.replace('text-', 'bg-')} group-hover:scale-110 transition-transform`}>
          {icon}
        </div>
        {trend && (
          <div className={`flex items-center text-[10px] font-black ${trend.startsWith('+') ? 'text-green-500' : 'text-red-500'} bg-gray-50 px-2 py-1 rounded-full`}>
            {trend.startsWith('+') ? <ArrowUpRight size={10} className="mr-0.5" /> : <ArrowDownRight size={10} className="mr-0.5" />}
            {trend}
          </div>
        )}
      </div>
      <div>
        <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-1">{title}</p>
        <p className="text-3xl font-black text-gray-900 tracking-tighter">{value}</p>
      </div>
    </div>
  );

  return (
    <div className="flex-1 overflow-y-auto bg-[#FBFBFD] custom-scrollbar p-6 md:p-12 space-y-12 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-4xl font-black text-gray-900 tracking-tight">管理中心</h1>
          <p className="text-gray-500 font-medium mt-1">全局监控、用户配额与系统审计。</p>
        </div>
        <div className="flex bg-gray-200/50 backdrop-blur-md p-1 rounded-[18px] border border-gray-100">
          {[
            { id: 'users', label: '用户管理', icon: <Users size={14}/> },
            { id: 'resources', label: '资源配置', icon: <Settings size={14}/> },
            { id: 'usage', label: '用量分析', icon: <Activity size={14}/> },
            { id: 'audit', label: '审计日志', icon: <Shield size={14}/> }
          ].map(tab => (
            <button 
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id as any)}
              className={`flex items-center space-x-2 px-6 py-2.5 text-[11px] font-black rounded-[14px] transition-all ${activeSubTab === tab.id ? 'bg-white shadow-sm text-blue-600' : 'text-gray-500 hover:text-gray-900'}`}
            >
              {tab.icon}
              <span className="uppercase tracking-widest">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Overview Stats */}
      {/* <div className="flex flex-wrap gap-6">
        <StatCard title="Total Users" value="1,284" trend="+12.5%" icon={<Users size={20}/>} color="text-blue-600" />
        <StatCard title="Daily Tokens" value="4.2M" trend="+24.1%" icon={<Cpu size={20}/>} color="text-purple-600" />
        <StatCard title="Estimated Cost" value="$128.45" trend="-2.4%" icon={<CreditCard size={20}/>} color="text-green-600" />
        <StatCard title="System Load" value="12%" trend="Stable" icon={<Activity size={20}/>} color="text-amber-600" />
      </div> */}

      {/* Sub Tab Content */}
      <div className="space-y-6">
        {activeSubTab === 'users' && (
          <div className="bg-white rounded-[40px] border border-gray-100 shadow-sm overflow-hidden">
            <div className="p-8 border-b border-gray-50 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="relative group max-w-sm w-full">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={16} />
                <input 
                  type="text" 
                  placeholder="搜索用户、邮箱或 UID..." 
                  className="w-full pl-12 pr-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-[13px] font-bold focus:bg-white focus:border-blue-100 focus:outline-none transition-all"
                />
              </div>
              <div className="flex items-center space-x-3">
                 <button className="p-3 bg-gray-50 text-gray-500 rounded-2xl hover:bg-gray-100 transition-all"><Filter size={18}/></button>
                 <button 
                   onClick={() => setShowAddUserDialog(true)}
                   className="flex items-center space-x-2 px-6 py-3 bg-[#1D1D1F] text-white rounded-2xl text-xs font-black hover:bg-black transition-all shadow-xl active:scale-95"
                 >
                    <UserPlus size={16} />
                    <span className="uppercase tracking-widest">新增用户</span>
                 </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-gray-50/50 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] border-b border-gray-50">
                    <th className="px-8 py-5">用户信息</th>
                    <th className="px-8 py-5">角色权限</th>
                    <th className="px-8 py-5">状态</th>
                    <th className="px-8 py-5">Token 消耗率 (Used/Limit)</th>
                    <th className="px-8 py-5">创建时间</th>
                    <th className="px-8 py-5 text-right">管理</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="px-8 py-12 text-center text-gray-400">
                        <div className="flex items-center justify-center space-x-2">
                          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                          <span>加载中...</span>
                        </div>
                      </td>
                    </tr>
                  ) : error ? (
                    <tr>
                      <td colSpan={6} className="px-8 py-12 text-center text-red-500">
                        {error}
                      </td>
                    </tr>
                  ) : users.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-8 py-12 text-center text-gray-400">
                        暂无用户数据
                      </td>
                    </tr>
                  ) : (
                    users.map(user => (
                    <tr key={user.id} className="hover:bg-gray-50/30 transition-colors group">
                      <td className="px-8 py-6">
                        <div className="flex items-center space-x-4">
                          <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-black text-lg transition-all ${user.status === 'active' ? 'bg-blue-50 text-blue-600' : 'bg-gray-100 text-gray-400'}`}>
                            {user.username.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="text-[14px] font-black text-gray-900 tracking-tight">{user.username}</p>
                            <p className="text-[11px] text-gray-400 font-medium">{user.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-8 py-6">
                        <span className={`text-[9px] font-black px-3 py-1 rounded-full border ${
                          user.role === UserRole.Admin ? 'text-red-600 bg-red-50 border-red-100' :
                          user.role === UserRole.Developer ? 'text-purple-600 bg-purple-50 border-purple-100' :
                          'text-blue-600 bg-blue-50 border-blue-100'
                        } uppercase tracking-widest`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="px-8 py-6">
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${user.status === 'active' ? 'bg-green-500 animate-pulse' : 'bg-gray-300'}`} />
                          <span className="text-[11px] font-black text-gray-600 uppercase tracking-widest">{user.status}</span>
                        </div>
                      </td>
                      <td className="px-8 py-6">
                        <div className="space-y-2 max-w-[180px]">
                          <div className="flex justify-between text-[10px] font-black">
                            <span className="text-gray-900">{(user.tokenUsed / 1000).toFixed(1)}K</span>
                            <span className="text-gray-400">{(user.tokenLimit / 1000).toFixed(1)}K</span>
                          </div>
                          <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                            <div 
                              className={`h-full transition-all duration-1000 ${user.tokenUsed / user.tokenLimit > 0.8 ? 'bg-amber-500' : 'bg-blue-500'}`}
                              style={{ width: `${Math.min((user.tokenUsed / user.tokenLimit) * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="px-8 py-6 text-[11px] font-bold text-gray-500">{user.joinDate}</td>
                      <td className="px-8 py-6 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button 
                            onClick={() => {
                              if (onViewUserLogs) {
                                onViewUserLogs(user.id, user.username);
                              } else {
                                setSelectedUserForLogs({ id: user.id, username: user.username });
                                setShowUserLogsDialog(true);
                              }
                            }}
                            className="p-2 text-gray-300 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all"
                            title="查看日志"
                          >
                            <FileText size={20} />
                          </button>
                          <button
                            onClick={() => {
                              setSelectedUserId(user.id);
                              setSelectedUserName(user.username);
                              setShowUserSettingsDialog(true);
                              loadUserSettings(user.id);
                            }}
                            className="p-2 text-gray-300 hover:text-gray-900 hover:bg-gray-50 rounded-xl transition-all"
                            title="用户设置"
                          >
                            <Settings size={20} />
                          </button>
                          <button
                            onClick={() => {
                              setSelectedUserForPlugins({ id: user.id, username: user.username });
                              setShowUserPluginsDialog(true);
                              loadUserPackages(user.id);
                            }}
                            className="p-2 text-gray-300 hover:text-purple-600 hover:bg-purple-50 rounded-xl transition-all"
                            title="插件管理"
                          >
                            <Package size={20} />
                          </button>
                        </div>
                      </td>
                    </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeSubTab === 'usage' && (
          <div className="grid lg:grid-cols-2 gap-8">
            <div className="bg-white p-10 rounded-[48px] border border-gray-100 shadow-sm group">
              <div className="flex items-center justify-between mb-10">
                <h3 className="text-xl font-black text-gray-900 tracking-tight flex items-center space-x-3">
                  <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl"><BarChart size={20} /></div>
                  <span>Token 流量趋势</span>
                </h3>
                <span className="text-[10px] font-black text-blue-500 bg-blue-50 px-3 py-1 rounded-full uppercase tracking-widest">Live 实时更新</span>
              </div>
              <div className="h-64 flex items-end space-x-3">
                {[45, 60, 40, 75, 90, 65, 80, 50, 40, 55, 70, 85].map((h, i) => (
                  <div key={i} className="flex-1 group/bar relative">
                    <div 
                      className="w-full bg-blue-500/10 rounded-t-xl group-hover/bar:bg-blue-600 group-hover/bar:shadow-lg group-hover/bar:shadow-blue-500/20 transition-all duration-700 ease-out"
                      style={{ height: `${h}%` }}
                    />
                    <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 text-[9px] font-black text-gray-400 group-hover/bar:text-blue-600 transition-colors">
                      {i + 1}月
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white p-10 rounded-[48px] border border-gray-100 shadow-sm">
               <div className="flex items-center justify-between mb-10">
                <h3 className="text-xl font-black text-gray-900 tracking-tight flex items-center space-x-3">
                  <div className="p-3 bg-purple-50 text-purple-600 rounded-2xl"><Activity size={20} /></div>
                  <span>模型资源分配</span>
                </h3>
              </div>
              <div className="space-y-8">
                {[
                  { name: 'Gemini 3 Flash-Preview', usage: 65, color: 'bg-blue-500' },
                  { name: 'Gemini 3 Pro-Preview', usage: 25, color: 'bg-purple-500' },
                  { name: 'Gemini 2.5 Flash', usage: 10, color: 'bg-amber-500' }
                ].map((item, idx) => (
                  <div key={idx} className="space-y-3">
                    <div className="flex justify-between text-[12px] font-black">
                      <span className="text-gray-700 tracking-tight">{item.name}</span>
                      <span className="text-blue-600">{item.usage}%</span>
                    </div>
                    <div className="h-2.5 w-full bg-gray-50 rounded-full overflow-hidden">
                      <div className={`h-full ${item.color} shadow-sm`} style={{ width: `${item.usage}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeSubTab === 'audit' && (
          <div className="bg-white rounded-[40px] border border-gray-100 shadow-sm overflow-hidden">
             <div className="p-8 border-b border-gray-50 flex items-center justify-between">
               <h3 className="text-[11px] font-black text-gray-400 uppercase tracking-[0.2em]">系统交互实时全景</h3>
               <div className="flex space-x-2">
                  <button className="p-2.5 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors text-gray-400"><Download size={18}/></button>
               </div>
             </div>
             <div className="divide-y divide-gray-50">
                {mockLogs.map(log => (
                  <div key={log.id} className="p-8 flex flex-col md:flex-row md:items-center justify-between hover:bg-gray-50/50 transition-all gap-6 group">
                    <div className="flex items-start space-x-6">
                      <div className="p-4 bg-gray-50 text-gray-400 rounded-2xl group-hover:bg-blue-600 group-hover:text-white transition-all">
                        <Activity size={20} />
                      </div>
                      <div>
                        <p className="text-[14px] font-black text-gray-900 tracking-tight">用户 <span className="text-blue-600">{log.username}</span> 调用了模型接口</p>
                        <p className="text-[11px] text-gray-400 font-bold uppercase tracking-widest mt-1">
                          MODEL: <span className="text-gray-900">{log.model}</span> • {log.timestamp}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-12">
                      <div className="text-right">
                        <p className="text-[15px] font-black text-gray-900 tracking-tighter">{log.tokens.toLocaleString()} <span className="text-[10px] text-gray-400 uppercase tracking-widest ml-1">Tokens</span></p>
                        <p className="text-[10px] text-green-600 font-black uppercase tracking-widest mt-0.5">Est. ${log.cost}</p>
                      </div>
                      <button className="w-10 h-10 flex items-center justify-center bg-gray-50 hover:bg-white hover:shadow-md rounded-full text-gray-300 hover:text-blue-600 transition-all">
                        <ChevronRight size={18} strokeWidth={3} />
                      </button>
                    </div>
                  </div>
                ))}
             </div>
          </div>
        )}

        {activeSubTab === 'resources' && (
          <div className="bg-white rounded-[40px] border border-gray-100 shadow-sm overflow-hidden p-6">
            <ResourceCenter
              onEditPackage={onEditPackage}
              onCreatePackage={onCreatePackage}
              defaultTab={defaultResourceTab}
            />
          </div>
        )}

      </div>

      {/* 新增用户对话框 */}
      {showAddUserDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-[40px] border border-gray-100 shadow-2xl w-full max-w-md animate-scale-in">
            {/* 对话框头部 */}
            <div className="p-8 border-b border-gray-50 flex items-center justify-between">
              <h2 className="text-2xl font-black text-gray-900">新增用户</h2>
              <button
                onClick={() => {
                  setShowAddUserDialog(false);
                  setNewUserForm({
                    username: '',
                    email: '',
                    password: '',
                    full_name: '',
                    role_id: undefined,
                  });
                  setAddUserError(null);
                }}
                className="p-2 text-gray-400 hover:text-gray-900 hover:bg-gray-50 rounded-xl transition-all"
              >
                <X size={20} />
              </button>
            </div>

            {/* 表单内容 */}
            <div className="p-8 space-y-6">
              {addUserError && (
                <div className="p-4 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm font-bold">
                  {addUserError}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                    用户名 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={newUserForm.username}
                    onChange={(e) => setNewUserForm({ ...newUserForm, username: e.target.value })}
                    placeholder="请输入用户名（至少3个字符）"
                    className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-sm font-bold focus:bg-white focus:border-blue-100 focus:outline-none transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                    邮箱 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    value={newUserForm.email}
                    onChange={(e) => setNewUserForm({ ...newUserForm, email: e.target.value })}
                    placeholder="请输入邮箱地址"
                    className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-sm font-bold focus:bg-white focus:border-blue-100 focus:outline-none transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                    密码 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    value={newUserForm.password}
                    onChange={(e) => setNewUserForm({ ...newUserForm, password: e.target.value })}
                    placeholder="请输入密码（至少6个字符）"
                    className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-sm font-bold focus:bg-white focus:border-blue-100 focus:outline-none transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                    全名
                  </label>
                  <input
                    type="text"
                    value={newUserForm.full_name || ''}
                    onChange={(e) => setNewUserForm({ ...newUserForm, full_name: e.target.value })}
                    placeholder="请输入全名（可选）"
                    className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-sm font-bold focus:bg-white focus:border-blue-100 focus:outline-none transition-all"
                  />
                </div>
              </div>
            </div>

            {/* 对话框底部 */}
            <div className="p-8 border-t border-gray-50 flex items-center justify-end space-x-3">
              <button
                onClick={() => {
                  setShowAddUserDialog(false);
                  setNewUserForm({
                    username: '',
                    email: '',
                    password: '',
                    full_name: '',
                    role_id: undefined,
                  });
                  setAddUserError(null);
                }}
                className="px-6 py-3 text-sm font-black text-gray-600 hover:bg-gray-50 rounded-2xl transition-all"
                disabled={addingUser}
              >
                取消
              </button>
              <button
                onClick={handleAddUser}
                disabled={addingUser}
                className="px-6 py-3 bg-[#1D1D1F] text-white rounded-2xl text-sm font-black hover:bg-black transition-all shadow-xl active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {addingUser ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>创建中...</span>
                  </>
                ) : (
                  <>
                    <UserPlus size={16} />
                    <span>创建用户</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 用户设置对话框 */}
      {showUserSettingsDialog && selectedUserId && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-[40px] border border-gray-100 shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col animate-scale-in">
            {/* 对话框头部 */}
            <div className="p-8 border-b border-gray-50 flex items-center justify-between flex-shrink-0">
              <div>
                <h2 className="text-2xl font-black text-gray-900">用户设置</h2>
                {selectedUserName && (
                  <p className="text-sm text-gray-500 mt-1">用户: {selectedUserName}</p>
                )}
              </div>
              <button
                onClick={() => {
                  setShowUserSettingsDialog(false);
                  setSelectedUserId(null);
                  setSelectedUserName('');
                  setUserConfig(null);
                  setUserSettingsError(null);
                  setSelectedScenarioIds([]);
                  setUserCustomPrompt('');
                  setSettingsTab('scenarios');
                }}
                className="p-2 text-gray-400 hover:text-gray-900 hover:bg-gray-50 rounded-xl transition-all"
              >
                <X size={20} />
              </button>
            </div>

            {/* 对话框内容 */}
            <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
              {loadingUserSettings ? (
                <div className="flex items-center justify-center py-12">
                  <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : (
                <>
                  {userSettingsError && (
                    <div className="p-4 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm font-bold">
                      {userSettingsError}
                    </div>
                  )}

                  {/* 用户配置部分 */}
                  <div className="space-y-6">
                    <div className="flex items-center space-x-2">
                      <h3 className="text-lg font-black text-gray-900">用户配置</h3>
                      <div className="relative">
                        <button
                          type="button"
                          onClick={() => setShowConfigPriorityHelp(!showConfigPriorityHelp)}
                          className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                          title="配置优先级说明"
                        >
                          <HelpCircle size={18} />
                        </button>
                        {showConfigPriorityHelp && (
                          <div className="absolute left-0 top-8 z-50 w-96 bg-white border border-gray-200 rounded-2xl shadow-2xl p-6 animate-scale-in">
                            <div className="flex items-start justify-between mb-4">
                              <h4 className="text-sm font-black text-gray-900">配置优先级说明</h4>
                              <button
                                onClick={() => setShowConfigPriorityHelp(false)}
                                className="p-1 text-gray-400 hover:text-gray-900"
                              >
                                <X size={16} />
                              </button>
                            </div>
                            <div className="space-y-3 text-xs">
                              <p className="text-gray-600 font-bold mb-3">配置按以下优先级合并（从高到低）：</p>
                              <div className="space-y-2">
                                <div className="flex items-start space-x-2">
                                  <span className="font-black text-blue-600 min-w-[80px]">Request</span>
                                  <div>
                                    <p className="font-black text-gray-900">请求级别（最高）</p>
                                    <p className="text-gray-500 text-[10px] mt-0.5">API 请求参数，每次可不同</p>
                                  </div>
                                </div>
                                <div className="flex items-start space-x-2">
                                  <span className="font-black text-purple-600 min-w-[80px]">Session</span>
                                  <div>
                                    <p className="font-black text-gray-900">会话级别</p>
                                    <p className="text-gray-500 text-[10px] mt-0.5">会话创建时保存，同一会话共享</p>
                                  </div>
                                </div>
                                <div className="flex items-start space-x-2">
                                  <span className="font-black text-orange-600 min-w-[80px]">User</span>
                                  <div>
                                    <p className="font-black text-gray-900">用户级别</p>
                                    <p className="text-gray-500 text-[10px] mt-0.5">用户个人配置（当前配置）</p>
                                  </div>
                                </div>
                                <div className="flex items-start space-x-2">
                                  <span className="font-black text-green-600 min-w-[80px]">Scenario</span>
                                  <div>
                                    <p className="font-black text-gray-900">场景级别</p>
                                    <p className="text-gray-500 text-[10px] mt-0.5">业务场景配置，可关联多个用户</p>
                                  </div>
                                </div>
                                <div className="flex items-start space-x-2">
                                  <span className="font-black text-gray-500 min-w-[80px]">Global</span>
                                  <div>
                                    <p className="font-black text-gray-900">全局级别（最低）</p>
                                    <p className="text-gray-500 text-[10px] mt-0.5">系统默认配置，所有用户共享</p>
                                  </div>
                                </div>
                              </div>
                              <div className="mt-4 pt-4 border-t border-gray-100">
                                <p className="text-gray-600 font-bold text-[10px]">
                                  💡 提示：高优先级配置会覆盖低优先级配置
                                </p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                          默认系统提示词
                        </label>
                        <textarea
                          value={configForm.default_system_prompt || ''}
                          onChange={(e) => setConfigForm({ ...configForm, default_system_prompt: e.target.value })}
                          placeholder="请输入默认系统提示词"
                          rows={4}
                          className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-sm font-bold focus:bg-white focus:border-blue-100 focus:outline-none transition-all resize-none"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                          默认模型
                        </label>
                        <select
                          value={configForm.default_model || 'sonnet'}
                          onChange={(e) => setConfigForm({ ...configForm, default_model: e.target.value })}
                          className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-sm font-bold focus:bg-white focus:border-blue-100 focus:outline-none transition-all"
                        >
                          <option value="sonnet">Claude Sonnet</option>
                          <option value="opus">Claude Opus</option>
                          <option value="haiku">Claude Haiku</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                          权限模式
                        </label>
                        <select
                          value={configForm.permission_mode || 'acceptEdits'}
                          onChange={(e) => setConfigForm({ ...configForm, permission_mode: e.target.value })}
                          className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-sm font-bold focus:bg-white focus:border-blue-100 focus:outline-none transition-all"
                        >
                          <option value="acceptEdits">接受编辑</option>
                          <option value="requireApproval">需要批准</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                          最大轮次
                        </label>
                        <input
                          type="number"
                          value={configForm.max_turns || 100}
                          onChange={(e) => setConfigForm({ ...configForm, max_turns: parseInt(e.target.value) || 100 })}
                          min={1}
                          max={100}
                          className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-sm font-bold focus:bg-white focus:border-blue-100 focus:outline-none transition-all"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                          工作目录
                        </label>
                        <input
                          type="text"
                          value={configForm.work_dir || ''}
                          onChange={(e) => setConfigForm({ ...configForm, work_dir: e.target.value })}
                          placeholder="请输入工作目录路径"
                          className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-sm font-bold focus:bg-white focus:border-blue-100 focus:outline-none transition-all"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                          默认允许的工具
                        </label>
                        <ToolSelector
                          selectedTools={configForm.default_allowed_tools || []}
                          onChange={(tools) => setConfigForm({ ...configForm, default_allowed_tools: tools })}
                          category="all"
                          multiSelect={true}
                          className="max-h-96 overflow-y-auto"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                          自定义技能
                        </label>
                        {skills.length === 0 ? (
                          <p className="text-xs text-gray-500 py-2">加载技能列表中...</p>
                        ) : (
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto custom-scrollbar">
                            {skills.map(skill => {
                              // 使用技能名称而不是ID进行比较（数据库现在存储的是名称数组）
                              const isChecked = configForm.custom_skills?.includes(skill.name) || false;
                              return (
                                <div key={skill.id} className="flex items-center space-x-2 p-3 bg-[#F5F5F7] rounded-xl transition-all">
                                  <input
                                    type="checkbox"
                                    id={`skill-${skill.id}`}
                                    checked={isChecked}
                                    onChange={(e) => {
                                      e.stopPropagation();
                                      const current = configForm.custom_skills || [];
                                      if (e.target.checked) {
                                        setConfigForm({ ...configForm, custom_skills: [...current, skill.name] });
                                      } else {
                                        setConfigForm({ ...configForm, custom_skills: current.filter(name => name !== skill.name) });
                                      }
                                    }}
                                    className="rounded"
                                  />
                                  <label
                                    htmlFor={`skill-${skill.id}`}
                                    className="text-xs font-bold text-gray-700 cursor-pointer select-none flex-1"
                                  >
                                    {skill.name}
                                  </label>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>

                      <div>
                        <label className="block text-xs font-black text-gray-700 mb-2 uppercase tracking-wider">
                          自定义工具 (MCP Servers) <span className="text-gray-400 font-normal">(JSON 格式)</span>
                        </label>
                        <textarea
                          value={configForm.custom_tools ? JSON.stringify(configForm.custom_tools, null, 2) : ''}
                          onChange={(e) => {
                            try {
                              const value = e.target.value.trim();
                              if (value === '') {
                                setConfigForm({ ...configForm, custom_tools: undefined });
                              } else {
                                const parsed = JSON.parse(value);
                                setConfigForm({ ...configForm, custom_tools: parsed });
                              }
                            } catch (err) {
                              // JSON 解析错误，保持原值
                            }
                          }}
                          placeholder='{"server_name": {"url": "http://...", "api_key": "..."}}'
                          rows={6}
                          className="w-full px-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-xs font-mono focus:bg-white focus:border-blue-100 focus:outline-none transition-all resize-none"
                        />
                        <p className="text-[10px] text-gray-400 mt-1">输入有效的 JSON 格式，用于配置 MCP 服务器</p>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* 对话框底部 */}
            <div className="p-8 border-t border-gray-50 flex items-center justify-end space-x-3 flex-shrink-0">
              <button
                onClick={() => {
                  setShowUserSettingsDialog(false);
                  setSelectedUserId(null);
                  setUserConfig(null);
                  setUserSettingsError(null);
                }}
                className="px-6 py-3 text-sm font-black text-gray-600 hover:bg-gray-50 rounded-2xl transition-all"
                disabled={savingUserSettings}
              >
                取消
              </button>
              <button
                onClick={handleSaveUserSettings}
                disabled={savingUserSettings || loadingUserSettings}
                className="px-6 py-3 bg-[#1D1D1F] text-white rounded-2xl text-sm font-black hover:bg-black transition-all shadow-xl active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {savingUserSettings ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>保存中...</span>
                  </>
                ) : (
                  <>
                    <Settings size={16} />
                    <span>保存设置</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 用户日志查看对话框 */}
      {showUserLogsDialog && selectedUserForLogs && (
        <UserLogsDialog
          userId={selectedUserForLogs.id}
          username={selectedUserForLogs.username}
          onClose={() => {
            setShowUserLogsDialog(false);
            setSelectedUserForLogs(null);
          }}
        />
      )}

      {/* 用户插件管理对话框 */}
      {showUserPluginsDialog && selectedUserForPlugins && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-[40px] shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden animate-scale-in">
            {/* 对话框头部 */}
            <div className="p-8 border-b border-gray-50 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-black text-gray-900">插件管理</h2>
                <p className="text-gray-500 text-sm mt-1">
                  为用户 <span className="font-bold text-purple-600">{selectedUserForPlugins.username}</span> 配置可用的插件
                </p>
              </div>
              <button
                onClick={() => {
                  setShowUserPluginsDialog(false);
                  setSelectedUserForPlugins(null);
                  setUserPlugins({ bindings: [], available_packages: [] });
                }}
                className="p-2 text-gray-400 hover:text-gray-900 hover:bg-gray-50 rounded-xl transition-all"
              >
                <X size={20} />
              </button>
            </div>

            {/* 对话框内容 */}
            <div className="flex-1 overflow-y-auto p-8">
              {loadingUserPlugins ? (
                <div className="flex items-center justify-center py-12">
                  <div className="w-8 h-8 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* 已绑定插件 */}
                  <div>
                    <h3 className="text-sm font-black text-gray-700 mb-4 flex items-center space-x-2">
                      <Package size={16} className="text-purple-600" />
                      <span>已绑定插件 ({userPlugins.bindings.length})</span>
                    </h3>
                    {userPlugins.bindings.length === 0 ? (
                      <p className="text-gray-400 text-sm text-center py-4 bg-gray-50 rounded-xl">
                        暂未绑定任何插件
                      </p>
                    ) : (
                      <div className="grid grid-cols-2 gap-3">
                        {userPlugins.bindings.map((binding: any) => (
                          <div key={binding.id} className="p-4 bg-purple-50 border border-purple-100 rounded-xl">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                                  <Package size={18} className="text-purple-600" />
                                </div>
                                <div>
                                  <p className="text-sm font-black text-gray-900">{binding.package_display_name || binding.package_name}</p>
                                  <p className="text-xs text-gray-500">{binding.is_enabled ? '已启用' : '已禁用'}</p>
                                </div>
                              </div>
                              <button
                                onClick={() => handleUnbindPackage(binding.package_id)}
                                className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                                title="解绑"
                              >
                                <X size={16} />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* 可用插件 */}
                  <div>
                    <h3 className="text-sm font-black text-gray-700 mb-4 flex items-center space-x-2">
                      <Package size={16} className="text-gray-400" />
                      <span>可用插件 ({userPlugins.available_packages.length})</span>
                    </h3>
                    <div className="grid grid-cols-2 gap-3 max-h-60 overflow-y-auto">
                      {userPlugins.available_packages.map((pkg: any) => {
                        const isBound = userPlugins.bindings.some((b: any) => b.package_id === pkg.id);
                        return (
                          <div key={pkg.id} className="p-4 bg-gray-50 border border-gray-100 rounded-xl">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
                                  <Package size={18} className="text-gray-600" />
                                </div>
                                <div>
                                  <p className="text-sm font-black text-gray-900">{pkg.display_name || pkg.name}</p>
                                  <p className="text-xs text-gray-500">{pkg.category || '通用'}</p>
                                </div>
                              </div>
                              <button
                                onClick={() => handleBindPackage(pkg.id)}
                                disabled={isBound}
                                className={`px-3 py-1.5 rounded-lg text-xs font-black transition-all ${
                                  isBound
                                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                    : 'bg-purple-600 text-white hover:bg-purple-700'
                                }`}
                              >
                                {isBound ? '已绑定' : '绑定'}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 对话框底部 */}
            <div className="p-8 border-t border-gray-50 flex justify-end">
              <button
                onClick={() => {
                  setShowUserPluginsDialog(false);
                  setSelectedUserForPlugins(null);
                  setUserPlugins({ bindings: [], available_packages: [] });
                }}
                className="px-6 py-3 text-sm font-black text-gray-600 hover:bg-gray-50 rounded-2xl transition-all"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
