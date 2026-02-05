/**
 * Skill Market V2 - Improved Design
 * 结合现有前端风格的技能市场
 */
import React, { useState, useEffect } from 'react';
import {
  Search, Star, Users, Download, Eye, Code2, TrendingUp, Shield,
  Zap, Crown, Sparkles, ArrowUpRight, Play, Briefcase, Palette,
  GraduationCap, Megaphone, UserCircle, ChevronRight, Grid3X3, List,
  Filter, BarChart3, CheckCircle, Terminal, MessageSquare
} from 'lucide-react';

// Types
interface SkillPackage {
  id: number;
  name: string;
  identifier: string;
  display_name: string;
  description: string;
  long_description?: string;
  category?: string;
  tags?: string[];
  current_version?: string;
  author_name?: string;
  repository_url?: string;
  download_count: number;
  install_count: number;
  view_count: number;
  rating_average: number;
  rating_count: number;
  is_featured: boolean;
  is_official: boolean;
  is_active: boolean;
  is_installed: boolean;
  has_update: boolean;
  created_at: string;
}

// API Service
class SkillMarketService {
  private baseUrl = '/api/v1/skills';

  async querySkillMarket(params: {
    category?: string;
    search?: string;
    sort?: string;
    tags?: string[];
    page?: number;
    page_size?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params.category) queryParams.set('category', params.category);
    if (params.search) queryParams.set('search', params.search);
    if (params.sort) queryParams.set('sort', params.sort);
    if (params.page) queryParams.set('page', params.page.toString());
    if (params.page_size) queryParams.set('page_size', params.page_size.toString());

    const response = await fetch(`${this.baseUrl}/market?${queryParams}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch skill market: ${response.status}`);
    }
    return response.json();
  }

  async getSkillPackageDetail(packageId: number) {
    const response = await fetch(`${this.baseUrl}/market/${packageId}`);
    if (!response.ok) throw new Error('Failed to fetch skill package detail');
    return response.json();
  }

  async installSkillPackage(packageId: number) {
    const response = await fetch(`${this.baseUrl}/market/${packageId}/install`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });
    if (!response.ok) throw new Error('Failed to install skill package');
    return response.json();
  }

  async uninstallSkillPackage(packageId: number) {
    const response = await fetch(`${this.baseUrl}/market/${packageId}/install`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });
    if (!response.ok) throw new Error('Failed to uninstall skill package');
    return response.json();
  }
}

// Main Component
export const SkillMarketV2Styled: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState('全部');
  const [searchQuery, setSearchQuery] = useState('');
  const [isVisible, setIsVisible] = useState(false);
  const [skills, setSkills] = useState<SkillPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState('popular');

  const service = new SkillMarketService();

  useEffect(() => {
    setIsVisible(true);
    loadSkills();
  }, []);

  const loadSkills = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await service.querySkillMarket({
        search: searchQuery || undefined,
        sort: sortBy,
        page: 1,
        page_size: 50,
      });
      setSkills(data.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载技能失败');
      console.error('Failed to load skills:', err);
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    { name: '全部', icon: <Zap size={14} />, color: 'from-gray-500/20 to-gray-600/5', text: 'text-gray-600' },
    { name: 'marketing', icon: <Megaphone size={14} />, color: 'from-amber-500/20 to-amber-600/5', text: 'text-amber-600' },
    { name: 'data-analysis', icon: <BarChart3 size={14} />, color: 'from-blue-500/20 to-blue-600/5', text: 'text-blue-600' },
    { name: 'productivity', icon: <Sparkles size={14} />, color: 'from-purple-500/20 to-purple-600/5', text: 'text-purple-600' },
    { name: 'development', icon: <Code2 size={14} />, color: 'from-green-500/20 to-green-600/5', text: 'text-green-600' },
  ];

  const getCategoryInfo = (category: string) => {
    const info = categories.find(c => c.name === category);
    return info || categories[0];
  };

  const getIconForCategory = (category: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'marketing': <Megaphone size={32} strokeWidth={1.5} />,
      'data-analysis': <BarChart3 size={32} strokeWidth={1.5} />,
      'productivity': <Sparkles size={32} strokeWidth={1.5} />,
      'development': <Code2 size={32} strokeWidth={1.5} />,
    };
    return iconMap[category || ''] || <Zap size={32} strokeWidth={1.5} />;
  };

  const filteredSkills = skills.filter(skill => {
    const matchesCategory = activeCategory === '全部' || skill.category === activeCategory;
    const matchesSearch = !searchQuery ||
      skill.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleInstall = async (skillId: number) => {
    try {
      await service.installSkillPackage(skillId);
      // Reload skills
      loadSkills();
    } catch (err) {
      alert(err instanceof Error ? err.message : '安装失败');
    }
  };

  const handleUninstall = async (skillId: number) => {
    try {
      await service.uninstallSkillPackage(skillId);
      loadSkills();
    } catch (err) {
      alert(err instanceof Error ? err.message : '卸载失败');
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-white custom-scrollbar scroll-smooth selection:bg-blue-100 selection:text-blue-900">
      {/* Hero Section */}
      <section className="px-6 pt-16 pb-8">
        <div className={`max-w-7xl mx-auto transition-all duration-1000 transform ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
          <div className="relative rounded-[40px] overflow-hidden bg-[#1D1D1F] p-10 md:p-16 text-white group shadow-2xl">
            {/* Background elements */}
            <div className="absolute top-0 right-0 w-2/3 h-full bg-gradient-to-l from-blue-500/20 to-transparent pointer-events-none" />
            <div className="absolute -bottom-20 -right-20 w-80 h-80 bg-blue-500/10 blur-[100px] rounded-full group-hover:bg-blue-500/20 transition-all duration-700" />

            <div className="relative z-10 grid md:grid-cols-2 gap-12 items-center">
              <div className="space-y-8">
                <div className="flex items-center space-x-3 bg-white/10 w-fit px-4 py-1.5 rounded-full border border-white/10 backdrop-blur-md">
                   <Sparkles size={14} className="text-blue-400" />
                   <span className="text-[11px] font-black uppercase tracking-[0.2em] text-blue-100">在线技能市场</span>
                </div>
                <h2 className="text-4xl md:text-6xl font-black tracking-tight leading-[0.9] text-white">
                  发现并安装<br />
                  <span className="text-blue-400">AI 技能插件</span>
                </h2>
                <p className="text-lg text-gray-400 max-w-md font-medium leading-relaxed">
                  浏览、安装和管理 AI 技能。{skills.length} 个精选技能包，覆盖营销、数据分析、生产力等多个领域。
                </p>
                <div className="flex items-center space-x-4 pt-4">
                  <div className="flex items-center space-x-2">
                    <Download size={18} className="text-blue-400" />
                    <span className="text-white font-bold">{skills.reduce((sum, s) => sum + s.download_count, 0).toLocaleString()}</span>
                    <span className="text-gray-400 text-sm">下载</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Users size={18} className="text-green-400" />
                    <span className="text-white font-bold">{skills.reduce((sum, s) => sum + s.install_count, 0).toLocaleString()}</span>
                    <span className="text-gray-400 text-sm">安装</span>
                  </div>
                </div>
              </div>

              {/* Hero Image/Illustration */}
              <div className="hidden md:flex items-center justify-center">
                <div className="relative">
                  <div className="w-64 h-64 bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl flex items-center justify-center">
                    <div className="text-center space-y-4">
                      <Sparkles size={64} className="text-white/90" />
                      <div className="text-6xl font-black text-white">{skills.length}</div>
                      <div className="text-sm font-bold text-white/80">可用技能</div>
                    </div>
                  </div>
                  <div className="absolute -bottom-4 -right-4 w-32 h-32 bg-amber-500 rounded-2xl flex items-center justify-center shadow-xl">
                    <Crown size={40} className="text-amber-100" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Search and Filter Section */}
      <section className="px-6 pb-8">
        <div className="max-w-7xl mx-auto">
          {/* Search Bar */}
          <div className="relative mb-8">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="搜索技能..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                loadSkills();
              }}
              className="w-full pl-12 pr-4 py-4 rounded-2xl border-2 border-gray-200 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-gray-900 font-medium transition-all"
            />
          </div>

          {/* Categories */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex flex-wrap gap-3">
              {categories.map((cat) => {
                const catInfo = getCategoryInfo(cat.name);
                const isActive = activeCategory === cat.name;
                return (
                  <button
                    key={cat.name}
                    onClick={() => setActiveCategory(cat.name)}
                    className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-bold transition-all duration-300 ${
                      isActive
                        ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/30 scale-105'
                        : 'bg-white border-2 border-gray-200 text-gray-700 hover:border-blue-300 hover:shadow-md'
                    }`}
                  >
                    {cat.icon}
                    <span className="hidden md:inline">{cat.name === '全部' ? '全部' :
                      cat.name === 'marketing' ? '营销' :
                      cat.name === 'data-analysis' ? '数据分析' :
                      cat.name === 'productivity' ? '生产力' :
                      cat.name === 'development' ? '开发' : cat.name}</span>
                  </button>
                );
              })}
            </div>

            {/* Sort */}
            <div className="flex items-center gap-2">
              <Filter size={18} className="text-gray-500" />
              <select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value);
                  loadSkills();
                }}
                className="px-4 py-3 rounded-2xl border-2 border-gray-200 focus:border-blue-500 focus:outline-none font-bold text-gray-700 bg-white"
              >
                <option value="popular">热门</option>
                <option value="latest">最新</option>
                <option value="rated">评分</option>
                <option value="featured">精选</option>
              </select>
            </div>
          </div>

          {/* Skills Grid */}
          {loading ? (
            <div className="text-center py-20">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              <p className="mt-4 text-gray-600 font-medium">加载技能中...</p>
            </div>
          ) : error ? (
            <div className="bg-red-50 border-2 border-red-200 text-red-700 p-6 rounded-2xl font-bold text-center">
              {error}
            </div>
          ) : filteredSkills.length === 0 ? (
            <div className="text-center py-20">
              <Zap size={48} className="mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 font-medium text-lg">没有找到匹配的技能</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredSkills.map((skill, index) => {
                const catInfo = getCategoryInfo(skill.category || '');
                return (
                  <div
                    key={skill.id}
                    className={`group relative overflow-hidden rounded-3xl border-2 transition-all duration-300 hover:shadow-2xl ${
                      skill.is_featured
                        ? 'border-amber-300 bg-gradient-to-br from-amber-50 to-orange-50'
                        : 'border-gray-200 bg-white hover:border-blue-300'
                    }`}
                    style={{
                      animation: `fadeInUp 0.5s ease-out ${index * 0.1}s both`
                    }}
                  >
                    {/* Featured Badge */}
                    {skill.is_featured && (
                      <div className="absolute top-4 right-4 z-10">
                        <div className="bg-amber-500 text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1 shadow-lg">
                          <Crown size={12} />
                          精选
                        </div>
                      </div>
                    )}

                    <div className="p-6 space-y-4">
                      {/* Icon */}
                      <div className={`w-16 h-16 rounded-2xl flex items-center justify-center bg-gradient-to-br ${catInfo.color} shadow-lg`}>
                        <div className={catInfo.text}>
                          {getIconForCategory(skill.category || '')}
                        </div>
                      </div>

                      {/* Title & Description */}
                      <div>
                        <h3 className="text-xl font-black text-gray-900 mb-2 flex items-center gap-2">
                          {skill.display_name || skill.name}
                          {skill.is_official && <Shield size={18} className="text-blue-500" />}
                        </h3>
                        <p className="text-gray-600 text-sm line-clamp-2 leading-relaxed">
                          {skill.description}
                        </p>
                      </div>

                      {/* Tags */}
                      {skill.tags && skill.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {skill.tags.slice(0, 3).map((tag) => (
                            <span key={tag} className="px-3 py-1 bg-blue-50 text-blue-700 text-xs rounded-full font-bold">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Stats */}
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <Star size={16} className="text-amber-500 fill-amber-500" />
                          <span className="font-bold text-gray-900">{skill.rating_average.toFixed(1)}</span>
                          <span className="text-gray-500">({skill.rating_count})</span>
                        </div>
                        <div className="flex items-center gap-1 text-gray-600">
                          <Download size={16} />
                          <span className="font-medium">{skill.download_count}</span>
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-2 pt-2">
                        {skill.is_installed ? (
                          <>
                            <button
                              onClick={() => handleUninstall(skill.id)}
                              className="flex-1 px-4 py-3 bg-red-500 hover:bg-red-600 text-white rounded-2xl font-bold transition-all shadow-lg hover:shadow-xl active:scale-95"
                            >
                              卸载
                            </button>
                            {skill.has_update && (
                              <button
                                onClick={() => handleInstall(skill.id)}
                                className="px-4 py-3 bg-green-500 hover:bg-green-600 text-white rounded-2xl font-bold transition-all shadow-lg hover:shadow-xl active:scale-95"
                              >
                                更新
                              </button>
                            )}
                          </>
                        ) : (
                          <button
                            onClick={() => handleInstall(skill.id)}
                            className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white rounded-2xl font-bold transition-all shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
                          >
                            <Download size={18} />
                            安装
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Hover Effect Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* Stats Section */}
      <section className="px-6 pb-12">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl p-6 text-white shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-sm font-bold mb-1">总技能数</p>
                  <p className="text-4xl font-black">{skills.length}</p>
                </div>
                <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur">
                  <Sparkles size={28} className="text-white" />
                </div>
              </div>
            </div>
            <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-3xl p-6 text-white shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-sm font-bold mb-1">总下载量</p>
                  <p className="text-4xl font-black">{skills.reduce((sum, s) => sum + s.download_count, 0).toLocaleString()}</p>
                </div>
                <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur">
                  <Download size={28} className="text-white" />
                </div>
              </div>
            </div>
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-3xl p-6 text-white shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-sm font-bold mb-1">活跃用户</p>
                  <p className="text-4xl font-black">{skills.reduce((sum, s) => sum + s.install_count, 0).toLocaleString()}</p>
                </div>
                <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur">
                  <Users size={28} className="text-white" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 bg-gray-50 border-t border-gray-200">
        <div className="max-w-7xl mx-auto text-center text-gray-600">
          <p className="font-medium">技能市场 V2 - 让 AI 更强大</p>
          <p className="text-sm mt-2 text-gray-500">发现、安装和管理 AI 技能插件</p>
        </div>
      </footer>
    </div>
  );
};

// Add fadeInUp animation
const style = document.createElement('style');
style.textContent = `
  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(30px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;
document.head.appendChild(style);
