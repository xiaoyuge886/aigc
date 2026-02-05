/**
 * Skill Market - Apple Design Style
 * 参考 Apple 官网设计风格
 */
import React, { useState, useEffect } from 'react';
import {
  Search, Star, Users, Download, Eye, Code2, TrendingUp,
  Sparkles, ChevronRight, Grid3X3, Filter, BarChart3, Check,
  Crown, Shield, Zap, Megaphone, Briefcase, Palette, GraduationCap
} from 'lucide-react';

// Types
interface SkillPackage {
  id: number;
  name: string;
  identifier: string;
  display_name: string;
  description: string;
  category?: string;
  tags?: string[];
  current_version?: string;
  author_name?: string;
  download_count: number;
  install_count: number;
  rating_average: number;
  rating_count: number;
  is_featured: boolean;
  is_official: boolean;
  is_installed: boolean;
  has_update: boolean;
}

// API Service
class SkillMarketService {
  private baseUrl = '/api/v1/skills';

  async querySkillMarket(params: { search?: string; sort?: string; page?: number; page_size?: number }) {
    const queryParams = new URLSearchParams();
    if (params.search) queryParams.set('search', params.search);
    if (params.sort) queryParams.set('sort', params.sort);
    if (params.page) queryParams.set('page', params.page.toString());
    if (params.page_size) queryParams.set('page_size', params.page_size.toString());

    const response = await fetch(`${this.baseUrl}/market?${queryParams}`);
    if (!response.ok) throw new Error('Failed to fetch');
    return response.json();
  }

  async getSkillPackageDetail(packageId: number) {
    const response = await fetch(`${this.baseUrl}/market/${packageId}`);
    if (!response.ok) throw new Error('Failed to fetch detail');
    return response.json();
  }

  async installSkillPackage(packageId: number) {
    const token = localStorage.getItem('access_token');
    const url = `${this.baseUrl}/market/${packageId}/install`;

    console.log('[SkillMarketApple Install] Debug Info:', {
      packageId,
      token: token ? `${token.substring(0, 30)}... (length: ${token.length})` : 'null',
      url,
      method: 'POST'
    });

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    });

    console.log('[SkillMarketApple Install] Response:', {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[SkillMarketApple Install] Error response:', errorText);
      throw new Error(`Failed to install (${response.status}): ${errorText}`);
    }
    return response.json();
  }

  async uninstallSkillPackage(packageId: number) {
    const token = localStorage.getItem('access_token');
    const url = `${this.baseUrl}/market/${packageId}/install`;

    console.log('[SkillMarketApple Uninstall] Debug Info:', {
      packageId,
      token: token ? `${token.substring(0, 30)}... (length: ${token.length})` : 'null',
      url,
      method: 'DELETE'
    });

    const response = await fetch(url, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` },
    });

    console.log('[SkillMarketApple Uninstall] Response:', {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[SkillMarketApple Uninstall] Error response:', errorText);
      throw new Error(`Failed to uninstall (${response.status}): ${errorText}`);
    }
    return response.json();
  }
}

// Main Component
interface SkillMarketAppleProps {
  onViewSkillDetail?: (skillId: number) => void;
}

export const SkillMarketApple: React.FC<SkillMarketAppleProps> = ({ onViewSkillDetail }) => {
  const [activeCategory, setActiveCategory] = useState('全部');
  const [searchQuery, setSearchQuery] = useState('');
  const [skills, setSkills] = useState<SkillPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSkill, setSelectedSkill] = useState<SkillPackage | null>(null);
  const [sortBy, setSortBy] = useState('featured');

  const service = new SkillMarketService();

  useEffect(() => {
    loadSkills();
  }, [sortBy]);

  const loadSkills = async () => {
    try {
      setLoading(true);
      const data = await service.querySkillMarket({
        search: searchQuery || undefined,
        sort: sortBy,
        page: 1,
        page_size: 50,
      });
      console.log('Skills data received:', data);
      setSkills(data.items || []);
    } catch (err) {
      console.error('Failed to load skills:', err);
      setSkills([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    { name: '全部', icon: <Zap size={16} />, color: 'text-gray-900' },
    { name: 'marketing', label: '营销', icon: <Megaphone size={16} />, color: 'text-orange-600' },
    { name: 'data-analysis', label: '数据', icon: <BarChart3 size={16} />, color: 'text-blue-600' },
    { name: 'productivity', label: '效率', icon: <Sparkles size={16} />, color: 'text-purple-600' },
    { name: 'development', label: '开发', icon: <Code2 size={16} />, color: 'text-green-600' },
  ];

  const getCategoryInfo = (category: string) => {
    const found = categories.find(c => c.name === category);
    return found || categories[0];
  };

  const filteredSkills = skills.filter(skill => {
    const matchesCategory = activeCategory === '全部' || skill.category === activeCategory;
    const matchesSearch = !searchQuery ||
      skill.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      skill.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleInstall = async (skillId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await service.installSkillPackage(skillId);
      loadSkills();
    } catch (err) {
      alert('安装失败：' + (err instanceof Error ? err.message : '未知错误'));
    }
  };

  const handleUninstall = async (skillId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await service.uninstallSkillPackage(skillId);
      loadSkills();
    } catch (err) {
      alert('卸载失败：' + (err instanceof Error ? err.message : '未知错误'));
    }
  };

  const handleViewDetail = (skill: SkillPackage) => {
    if (onViewSkillDetail) {
      onViewSkillDetail(skill.id);
    } else {
      setSelectedSkill(skill);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Hero Section */}
        <section className="pt-20 pb-16 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-gray-100 rounded-full px-4 py-2 mb-6">
            <Sparkles size={14} className="text-blue-600" />
            <span className="text-sm font-semibold text-gray-900">技能市场</span>
          </div>

          <p className="text-2xl text-gray-600 font-normal mb-12 max-w-3xl mx-auto leading-relaxed">
            浏览、安装和管理 AI 技能插件，为你的智能体添加超能力
          </p>

          {/* Search Bar */}
          <div className="relative max-w-2xl mx-auto">
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="搜索技能..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                loadSkills();
              }}
              className="w-full pl-14 pr-6 py-4 bg-white border-0 shadow-sm rounded-2xl text-gray-900 text-lg placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
            />
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-8 border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-6">
          <div className="flex items-center gap-3 overflow-x-auto">
            {categories.map((cat) => {
              const info = getCategoryInfo(cat.name);
              const isActive = activeCategory === cat.name;
              return (
                <button
                  key={cat.name}
                  onClick={() => setActiveCategory(cat.name)}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {cat.icon}
                  {cat.label || cat.name}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* Skills Grid */}
      <section className="py-16 px-6">
        <div className="max-w-5xl mx-auto">
          {/* Skills List */}
          {loading ? (
            <div className="text-center py-20">
              <div className="inline-block animate-spin rounded-full h-10 w-10 border-2 border-gray-300 border-t-transparent"></div>
            </div>
          ) : filteredSkills.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-xl text-gray-500">没有找到匹配的技能</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredSkills.map((skill, index) => {
                const catInfo = getCategoryInfo(skill.category || '');
                return (
                  <div
                    key={skill.id}
                    onClick={() => handleViewDetail(skill)}
                    className="group relative bg-white rounded-2xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-[0_4px_24px_rgba(0,0,0,0.08)] transition-all duration-300 cursor-pointer overflow-hidden"
                  >
                    {/* Featured Badge */}
                    {skill.is_featured && (
                      <div className="absolute top-6 right-6 z-10">
                        <div className="flex items-center gap-1 bg-gray-900 text-white px-3 py-1 rounded-full text-xs font-medium">
                          <Crown size={12} />
                          推荐
                        </div>
                      </div>
                    )}

                    <div className="p-8">
                      {/* Icon & Category */}
                      <div className={`mb-6 inline-flex items-center justify-center w-14 h-14 rounded-2xl ${
                        skill.category === 'marketing' ? 'bg-orange-50' :
                        skill.category === 'data-analysis' ? 'bg-blue-50' :
                        skill.category === 'productivity' ? 'bg-purple-50' :
                        skill.category === 'development' ? 'bg-green-50' :
                        'bg-gray-50'
                      }`}>
                        <div className={catInfo.color}>
                          {catInfo.icon}
                        </div>
                      </div>

                      {/* Title */}
                      <h3 className="text-2xl font-semibold text-gray-900 mb-3">
                        {skill.display_name || skill.name}
                      </h3>

                      {/* Description */}
                      <p className="text-gray-600 text-base leading-relaxed mb-6 line-clamp-2">
                        {skill.description}
                      </p>

                      {/* Tags */}
                      {skill.tags && skill.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-6">
                          {skill.tags.slice(0, 3).map((tag) => (
                            <span key={tag} className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full font-medium">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Stats */}
                      <div className="flex items-center gap-6 text-sm text-gray-600 mb-6 pb-6 border-b border-gray-100">
                        <div className="flex items-center gap-1">
                          <Star size={16} className="text-yellow-500 fill-yellow-500" />
                          <span className="font-semibold">{skill.rating_average.toFixed(1)}</span>
                          <span className="text-gray-400">({skill.rating_count})</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Download size={16} />
                          <span className="font-medium">{skill.download_count.toLocaleString()}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Users size={16} />
                          <span className="font-medium">{skill.install_count.toLocaleString()}</span>
                        </div>
                      </div>

                      {/* Action */}
                      <div className="flex items-center gap-3">
                        {skill.is_installed ? (
                          <>
                            <button
                              onClick={(e) => handleUninstall(skill.id, e)}
                              className="flex-1 px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-xl font-semibold transition-colors"
                            >
                              卸载
                            </button>
                            {skill.has_update && (
                              <button
                                onClick={(e) => handleInstall(skill.id, e)}
                                className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition-colors"
                              >
                                更新
                              </button>
                            )}
                          </>
                        ) : (
                          <button
                            onClick={(e) => handleInstall(skill.id, e)}
                            className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition-all flex items-center justify-center gap-2 group"
                          >
                            <Download size={18} className="group-hover:scale-110 transition-transform" />
                            获取
                            <ChevronRight size={18} className="opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-6 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-5xl font-semibold text-gray-900 mb-2">{skills.length}</div>
              <div className="text-gray-600">可用技能</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-semibold text-gray-900 mb-2">
                {skills.reduce((sum, s) => sum + s.download_count, 0).toLocaleString()}
              </div>
              <div className="text-gray-600">总下载量</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-semibold text-gray-900 mb-2">
                {skills.reduce((sum, s) => sum + s.install_count, 0).toLocaleString()}
              </div>
              <div className="text-gray-600">总安装量</div>
            </div>
          </div>
        </div>
      </section>
      </div>

      {/* Detail Modal */}
      {selectedSkill && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-6 overflow-y-auto"
          onClick={() => setSelectedSkill(null)}
        >
          <div
            className="bg-white rounded-3xl shadow-2xl max-w-3xl w-full my-8 animate-[scale_0.95_opacity_0] animate-in"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="p-8 border-b border-gray-200 flex-shrink-0">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-16 h-16 rounded-2xl flex items-center justify-center ${
                      selectedSkill.category === 'marketing' ? 'bg-orange-50' :
                      selectedSkill.category === 'data-analysis' ? 'bg-blue-50' :
                      selectedSkill.category === 'productivity' ? 'bg-purple-50' :
                      selectedSkill.category === 'development' ? 'bg-green-50' :
                      'bg-gray-50'
                    }`}>
                      <div className={getCategoryInfo(selectedSkill.category || '').color}>
                        {getIconForCategory(selectedSkill.category || '')}
                      </div>
                    </div>
                    <div>
                      <h2 className="text-3xl font-semibold text-gray-900 mb-2">
                        {selectedSkill.display_name || selectedSkill.name}
                      </h2>
                      {selectedSkill.is_featured && (
                        <div className="flex items-center gap-1 text-amber-600 text-sm font-semibold">
                          <Crown size={16} fill="currentColor" />
                          推荐技能
                        </div>
                      )}
                    </div>
                  </div>
                  <p className="text-xl text-gray-600 leading-relaxed">
                    {selectedSkill.description}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedSkill(null)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors flex-shrink-0"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 6L6 18M18 18L6 6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-8">
              {/* Info Grid */}
              <div className="grid grid-cols-2 gap-6 mb-8">
                <div>
                  <div className="text-sm text-gray-600 mb-1">作者</div>
                  <div className="text-lg font-medium text-gray-900">{selectedSkill.author_name || '未知'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">版本</div>
                  <div className="text-lg font-medium text-gray-900">{selectedSkill.current_version || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">评分</div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      <Star size={20} className="text-yellow-500 fill-yellow-500" />
                      <span className="text-lg font-semibold">{selectedSkill.rating_average.toFixed(1)}</span>
                    </div>
                    <span className="text-gray-500">({selectedSkill.rating_count} 评价)</span>
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">统计</div>
                  <div className="text-lg font-medium text-gray-900">
                    {selectedSkill.download_count.toLocaleString()} 下载 · {selectedSkill.install_count.toLocaleString()} 安装
                  </div>
                </div>
              </div>

              {/* Tags */}
              {selectedSkill.tags && selectedSkill.tags.length > 0 && (
                <div className="mb-8">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">标签</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedSkill.tags.map((tag) => (
                      <span key={tag} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Action */}
              <div className="flex gap-4 pt-6 border-t border-gray-200">
                {selectedSkill.is_installed ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleUninstall(selectedSkill.id, e);
                      setSelectedSkill(null);
                    }}
                    className="flex-1 px-6 py-4 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-2xl font-semibold transition-colors"
                  >
                    卸载技能
                  </button>
                ) : (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleInstall(selectedSkill.id, e);
                      setSelectedSkill(null);
                    }}
                    className="flex-1 px-6 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-semibold transition-all flex items-center justify-center gap-2"
                  >
                    <Download size={20} />
                    安装此技能
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function
function getIconForCategory(category: string) {
  const icons: Record<string, React.ReactNode> = {
    'marketing': <Megaphone size={32} strokeWidth={1.5} />,
    'data-analysis': <BarChart3 size={32} strokeWidth={1.5} />,
    'productivity': <Sparkles size={32} strokeWidth={1.5} />,
    'development': <Code2 size={32} strokeWidth={1.5} />,
  };
  return icons[category] || <Zap size={32} strokeWidth={1.5} />;
}
