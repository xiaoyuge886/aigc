import React, { useState, useEffect } from 'react';
import {
  Search, Star, Download, Users, Eye, Code, Play, Debug, Settings,
  Package, TrendingUp, Shield, Clock, CheckCircle, XCircle, AlertCircle,
  Filter, ChevronDown, ChevronUp, Heart, Share2, ExternalLink, BookOpen,
  Terminal, MessageSquare, BarChart3, Tag, Grid3X3, List, Plus, Upload,
  Zap, Crown, Sparkles, Flame, Bug
} from 'lucide-react';
import { DebugModal } from './DebugModal';

// Types (保持不变)
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
  is_installed: boolean;
  has_update: boolean;
  created_at: string;
}

interface SkillItem {
  id: number;
  name: string;
  display_name?: string;
  description?: string;
  skill_content: string;
  skill_type: string;
  use_count: number;
  success_count: number;
  error_count: number;
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
      const text = await response.text();
      console.error('API Error:', text);
      throw new Error(`Failed to fetch skill market: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  }

  async getSkillPackageDetail(packageId: number) {
    const response = await fetch(`${this.baseUrl}/market/${packageId}`);
    if (!response.ok) throw new Error('Failed to fetch skill package detail');
    return response.json();
  }

  async installSkillPackage(packageId: number, versionId?: number) {
    const queryParams = versionId ? `?version_id=${versionId}` : '';
    const response = await fetch(`${this.baseUrl}/market/${packageId}/install${queryParams}`, {
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

  async getSkillItemByName(skillName: string) {
    const response = await fetch(`${this.baseUrl}/items/name/${encodeURIComponent(skillName)}`);
    if (!response.ok) throw new Error('Failed to fetch skill item');
    return response.json();
  }
}

// Main Component
export const SkillMarketV2: React.FC = () => {
  const [view, setView] = useState<'market' | 'installed' | 'detail'>('market');
  const [marketView, setMarketView] = useState<'grid' | 'list'>('grid');

  // Market state
  const [skills, setSkills] = useState<SkillPackage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState('popular');

  // Detail view
  const [selectedSkill, setSelectedSkill] = useState<SkillPackage | null>(null);
  const [skillItems, setSkillItems] = useState<SkillItem[]>([]);

  // Debug state
  const [isDebugModalOpen, setIsDebugModalOpen] = useState(false);
  const [debuggingSkillItem, setDebuggingSkillItem] = useState<SkillItem | null>(null);

  const service = new SkillMarketService();

  const categories = [
    { id: 'all', name: '全部', icon: <Grid3X3 size={16} /> },
    { id: 'marketing', name: '营销', icon: <TrendingUp size={16} /> },
    { id: 'data-analysis', name: '数据分析', icon: <BarChart3 size={16} /> },
    { id: 'productivity', name: '生产力', icon: <Zap size={16} /> },
    { id: 'development', name: '开发', icon: <Code size={16} /> },
  ];

  useEffect(() => {
    loadMarket();
  }, [selectedCategory, sortBy]);

  const loadMarket = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await service.querySkillMarket({
        category: selectedCategory !== 'all' ? selectedCategory : undefined,
        search: searchQuery || undefined,
        sort: sortBy,
        page: 1,
        page_size: 20,
      });
      setSkills(data.packages || data);
    } catch (err) {
      console.error('Failed to load market:', err);
      setError('加载失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = async (skill: SkillPackage) => {
    setSelectedSkill(skill);
    setView('detail');

    // Load skill items from API
    try {
      const detail = await service.getSkillPackageDetail(skill.id);
      setSkillItems(detail.items || []);
    } catch (err) {
      console.error('Failed to load skill items:', err);
      setSkillItems([]);
    }
  };

  const handleInstall = async (skillId: number) => {
    try {
      await service.installSkillPackage(skillId);
      alert('安装成功！');
      await loadMarket();
    } catch (err) {
      console.error('Install failed:', err);
      alert('安装失败：' + (err as Error).message);
    }
  };

  const handleUninstall = async (skillId: number) => {
    try {
      await service.uninstallSkillPackage(skillId);
      alert('卸载成功！');
      await loadMarket();
    } catch (err) {
      console.error('Uninstall failed:', err);
      alert('卸载失败：' + (err as Error).message);
    }
  };

  // 打开调试对话框
  const handleOpenDebug = async (skillItem: SkillItem) => {
    setDebuggingSkillItem(skillItem);
    setIsDebugModalOpen(true);
  };

  // 关闭调试对话框
  const handleCloseDebug = () => {
    setIsDebugModalOpen(false);
    setDebuggingSkillItem(null);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-6 pb-0 flex-shrink-0">
        <h1 className="text-3xl font-bold mb-2">技能市场</h1>
        <p className="text-gray-600">浏览、安装和调试 AI 技能</p>
      </div>

      {/* Market View */}
      {view === 'market' && (
        <div className="flex-1 overflow-y-auto p-6">
          {/* Search and Filters */}
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <div className="flex gap-4 mb-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="搜索技能..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg"
                />
              </div>
              <div className="flex gap-2">
                {categories.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.id)}
                    className={`px-4 py-2 rounded-lg ${
                      selectedCategory === cat.id ? 'bg-blue-500 text-white' : 'bg-gray-100'
                    }`}
                  >
                    {cat.icon}
                    {cat.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Skill Grid */}
            {loading ? (
              <div className="text-center py-12">加载中...</div>
            ) : error ? (
              <div className="text-center py-12 text-red-600">{error}</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {skills.map((skill) => (
                  <div key={skill.id} className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition cursor-pointer">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900">{skill.display_name}</h3>
                        <p className="text-sm text-gray-600">{skill.description}</p>
                      </div>
                      {skill.is_official && (
                        <div className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-medium">
                          官方
                        </div>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-2 mb-4">
                      {skill.tags?.slice(0, 3).map((tag) => (
                        <span key={tag} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">
                          {tag}
                        </span>
                      ))}
                    </div>

                    <div className="flex items-center justify-between text-sm text-gray-600 mb-4">
                      <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                          <Download className="w-4 h-4" />
                          {skill.download_count}
                        </span>
                        <span className="flex items-center gap-1">
                          <Star className="w-4 h-4 fill="currentColor" />
                          {skill.rating_average.toFixed(1)}
                        </span>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewDetail(skill)}
                        className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                      >
                        查看详情
                      </button>
                      {skill.is_installed ? (
                        <button
                          onClick={() => handleUninstall(skill.id)}
                          className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
                        >
                          卸载
                        </button>
                      ) : (
                        <button
                          onClick={() => handleInstall(skill.id)}
                          className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                        >
                          安装
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
        </div>
      )}

      {/* Detail View */}
      {view === 'detail' && selectedSkill && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {/* Header卡片 */}
            <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
              <button
                onClick={() => setView('market')}
                className="text-blue-600 hover:text-blue-700 mb-4 flex items-center gap-1"
              >
                ← 返回市场
              </button>
              <h2 className="text-3xl font-bold mb-2">{selectedSkill.display_name}</h2>
              <p className="text-gray-600">{selectedSkill.description}</p>
            </div>

            {/* 技能列表卡片 */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-xl font-semibold mb-6">包含的技能</h3>
              {skillItems.length === 0 ? (
                <div className="text-center py-16 text-gray-500">
                  暂无技能项
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {skillItems.map((skillItem) => (
                    <div key={skillItem.id} className="border border-gray-200 rounded-xl p-6 hover:shadow-lg hover:border-blue-300 transition-all">
                      <div className="flex flex-col gap-4">
                        {/* 顶部：名称和类型标签 */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <h4 className="text-lg font-semibold text-gray-900">{skillItem.name}</h4>
                            {skillItem.skill_type && (
                              <span className="text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded font-medium">
                                {skillItem.skill_type}
                              </span>
                            )}
                          </div>
                          <button
                            onClick={() => handleOpenDebug(skillItem)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 text-sm font-medium whitespace-nowrap"
                          >
                            <Bug className="w-4 h-4" />
                            调试
                          </button>
                        </div>

                        {/* 描述 */}
                        {skillItem.description && (
                          <p className="text-sm text-gray-600 leading-relaxed">{skillItem.description}</p>
                        )}

                        {/* 统计信息 */}
                        <div className="flex items-center gap-6 text-xs text-gray-500 pt-2 border-t border-gray-100">
                          <div className="flex items-center gap-1">
                            <span className="font-semibold">使用:</span>
                            <span>{skillItem.use_count || 0}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="font-semibold text-green-600">成功:</span>
                            <span>{skillItem.success_count || 0}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="font-semibold text-red-600">失败:</span>
                            <span>{skillItem.error_count || 0}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Debug Modal */}
      <DebugModal
        isOpen={isDebugModalOpen}
        onClose={handleCloseDebug}
        skillId={debuggingSkillItem?.id || 0}
        skillName={debuggingSkillItem?.name || ''}
        skillContent={debuggingSkillItem?.skill_content || ''}
      />
    </div>
  );
};
