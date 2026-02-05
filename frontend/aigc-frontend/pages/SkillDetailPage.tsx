/**
 * Skill Detail Page
 * 技能包详情页面 - 参考 aiagentskills.net 设计风格
 */
import React, { useState, useEffect } from 'react';
import {
  Star, GitFork, Calendar, Download, Users, Code2, TrendingUp,
  ChevronRight, Terminal, Github, ArrowLeft, Crown, Shield,
  Megaphone, BarChart3, Sparkles, ExternalLink, Check, Bug, MessageSquare
} from 'lucide-react';
import { DebugModal } from '../components/DebugModal';

interface SkillDetailPageProps {
  skillId: number;
  onBack: () => void;
}

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
  license?: string;
  download_count: number;
  install_count: number;
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

  async getSkillPackageDetail(packageId: number) {
    const response = await fetch(`${this.baseUrl}/market/${packageId}`);
    if (!response.ok) throw new Error('Failed to fetch skill package detail');
    return response.json();
  }

  async installSkillPackage(packageId: number) {
    const token = localStorage.getItem('access_token');
    const url = `${this.baseUrl}/market/${packageId}/install`;

    console.log('[Skill Install] Debug Info:', {
      packageId,
      token: token ? `${token.substring(0, 30)}... (length: ${token.length})` : 'null',
      url,
      method: 'POST'
    });

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });

    console.log('[Skill Install] Response:', {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[Skill Install] Error response:', errorText);
      throw new Error(`Failed to install skill package (${response.status}): ${errorText}`);
    }
    return response.json();
  }

  async uninstallSkillPackage(packageId: number) {
    const token = localStorage.getItem('access_token');
    const url = `${this.baseUrl}/market/${packageId}/install`;

    console.log('[Skill Uninstall] Debug Info:', {
      packageId,
      token: token ? `${token.substring(0, 30)}... (length: ${token.length})` : 'null',
      url,
      method: 'DELETE'
    });

    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    console.log('[Skill Uninstall] Response:', {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[Skill Uninstall] Error response:', errorText);
      throw new Error(`Failed to uninstall skill package (${response.status}): ${errorText}`);
    }
    return response.json();
  }
}

export const SkillDetailPage: React.FC<SkillDetailPageProps> = ({ skillId, onBack }) => {
  const [skill, setSkill] = useState<SkillPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [installing, setInstalling] = useState(false);
  const [skillItems, setSkillItems] = useState<SkillItem[]>([]);

  // Debug state
  const [isDebugModalOpen, setIsDebugModalOpen] = useState(false);
  const [debuggingSkillItem, setDebuggingSkillItem] = useState<SkillItem | null>(null);

  // Chat state
  const [activeSkillForChat, setActiveSkillForChat] = useState<SkillItem | null>(null);
  const [showChat, setShowChat] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{ id: string; text: string; sender: 'user' | 'ai'; timestamp: Date }>>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  const service = new SkillMarketService();
  const chatEndRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSkillDetail(skillId);
  }, [skillId]);

  const loadSkillDetail = async (packageId: number) => {
    try {
      setLoading(true);
      const data = await service.getSkillPackageDetail(packageId);
      console.log('Skill detail received:', data);
      setSkill(data);
      // Load skill items
      setSkillItems(data.items || []);
    } catch (err) {
      console.error('Failed to load skill detail:', err);
      setSkill(null); // Set null on error
      setSkillItems([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInstall = async () => {
    if (!skill) return;
    try {
      setInstalling(true);
      await service.installSkillPackage(skill.id);
      // Reload skill detail
      await loadSkillDetail(skill.id);
    } catch (err) {
      alert(err instanceof Error ? err.message : '安装失败');
    } finally {
      setInstalling(false);
    }
  };

  const handleUninstall = async () => {
    if (!skill) return;
    try {
      setInstalling(true);
      await service.uninstallSkillPackage(skill.id);
      await loadSkillDetail(skill.id);
    } catch (err) {
      alert(err instanceof Error ? err.message : '卸载失败');
    } finally {
      setInstalling(false);
    }
  };

  const getCategoryIcon = (category?: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'marketing': <Megaphone size={32} strokeWidth={1.5} />,
      'data-analysis': <BarChart3 size={32} strokeWidth={1.5} />,
      'productivity': <Sparkles size={32} strokeWidth={1.5} />,
      'development': <Code2 size={32} strokeWidth={1.5} />,
    };
    return iconMap[category || ''] || <Terminal size={32} strokeWidth={1.5} />;
  };

  const getCategoryColor = (category?: string) => {
    const colorMap: Record<string, string> = {
      'marketing': 'from-amber-500/20 to-amber-600/5',
      'data-analysis': 'from-blue-500/20 to-blue-600/5',
      'productivity': 'from-purple-500/20 to-purple-600/5',
      'development': 'from-green-500/20 to-green-600/5',
    };
    return colorMap[category || ''] || 'from-gray-500/20 to-gray-600/5';
  };

  // 打开调试对话框
  const handleOpenDebug = (skillItem: SkillItem) => {
    setDebuggingSkillItem(skillItem);
    setIsDebugModalOpen(true);
  };

  // 关闭调试对话框
  const handleCloseDebug = () => {
    setIsDebugModalOpen(false);
    setDebuggingSkillItem(null);
  };

  // 开始对话
  const handleStartChat = (skillItem: SkillItem) => {
    setActiveSkillForChat(skillItem);
    setShowChat(true);
    setChatMessages([
      {
        id: 'm1',
        text: `🎯 已启用技能：**${skillItem.name}**\n\n技能说明：${skillItem.description || '暂无说明'}\n\n您可以开始与此技能进行对话了。`,
        sender: 'ai',
        timestamp: new Date()
      }
    ]);
    // Scroll to chat after a short delay
    setTimeout(() => {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  // 关闭对话
  const handleCloseChat = () => {
    setShowChat(false);
    setActiveSkillForChat(null);
    setChatMessages([]);
    setChatInput('');
  };

  // 发送消息
  const handleSendMessage = async () => {
    if (!chatInput.trim() || isChatLoading) return;

    const userMessage = chatInput.trim();
    setChatInput('');
    setIsChatLoading(true);

    // Add user message
    const userMsg = {
      id: `m${Date.now()}-user`,
      text: userMessage,
      sender: 'user' as const,
      timestamp: new Date()
    };
    setChatMessages(prev => [...prev, userMsg]);

    try {
      // Call agent API with skill
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/agent/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: userMessage,
          skill_content: activeSkillForChat?.skill_content,
          stream: false
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();

      // Add AI response
      const aiMsg = {
        id: `m${Date.now()}-ai`,
        text: data.response || data.answer || '收到您的消息',
        sender: 'ai' as const,
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, aiMsg]);

    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg = {
        id: `m${Date.now()}-error`,
        text: '抱歉，发生了错误。请稍后重试。',
        sender: 'ai' as const,
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          <p className="mt-4 text-gray-600 font-medium">加载技能详情中...</p>
        </div>
      </div>
    );
  }

  if (!skill) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 font-medium">技能不存在</p>
          <button
            onClick={onBack}
            className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700"
          >
            返回
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden bg-white">
      {/* Header - Simple */}
      <header className="border-b border-gray-100 flex-shrink-0">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 font-medium text-sm transition-colors"
          >
            <ArrowLeft size={18} />
            Back to skills
          </button>
        </div>
      </header>

      {/* Main Content - Scrollable */}
      <div className="flex-1 overflow-y-auto">
        <main className="max-w-6xl mx-auto px-6 py-8">
          {/* Hero Section */}
          <div className="mb-8">
            <div className="flex items-start gap-8">
              {/* Icon */}
              <div className={`flex-shrink-0 w-24 h-24 rounded-2xl flex items-center justify-center bg-gradient-to-br ${getCategoryColor(skill.category)} shadow-lg`}>
                <div className="text-5xl">
                  {getCategoryIcon(skill.category)}
                </div>
              </div>

              {/* Title & Description */}
              <div className="flex-1">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">
                      {skill.display_name || skill.name}
                    </h1>
                    <p className="text-lg text-gray-600 leading-relaxed">
                      {skill.description}
                    </p>
                  </div>

                  {/* Action Button */}
                  <div className="flex-shrink-0 ml-4">
                    {skill.is_installed ? (
                      <button
                        onClick={handleUninstall}
                        disabled={installing}
                        className="px-6 py-3 bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-300 rounded-xl font-semibold transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {installing ? '卸载中...' : '已安装'}
                      </button>
                    ) : (
                      <button
                        onClick={handleInstall}
                        disabled={installing}
                        className="px-6 py-3 bg-black hover:bg-gray-800 text-white rounded-xl font-semibold transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Download size={20} />
                        {installing ? '安装中...' : 'Use in your agent'}
                      </button>
                    )}
                  </div>
                </div>

                {/* Stats */}
                <div className="flex items-center gap-6 text-sm text-gray-500">
                  <div className="flex items-center gap-1">
                    <Star size={16} className="text-yellow-500 fill-yellow-500" />
                    <span>
                      {skill.rating_count > 0
                        ? `${Math.round(skill.rating_average * 10) / 10} (${skill.rating_count})`
                        : 'No ratings'
                      }
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Download size={16} />
                    <span>{skill.download_count.toLocaleString()} downloads</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Users size={16} />
                    <span>{skill.install_count.toLocaleString()} installs</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Tags */}
            {skill.tags && skill.tags.length > 0 && (
              <div className="flex items-center gap-2 mt-6 flex-wrap">
                {skill.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg font-medium text-sm"
                  >
                    {tag}
                  </span>
                ))}
                {skill.category && (
                  <span className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg font-medium text-sm capitalize">
                    {skill.category}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Overview Section */}
              <div className="prose prose-gray max-w-none">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Overview</h2>
                <div className="text-gray-700 leading-relaxed space-y-4">
                  {skill.long_description ? (
                    <p>{skill.long_description}</p>
                  ) : (
                    <p>{skill.description}</p>
                  )}
                </div>
              </div>

              {/* Installation Section */}
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Installation</h2>
                <div className="bg-gray-50 rounded-xl p-6">
                  <p className="text-sm text-gray-600 mb-3">Install this skill to your agent</p>
                  {!skill.is_installed && (
                    <button
                      onClick={handleInstall}
                      disabled={installing}
                      className="px-6 py-3 bg-black hover:bg-gray-800 text-white rounded-xl font-semibold transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Download size={20} />
                      {installing ? '安装中...' : 'Install Skill'}
                    </button>
                  )}
                  {skill.is_installed && (
                    <div className="flex items-center gap-2 text-green-600 font-medium">
                      <Check size={20} />
                      This skill is installed
                    </div>
                  )}
                </div>
              </div>

              {/* Skills Section */}
              {skillItems.length > 0 && (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">Skills</h2>
                  <div className="space-y-4">
                    {skillItems.map((skillItem) => (
                      <div key={skillItem.id} className="border border-gray-200 rounded-xl p-5 hover:shadow-md transition-all">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="text-lg font-semibold text-gray-900">{skillItem.name}</h3>
                              {skillItem.skill_type && (
                                <span className="text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded font-medium">
                                  {skillItem.skill_type}
                                </span>
                              )}
                            </div>
                            {skillItem.description && (
                              <p className="text-sm text-gray-600 mb-3">{skillItem.description}</p>
                            )}
                            <div className="flex items-center gap-6 text-xs text-gray-500">
                              <span>Uses: {skillItem.use_count || 0}</span>
                              <span className="text-green-600">Success: {skillItem.success_count || 0}</span>
                              <span className="text-red-600">Errors: {skillItem.error_count || 0}</span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleStartChat(skillItem)}
                              className="flex-shrink-0 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-all flex items-center gap-2 text-sm"
                            >
                              <MessageSquare size={16} />
                              开始对话
                            </button>
                            <button
                              onClick={() => handleOpenDebug(skillItem)}
                              className="flex-shrink-0 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-all flex items-center gap-2 text-sm"
                            >
                              <Bug size={16} />
                              调试
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right Column - Sidebar */}
            <div className="space-y-6">
              {/* Author Card */}
              <div className="border border-gray-200 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">About the author</h3>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                    <span className="text-gray-600 font-semibold">
                      {(skill.author_name || 'Unknown').charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">{skill.author_name || 'Unknown'}</div>
                    <div className="text-xs text-gray-500">Skill Developer</div>
                  </div>
                </div>
                {skill.repository_url && (
                  <a
                    href={skill.repository_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
                  >
                    View on GitHub
                    <ExternalLink size={14} />
                  </a>
                )}
              </div>

              {/* Version Card */}
              <div className="border border-gray-200 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">Version info</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Version</span>
                    <span className="font-medium text-gray-900">{skill.current_version || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status</span>
                    <span className={`font-medium ${skill.is_installed ? 'text-green-600' : 'text-gray-600'}`}>
                      {skill.is_installed ? 'Installed' : 'Not installed'}
                    </span>
                  </div>
                  {skill.license && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">License</span>
                      <span className="font-medium text-gray-900">{skill.license}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Official Badge */}
              {skill.is_official && (
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
                  <div className="flex items-center gap-3 mb-2">
                    <Shield size={20} className="text-blue-600" />
                    <h3 className="text-sm font-semibold text-blue-900">Official Skill</h3>
                  </div>
                  <p className="text-sm text-blue-800">
                    此技能由官方团队开发和维护
                  </p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Embedded Chat Interface */}
      {showChat && activeSkillForChat && (
        <div className="border-t border-gray-200 bg-white">
          <div className="max-w-6xl mx-auto">
            {/* Chat Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <MessageSquare size={20} className="text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">与 {activeSkillForChat.name} 对话</h3>
                  <p className="text-sm text-gray-500">使用此技能进行专业对话</p>
                </div>
              </div>
              <button
                onClick={handleCloseChat}
                className="px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors text-sm font-medium"
              >
                关闭对话
              </button>
            </div>

            {/* Chat Messages */}
            <div className="px-6 py-4 h-96 overflow-y-auto bg-gray-50">
              {chatMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`mb-4 ${msg.sender === 'user' ? 'flex justify-end' : 'flex justify-start'}`}
                >
                  <div
                    className={`max-w-2xl rounded-2xl px-4 py-3 ${
                      msg.sender === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-200 text-gray-900'
                    }`}
                  >
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                      {msg.text}
                    </div>
                  </div>
                </div>
              ))}
              {isChatLoading && (
                <div className="flex justify-start mb-4">
                  <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
                      <span className="text-sm text-gray-600">思考中...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Chat Input */}
            <div className="px-6 py-4 border-t border-gray-200 bg-white">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                  placeholder="输入您的问题..."
                  disabled={isChatLoading}
                  className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={isChatLoading || !chatInput.trim()}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white rounded-xl font-medium transition-colors disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <MessageSquare size={18} />
                  发送
                </button>
              </div>
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

export default SkillDetailPage;
