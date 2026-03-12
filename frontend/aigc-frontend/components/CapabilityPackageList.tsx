/**
 * Capability Package List - 能力包市场
 * Apple Design Style - 高级渐变配色方案
 */
import React, { useState, useEffect } from 'react';
import {
  Search, Users, Briefcase, Palette, Code2,
  Zap, Crown, Plus, Loader2, X,
  Puzzle, Boxes, BarChart3, FileText,
  Settings, Layers
} from 'lucide-react';
import { platformService, CapabilityPackage, UserCapabilityBinding } from '../services/platformService';
import { PackageDetailPage } from './PackageDetailPage';

// 高级渐变配色方案 - 每个分类独特的渐变
const CATEGORY_GRADIENTS: Record<string, {
  bg: string;
  gradient: string;
  iconBg: string;
  iconColor: string;
  accent: string;
  glow: string;
}> = {
  analysis: {
    bg: 'bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50',
    gradient: 'from-blue-500 via-indigo-500 to-violet-500',
    iconBg: 'bg-gradient-to-br from-blue-500 to-indigo-600',
    iconColor: 'text-white',
    accent: 'text-blue-600',
    glow: 'shadow-blue-500/20'
  },
  development: {
    bg: 'bg-gradient-to-br from-slate-50 via-emerald-50 to-teal-50',
    gradient: 'from-emerald-500 via-teal-500 to-cyan-500',
    iconBg: 'bg-gradient-to-br from-emerald-500 to-teal-600',
    iconColor: 'text-white',
    accent: 'text-emerald-600',
    glow: 'shadow-emerald-500/20'
  },
  document: {
    bg: 'bg-gradient-to-br from-slate-50 via-amber-50 to-orange-50',
    gradient: 'from-amber-500 via-orange-500 to-red-400',
    iconBg: 'bg-gradient-to-br from-amber-500 to-orange-600',
    iconColor: 'text-white',
    accent: 'text-amber-600',
    glow: 'shadow-amber-500/20'
  },
  creative: {
    bg: 'bg-gradient-to-br from-slate-50 via-pink-50 to-rose-50',
    gradient: 'from-pink-500 via-rose-500 to-red-500',
    iconBg: 'bg-gradient-to-br from-pink-500 to-rose-600',
    iconColor: 'text-white',
    accent: 'text-pink-600',
    glow: 'shadow-pink-500/20'
  },
  business: {
    bg: 'bg-gradient-to-br from-slate-50 via-violet-50 to-purple-50',
    gradient: 'from-violet-500 via-purple-500 to-fuchsia-500',
    iconBg: 'bg-gradient-to-br from-violet-500 to-purple-600',
    iconColor: 'text-white',
    accent: 'text-violet-600',
    glow: 'shadow-violet-500/20'
  },
  automation: {
    bg: 'bg-gradient-to-br from-slate-50 via-cyan-50 to-sky-50',
    gradient: 'from-cyan-500 via-sky-500 to-blue-500',
    iconBg: 'bg-gradient-to-br from-cyan-500 to-sky-600',
    iconColor: 'text-white',
    accent: 'text-cyan-600',
    glow: 'shadow-cyan-500/20'
  },
  default: {
    bg: 'bg-gradient-to-br from-slate-50 via-gray-50 to-zinc-50',
    gradient: 'from-slate-500 via-gray-500 to-zinc-500',
    iconBg: 'bg-gradient-to-br from-slate-500 to-gray-600',
    iconColor: 'text-white',
    accent: 'text-slate-600',
    glow: 'shadow-slate-500/20'
  }
};

// 分类图标映射
const CATEGORY_ICONS: Record<string, React.FC<{ size?: number; strokeWidth?: number; className?: string }>> = {
  analysis: BarChart3,
  development: Code2,
  document: FileText,
  creative: Palette,
  business: Briefcase,
  automation: Zap,
  default: Puzzle
};

// 分类定义
const CATEGORIES = [
  { id: 'all', name: '全部', icon: Layers },
  { id: 'analysis', name: '数据分析', icon: BarChart3 },
  { id: 'development', name: '开发工具', icon: Code2 },
  { id: 'document', name: '文档处理', icon: FileText },
  { id: 'creative', name: '创意设计', icon: Palette },
  { id: 'business', name: '商业应用', icon: Briefcase },
  { id: 'automation', name: '自动化', icon: Zap },
];

// 获取分类配色
const getCategoryStyle = (category?: string) => {
  return CATEGORY_GRADIENTS[category || 'default'] || CATEGORY_GRADIENTS.default;
};

// 获取分类图标
const getCategoryIcon = (category?: string) => {
  const IconComponent = CATEGORY_ICONS[category || 'default'] || CATEGORY_ICONS.default;
  return IconComponent;
};

interface PackageListProps {
  onPackageSelect?: (pkg: CapabilityPackage) => void;
}

export const CapabilityPackageList: React.FC<PackageListProps> = ({ onPackageSelect }) => {
  // 状态
  const [packages, setPackages] = useState<CapabilityPackage[]>([]);
  const [userBindings, setUserBindings] = useState<UserCapabilityBinding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [bindingInProgress, setBindingInProgress] = useState<number | null>(null);
  const [hoveredPackage, setHoveredPackage] = useState<number | null>(null);

  // 详情页面状态
  const [selectedPackageId, setSelectedPackageId] = useState<number | null>(null);

  // 加载数据
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [pkgsRes, myPkgsRes] = await Promise.all([
        platformService.listPackages(true),
        platformService.getMyPackages()
      ]);

      setPackages(pkgsRes);
      setUserBindings(myPkgsRes.bindings);
    } catch (err: any) {
      console.error('Failed to load packages:', err);
      setError(err.message || '加载能力包失败');
    } finally {
      setLoading(false);
    }
  };

  // 检查能力包是否已绑定
  const isPackageBound = (packageId: number): boolean => {
    return userBindings.some(b => b.package_id === packageId && b.is_enabled);
  };

  // 绑定能力包
  const handleBind = async (e: React.MouseEvent, packageId: number) => {
    e.stopPropagation();
    try {
      setBindingInProgress(packageId);
      await platformService.bindPackageToUser(0, packageId);
      const myPkgsRes = await platformService.getMyPackages();
      setUserBindings(myPkgsRes.bindings);
    } catch (err: any) {
      console.error('Failed to bind package:', err);
      alert(`绑定失败: ${err.message}`);
    } finally {
      setBindingInProgress(null);
    }
  };

  // 解绑能力包
  const handleUnbind = async (e: React.MouseEvent, packageId: number) => {
    e.stopPropagation();
    if (!confirm('确定要解绑此能力包吗？')) return;

    try {
      setBindingInProgress(packageId);
      await platformService.unbindPackageFromUser(0, packageId);
      const myPkgsRes = await platformService.getMyPackages();
      setUserBindings(myPkgsRes.bindings);
    } catch (err: any) {
      console.error('Failed to unbind package:', err);
      alert(`解绑失败: ${err.message}`);
    } finally {
      setBindingInProgress(null);
    }
  };

  // 过滤能力包
  const filteredPackages = packages.filter(pkg => {
    const matchCategory = activeCategory === 'all' || pkg.category === activeCategory;
    const matchSearch = !searchQuery ||
      pkg.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      pkg.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (pkg.description || '').toLowerCase().includes(searchQuery.toLowerCase());
    return matchCategory && matchSearch;
  });

  // 渲染加载状态
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-[#fbfbfd]">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-10 h-10 border-2 border-slate-800 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-medium text-slate-500">正在加载...</p>
        </div>
      </div>
    );
  }

  // 渲染错误状态
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-[#fbfbfd]">
        <X size={40} strokeWidth={1} className="text-slate-400" />
        <p className="mt-3 text-sm font-medium text-slate-800">{error}</p>
        <button
          onClick={loadData}
          className="mt-6 px-6 py-2 bg-slate-900 text-white rounded-full text-xs font-semibold hover:bg-slate-800 transition-colors"
        >
          重试
        </button>
      </div>
    );
  }

  // 如果选中了能力包，显示详情页面
  if (selectedPackageId !== null) {
    return (
      <PackageDetailPage
        packageId={selectedPackageId}
        onBack={() => setSelectedPackageId(null)}
      />
    );
  }

  return (
    <div className="flex h-full bg-[#fbfbfd]" style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", sans-serif' }}>
      {/* 左侧分类导航 */}
      <aside className="w-56 flex-shrink-0 overflow-y-auto bg-white/70 backdrop-blur-xl border-r border-black/[0.04]">
        <div className="p-5">
          <h2 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-4">
            分类
          </h2>
          <nav className="space-y-1">
            {CATEGORIES.map(cat => {
              const count = cat.id === 'all'
                ? packages.length
                : packages.filter(p => p.category === cat.id).length;
              const isActive = activeCategory === cat.id;
              const catStyle = getCategoryStyle(cat.id === 'all' ? 'default' : cat.id);

              return (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200 ${
                    isActive
                      ? 'bg-slate-900 text-white shadow-lg shadow-slate-900/20'
                      : 'text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <cat.icon
                    size={18}
                    strokeWidth={1.5}
                    className={isActive ? 'text-white' : 'text-slate-400'}
                  />
                  <span className="flex-1 text-[13px] font-medium">{cat.name}</span>
                  <span className={`text-xs font-medium ${isActive ? 'text-white/60' : 'text-slate-400'}`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* 统计卡片 */}
        <div className="mx-5 mt-4 p-5 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
          <div className="flex items-center gap-2 mb-3">
            <Boxes size={16} strokeWidth={1.5} className="text-slate-300" />
            <span className="text-[11px] font-medium text-slate-400">我的能力包</span>
          </div>
          <p className="text-3xl font-semibold tracking-tight">
            {userBindings.filter(b => b.is_enabled).length}
          </p>
          <p className="text-xs mt-1 text-slate-500">已绑定能力包</p>
        </div>
      </aside>

      {/* 右侧主内容区 */}
      <main className="flex-1 overflow-y-auto">
        {/* 头部搜索栏 */}
        <div className="sticky top-0 z-10 px-8 py-6 bg-[#fbfbfd]/80 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-[28px] font-semibold tracking-tight text-slate-900">
                能力包市场
              </h1>
              <p className="text-[14px] mt-1 text-slate-500">
                发现并使用强大的能力包来扩展 AI 助手
              </p>
            </div>

            {/* 搜索框 */}
            <div className="relative w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="搜索能力包..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-white rounded-xl text-[13px] border border-black/[0.06] text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-slate-300 focus:ring-4 focus:ring-slate-100 transition-all"
              />
            </div>
          </div>
        </div>

        {/* 能力包网格 */}
        <div className="px-8 pb-8">
          {filteredPackages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64">
              <Boxes size={48} strokeWidth={1} className="text-slate-300" />
              <p className="mt-4 text-sm font-medium text-slate-400">暂无能力包</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {filteredPackages.map(pkg => {
                const bound = isPackageBound(pkg.id);
                const isProcessing = bindingInProgress === pkg.id;
                const isHovered = hoveredPackage === pkg.id;
                const style = getCategoryStyle(pkg.category);
                const IconComponent = getCategoryIcon(pkg.category);

                return (
                  <div
                    key={pkg.id}
                    onClick={() => setSelectedPackageId(pkg.id)}
                    onMouseEnter={() => setHoveredPackage(pkg.id)}
                    onMouseLeave={() => setHoveredPackage(null)}
                    className={`rounded-2xl overflow-hidden cursor-pointer transition-all duration-300 bg-white ${
                      isHovered ? 'shadow-2xl shadow-slate-900/10 -translate-y-1' : 'shadow-sm shadow-slate-200/50'
                    }`}
                  >
                    {/* 卡片头部 - 渐变背景 */}
                    <div className={`h-28 ${style.bg} flex items-center justify-center relative overflow-hidden`}>
                      {/* 装饰性渐变圆 */}
                      <div className={`absolute -top-6 -right-6 w-24 h-24 rounded-full bg-gradient-to-br ${style.gradient} opacity-20 blur-2xl`} />
                      <div className={`absolute -bottom-8 -left-8 w-32 h-32 rounded-full bg-gradient-to-br ${style.gradient} opacity-10 blur-3xl`} />

                      {/* 图标 */}
                      <div
                        className={`w-14 h-14 rounded-xl ${style.iconBg} ${style.iconColor} flex items-center justify-center shadow-lg ${style.glow} transition-transform duration-300 ${
                          isHovered ? 'scale-110' : ''
                        }`}
                      >
                        <IconComponent size={26} strokeWidth={1.5} />
                      </div>

                      {/* 标签 */}
                      <div className="absolute top-3 left-3 flex items-center gap-1.5">
                        {pkg.is_official && (
                          <span className="px-2 py-0.5 bg-slate-900 text-white text-[10px] font-semibold rounded-full flex items-center gap-1">
                            <Crown size={10} strokeWidth={2} /> 官方
                          </span>
                        )}
                      </div>
                    </div>

                    {/* 卡片内容 */}
                    <div className="p-5">
                      {/* 标题 */}
                      <h3 className="font-semibold text-[15px] tracking-tight text-slate-900 mb-0.5 truncate">
                        {pkg.display_name}
                      </h3>
                      <p className="text-[11px] text-slate-400 mb-3">{pkg.name}</p>

                      {/* 描述 */}
                      <p className="text-[13px] leading-relaxed text-slate-500 mb-4 line-clamp-2">
                        {pkg.description || '暂无描述'}
                      </p>

                      {/* 统计信息 */}
                      <div className="flex items-center gap-4 text-[11px] text-slate-400 mb-5">
                        <span className="flex items-center gap-1">
                          <Users size={12} strokeWidth={1.5} />
                          {pkg.usage_count || 0} 次使用
                        </span>
                        <span className="flex items-center gap-1">
                          <Settings size={12} strokeWidth={1.5} />
                          {pkg.allowed_tools?.length || 0} 工具
                        </span>
                      </div>

                      {/* 操作按钮 */}
                      {bound ? (
                        <button
                          onClick={(e) => handleUnbind(e, pkg.id)}
                          disabled={isProcessing}
                          className="w-full py-2.5 rounded-xl text-[13px] font-medium flex items-center justify-center gap-2 bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
                        >
                          {isProcessing ? (
                            <Loader2 size={14} className="animate-spin" />
                          ) : (
                            <>
                              <span className="w-4 h-4 rounded-full bg-emerald-500 flex items-center justify-center">
                                <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                </svg>
                              </span>
                              已绑定
                            </>
                          )}
                        </button>
                      ) : (
                        <button
                          onClick={(e) => handleBind(e, pkg.id)}
                          disabled={isProcessing}
                          className={`w-full py-2.5 rounded-xl text-[13px] font-medium flex items-center justify-center gap-2 transition-all duration-200 ${
                            isHovered
                              ? 'bg-slate-900 text-white shadow-lg shadow-slate-900/20'
                              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                          }`}
                        >
                          {isProcessing ? (
                            <Loader2 size={14} className="animate-spin" />
                          ) : (
                            <>
                              <Plus size={14} strokeWidth={2} />
                              添加
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default CapabilityPackageList;