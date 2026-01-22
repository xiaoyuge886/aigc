import React, { useState, useEffect } from 'react';
import { ArrowRight, ArrowLeft, UserPlus, LogIn } from 'lucide-react';
import { authService, RegisterRequest } from '../services/authService';

interface LoginPageProps {
  onLoginSuccess: (user: { username: string; role: string }) => void;
  onBackToHome?: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess, onBackToHome }) => {
  // const [mode, setMode] = useState<'login' | 'register'>('login');
  const mode: 'login' | 'register' = 'login'; // 固定为登录模式

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');

  // 默认测试账号（开发环境）
  const defaultTestAccount = {
    username: 'admin',
    email: 'test@example.com',
    password: 'admin123'
  };
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    if (mode === 'login') {
      // 登录逻辑
      const result = await authService.login(username, password);

      if (result.success && result.data) {
        // 调试：输出登录返回的数据
        console.log('[LoginPage] Login response:', {
          username: result.data!.user.username,
          role_id: result.data!.user.role_id,
          role_id_type: typeof result.data!.user.role_id
        });
        
        // 判断角色：role_id === 1 或 role_id === '1' 都视为 Admin
        // 备用方案：如果 role_id 为 null 但用户名是 "admin"，也视为 Admin
        const roleId = result.data!.user.role_id;
        const username = result.data!.user.username;
        const isAdminRole = roleId === 1 || String(roleId) === '1' || 
                           (roleId == null && username?.toLowerCase() === 'admin');
        const role = isAdminRole ? 'ADMIN' : 'USER';
        
        console.log('[LoginPage] Role determined:', {
          roleId,
          role
        });
        
        onLoginSuccess({ username: result.data!.user.username, role });
      } else {
        setError(result.error || '登录失败');
        setIsLoading(false);
      }
    } else {
      // 注册逻辑
      const registerData: RegisterRequest = {
        username,
        email,
        password,
        full_name: fullName || undefined,
      };

      const result = await authService.register(registerData);

      if (result.success) {
        // 注册成功后自动登录
        const loginResult = await authService.login(username, password);
        if (loginResult.success && loginResult.data) {
          const role = loginResult.data!.user.role_id === 1 ? 'ADMIN' : 'USER';
          onLoginSuccess({ username: loginResult.data!.user.username, role });
        }
      } else {
        setError(result.error || '注册失败');
        setIsLoading(false);
      }
    }
  };

  // toggleMode 函数已禁用 - 不再需要切换登录/注册模式
  // const toggleMode = () => {
  //   setMode(mode === 'login' ? 'register' : 'login');
  //   setError('');
  //   setUsername('');
  //   setEmail('');
  //   setPassword('');
  //   setFullName('');
  // };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#FBFBFD] relative font-sans">

      {/* 背景装饰 */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] right-[10%] w-[600px] h-[600px] bg-blue-50/50 rounded-full blur-[120px] mix-blend-multiply" />
        <div className="absolute bottom-[-10%] left-[10%] w-[500px] h-[500px] bg-purple-50/40 rounded-full blur-[100px] mix-blend-multiply" />
      </div>

      {/* 返回按钮 */}
      {onBackToHome && (
        <button
          onClick={onBackToHome}
          className={`absolute top-10 left-10 flex items-center space-x-3 text-[11px] font-bold text-gray-500 hover:text-gray-900 transition-all duration-300 z-20 group ${mounted ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'}`}
        >
          <div className="w-10 h-10 rounded-xl bg-white border border-gray-200 flex items-center justify-center shadow-sm group-hover:shadow-md group-hover:border-gray-300 group-hover:scale-105 transition-all">
            <ArrowLeft size={16} className="group-hover:-translate-x-0.5 transition-transform text-gray-700" />
          </div>
          <span className="hidden sm:inline uppercase tracking-widest">返回首页</span>
        </button>
      )}

      {/* 主界面 */}
      <div className={`relative z-10 max-w-[440px] w-full px-6 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>

        {/* Logo 和标题 */}
        <div className="text-center mb-10">
          <div
            className="inline-flex items-center justify-center w-16 h-16 bg-[#1D1D1F] rounded-2xl text-white mb-6 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={onBackToHome}
          >
            <span className="text-2xl font-black italic tracking-tighter">X</span>
          </div>
          <h1 className="text-3xl font-black text-gray-900 mb-2 tracking-tight">
            {mode === 'login' ? '欢迎回来' : '创建账户'}
          </h1>
          <p className="text-gray-500 text-sm font-medium">
            {mode === 'login' ? '登录以访问您的智能工作区' : '注册以开始使用企业智能平台'}
          </p>
        </div>

        {/* 登录/注册卡片 */}
        <div className="bg-white border border-gray-200 p-8 md:p-10 rounded-3xl shadow-xl shadow-gray-200/50 space-y-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 用户名输入 */}
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">用户名</label>
              <input
                type="text"
                value={username}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUsername(e.target.value)}
                placeholder="请输入用户名"
                className="w-full px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#0066CC] focus:ring-2 focus:ring-[#0066CC]/20 transition-all text-sm font-medium"
                required
                minLength={3}
              />
            </div>

            {/* 邮箱输入 - 仅注册时显示 */}
            {mode === 'register' && (
              <div className="space-y-2">
                <label className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">邮箱地址</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#0066CC] focus:ring-2 focus:ring-[#0066CC]/20 transition-all text-sm font-medium"
                  required
                />
              </div>
            )}

            {/* 全名 - 仅注册时显示 */}
            {mode === 'register' && (
              <div className="space-y-2">
                <label className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">全名（可选）</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFullName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#0066CC] focus:ring-2 focus:ring-[#0066CC]/20 transition-all text-sm font-medium"
                />
              </div>
            )}

            {/* 密码输入 */}
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">密码</label>
              <input
                type="password"
                value={password}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-4 py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:border-[#0066CC] focus:ring-2 focus:ring-[#0066CC]/20 transition-all text-sm font-medium"
                required
                minLength={6}
              />
            </div>

            {error && (
              <div className="bg-red-50 py-3 rounded-xl border border-red-200 text-center">
                <span className="text-[11px] font-bold text-red-600 uppercase tracking-wider">
                  {error}
                </span>
              </div>
            )}

            {/* 提交按钮 */}
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full py-4 bg-[#1D1D1F] text-white font-bold rounded-xl hover:bg-black focus:outline-none focus:ring-4 focus:ring-gray-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden"
            >
              <div className="relative flex items-center justify-center space-x-2">
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span className="text-sm">{mode === 'login' ? '身份验证中...' : '创建账户中...'}</span>
                  </>
                ) : (
                  <>
                    {mode === 'login' ? <LogIn size={18} /> : <UserPlus size={18} />}
                    <span className="text-sm">{mode === 'login' ? '开始探索' : '立即注册'}</span>
                    <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </div>
            </button>
          </form>

          {/* 分隔线 */}
          <div className="my-6 flex items-center">
            <div className="flex-1 h-px bg-gray-200"></div>
            <span className="px-4 text-[11px] text-gray-500 uppercase tracking-wider">或</span>
            <div className="flex-1 h-px bg-gray-200"></div>
          </div>

          {/* 开发环境快速填充按钮 */}
          {import.meta.env.DEV && (
            <button
              type="button"
              onClick={() => {
                setUsername(defaultTestAccount.username);
                if (mode === 'register') {
                  setEmail(defaultTestAccount.email);
                }
                setPassword(defaultTestAccount.password);
              }}
              className="w-full py-3 bg-blue-50 border border-blue-200 rounded-xl text-blue-700 text-xs font-bold hover:bg-blue-100 transition-all flex items-center justify-center space-x-2"
            >
              <span>⚡ 快速填充测试账号</span>
            </button>
          )}

          {/* 切换登录/注册 */}
          {/* <button
            type="button"
            onClick={toggleMode}
            className="w-full py-3 bg-[#F5F5F7] border border-gray-200 rounded-xl text-gray-700 font-bold hover:bg-gray-100 hover:border-gray-300 transition-all flex items-center justify-center space-x-2 text-sm"
          >
            {mode === 'login' ? (
              <>
                <UserPlus size={16} className="text-gray-500" />
                <span>还没有账户？立即注册</span>
              </>
            ) : (
              <>
                <LogIn size={16} className="text-gray-500" />
                <span>已有账户？返回登录</span>
              </>
            )}
          </button> */}
        </div>

        {/* 底部信息 */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-400">
            © 2024 X Precision Intelligence. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};
