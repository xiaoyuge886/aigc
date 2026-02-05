/**
 * Nexus Skill Market
 * Apple Design Style Skill Market with Full Debug Sandbox
 * Migrated from Desktop/aigc project
 */
import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Search, Star, Users, Briefcase, Palette, Code2, GraduationCap,
  Zap, Crown, ChevronRight, Plus, Loader2, X, Terminal,
  Bug, Send, Video, Paperclip, FileIcon, Activity, Globe,
  FileText, Share2, Maximize2, Camera, RefreshCw, ThumbsUp, ThumbsDown,
  Folder, File, ChevronDown, Play, Sparkles, Database, Settings,
  GitBranch, Code, Layout, BarChart, Copy, Check, Filter, Layers,
  Puzzle, Cpu, Boxes, Megaphone, BarChart3, TrendingUp, Download, Trash2, Upload
} from 'lucide-react';
import { streamDebugSkill } from '../services/agentService';
import { GitHubSkillsPage } from './GitHubSkillsPanel';
import { AddSkillModal } from './AddSkillModal';
import { UploadSkillZip } from './UploadSkillZip';

// --- 简单的 Markdown 转 HTML 函数 ---
const simpleMarkdown = (text: string): string => {
  if (!text) return '';
  let html = text;

  // 转义HTML特殊字符（除了我们允许的标签）
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // 代码块 ```code```
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="bg-gray-100 p-2 rounded text-sm">$2</code></pre>');

  // 行内代码 `code`
  html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1.5 py-0.5 rounded text-sm text-pink-600">$1</code>');

  // 标题 # ###
  html = html.replace(/^### (.+)$/gm, '<h3 class="text-lg font-bold mt-3 mb-1">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mt-4 mb-2">$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mt-4 mb-2">$1</h1>');

  // 加粗 **text**
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // 斜体 *text*
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // 链接 [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" class="text-blue-600 underline" target="_blank" rel="noopener noreferrer">$1</a>');

  // 无序列表 - item
  html = html.replace(/^[\s]*[-*]\s+(.+)$/gm, '<li class="ml-4 list-disc">$1</li>');

  // 有序列表 1. item
  html = html.replace(/^[\s]*(\d+)\.\s+(.+)$/gm, '<li class="ml-4 list-decimal">$2</li>');

  // 换行转换为 <br>（但不在标签内）
  html = html.replace(/\n\n/g, '</p><p class="my-2">');
  html = html.replace(/\n/g, '<br />');

  // 段落包裹
  html = `<p class="my-1">${html}</p>`;

  // 清理多余的段落标签
  html = html.replace(/<p><\/p>/g, '');
  html = html.replace(/<p>(<h[1-6]>)/g, '$1');
  html = html.replace(/(<\/h[1-6]>)<\/p>/g, '$1');
  html = html.replace(/<p>(<pre>)/g, '$1');
  html = html.replace(/(<\/pre>)<\/p>/g, '$1');

  return html;
};

// --- 类型定义 ---
interface SkillNode {
  id: string;
  name: string;
  type: 'folder' | 'file';
  content?: string;
  isOpen?: boolean;
  children?: SkillNode[];
  icon?: React.ReactNode;
}

// 区分核心 AI 逻辑与外部插件工具
type SkillType = 'Core' | 'Plugin';

interface Skill {
  id: string;
  title: string;
  description: string;
  category: string;
  type: SkillType;
  icon: string;
  systemInstruction: string;
  rating: number;
  users: string;
  tree: SkillNode[];
  status?: 'draft' | 'testing' | 'published' | 'official' | 'archived';
  source?: 'github' | 'conversation' | 'upload' | 'official';
}

interface StreamEvent {
  type: string;
  text?: string;
  data?: any;
  content_block?: { type: string; text: string };
  tool_use?: { id: string; name: string; input: any };
  error?: string;
  result?: {
    session_id: string;
    total_cost_usd: number;
    duration_ms: number;
    num_turns: number;
  };
  session_id?: string;
}

// --- 模拟图标映射 ---
const IconMap: Record<string, any> = {
  Briefcase: <Briefcase size={20} />,
  Palette: <Palette size={20} />,
  Code2: <Code2 size={20} />,
  Zap: <Zap size={20} />,
  Users: <Users size={20} />,
  Sparkles: <Sparkles size={20} />,
  Puzzle: <Puzzle size={20} />,
  Megaphone: <Megaphone size={20} />,
  BarChart3: <BarChart3 size={20} />,
  TrendingUp: <TrendingUp size={20} />
};

export const SkillMarketNexus: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState('全部');
  const [activeType, setActiveType] = useState<'All' | 'Core' | 'Plugin'>('All');
  const [searchQuery, setSearchQuery] = useState('');

  // 初始技能数据（从数据库加载）
  const [skills, setSkills] = useState<Skill[]>([]);

  // GitHub 拉取状态
  const [showGitHubPanel, setShowGitHubPanel] = useState(false);

  // 添加技能模态框状态
  const [showAddSkillModal, setShowAddSkillModal] = useState(false);
  const [uploadZipMode, setUploadZipMode] = useState(false);

  // 处理添加技能模式选择
  const handleSelectAddSkillMode = (mode: 'github' | 'upload' | 'create') => {
    setShowAddSkillModal(false);
    if (mode === 'create') {
      // 对话创建：使用调试页面，创建一个空技能模板
      const createModeSkill: Skill = {
        id: 'create',
        title: '创建技能',
        description: '使用 skill-creator 技能生成新技能',
        category: 'creation',
        type: 'Core',
        icon: 'Sparkles',
        systemInstruction: '',
        rating: 0,
        users: '0',
        tree: [],
        status: 'draft',
        source: 'conversation'
      };
      setDebugSkill(createModeSkill);
      setDebugMessages([{
        id: 'init',
        text: '技能创建模式已就绪。请描述您想要创建的技能类型，我将使用 skill-creator 技能为您生成。',
        html: simpleMarkdown('技能创建模式已就绪。请描述您想要创建的技能类型，我将使用 skill-creator 技能为您生成。'),
        sender: 'ai'
      }]);
    } else if (mode === 'github') {
      setShowGitHubPanel(true);
    } else if (mode === 'upload') {
      setUploadZipMode(true);
    }
  };

  // 调试沙盒状态
  const [debugSkill, setDebugSkill] = useState<Skill | null>(null);
  const [debugMessages, setDebugMessages] = useState<any[]>([]);
  const [debugInput, setDebugInput] = useState('');
  const [debugLoading, setDebugLoading] = useState(false);
  const [debugFullText, setDebugFullText] = useState('');
  const [debugWsOpen, setDebugWsOpen] = useState(true);
  const [activeFile, setActiveFile] = useState<SkillNode | null>(null);
  const [copied, setCopied] = useState(false);

  // 流式输出相关状态
  const [streamCurrentText, setStreamCurrentText] = useState('');
  const [streamToolCalls, setStreamToolCalls] = useState<any[]>([]);
  const [streamFinalResult, setStreamFinalResult] = useState<any>(null);
  const [streamSessionId, setStreamSessionId] = useState<string>('');

  // 分割线调节相关状态
  const [leftPanelWidth, setLeftPanelWidth] = useState(60); // 左侧面板宽度百分比
  const [isDragging, setIsDragging] = useState(false); // 用于视觉反馈
  const isDraggingRef = useRef(false); // 用于实际拖拽逻辑
  const dragStartX = useRef(0);
  const dragStartWidth = useRef(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const debugEndRef = useRef<HTMLDivElement>(null);

  // 处理分割线拖拽
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    isDraggingRef.current = true;
    setIsDragging(true); // 更新 state 以触发视觉反馈
    dragStartX.current = e.clientX;
    dragStartWidth.current = leftPanelWidth;

    // 禁用文本选择
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';

    // 添加全局事件监听
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDraggingRef.current || !containerRef.current) return;

    const containerWidth = containerRef.current.offsetWidth;
    const deltaX = e.clientX - dragStartX.current;
    const deltaPercent = (deltaX / containerWidth) * 100;
    const newWidth = Math.max(30, Math.min(80, dragStartWidth.current + deltaPercent)); // 限制在 30%-80% 之间

    setLeftPanelWidth(newWidth);
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
    setIsDragging(false); // 更新 state 以触发视觉反馈

    // 恢复文本选择
    document.body.style.userSelect = '';
    document.body.style.cursor = '';

    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };

  // 从数据库加载技能
  useEffect(() => {
    loadSkillsFromDB();
  }, []);

  const loadSkillsFromDB = async () => {
    try {
      // 获取当前用户token以确定是否已登录
      const token = localStorage.getItem('access_token');

      const response = await fetch('/api/v1/skills/market?include_testing=true', {
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
      });
      if (response.ok) {
        const data = await response.json();
        console.log('API Response:', data); // Debug log

        // 转换为 Nexus 格式
        const nexusSkills: Skill[] = (data.skills || []).map((pkg: any) => ({
          id: pkg.id.toString(),
          title: pkg.name,
          description: pkg.description || '',
          category: '未分类',
          type: 'Core' as SkillType,
          icon: 'Zap',
          systemInstruction: pkg.description || '',
          rating: 0,
          users: `${pkg.usage_count || 0}`,
          status: pkg.status,
          tree: generateSkillTree(pkg)
        }));
        console.log('Loaded skills:', nexusSkills); // Debug log
        setSkills(nexusSkills);
      }
    } catch (error) {
      console.error('Failed to load skills:', error);
    }
  };

  // 从后端API加载技能文件树
  const loadSkillFiles = async (skillId: string, skill: Skill): Promise<SkillNode[]> => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/skills/${parseInt(skillId)}/files`, {
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Skill files loaded:', data);

        // 将后端返回的文件树转换为 SkillNode[] 格式
        const convertToSkillNodes = (node: any): SkillNode => {
          const skillNode: SkillNode = {
            id: node.path || node.name,
            name: node.name,
            type: node.type,
            content: node.content || ''
          };

          if (node.children && node.children.length > 0) {
            skillNode.children = node.children.map(convertToSkillNodes);
            skillNode.isOpen = node.name === skill.title; // 默认打开根目录
          }

          return skillNode;
        };

        return [convertToSkillNodes(data.file_tree)];
      } else {
        console.error('Failed to load skill files:', response.status);
        // 如果加载失败，返回模拟数据
        return skill.tree;
      }
    } catch (error) {
      console.error('Error loading skill files:', error);
      // 如果出错，返回模拟数据
      return skill.tree;
    }
  };

  // 删除技能
  const handleDeleteSkill = async (skillId: string, skillName: string) => {
    if (!confirm(`确定要删除技能 "${skillName}" 吗？此操作不可恢复。`)) {
      return;
    }

    try {
      // 将 skillId 从字符串转换为整数（后端期望整数）
      const response = await fetch(`/api/v1/skills/${parseInt(skillId)}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        // 从列表中移除该技能
        setSkills(prevSkills => prevSkills.filter(s => s.id !== skillId));
        console.log(`✓ 已删除技能: ${skillName}`);
      } else if (response.status === 403) {
        alert('您没有权限删除此技能（只能删除自己创建的技能）');
      } else if (response.status === 404) {
        alert('技能不存在');
      } else {
        const error = await response.json();
        alert(`删除失败: ${error.detail || '未知错误'}`);
      }
    } catch (error) {
      console.error('Failed to delete skill:', error);
      alert('删除失败，请稍后重试');
    }
  };

  const getIconForCategory = (category?: string) => {
    const iconMap: Record<string, string> = {
      'marketing': 'Megaphone',
      'data-analysis': 'BarChart3',
      'productivity': 'Sparkles',
      'development': 'Code2',
      'business': 'Briefcase',
      'creative': 'Palette'
    };
    return iconMap[category || ''] || 'Zap';
  };

  const generateSkillTree = (pkg: any): SkillNode[] => {
    return [
      {
        id: 'root',
        name: pkg.name,
        type: 'folder',
        isOpen: true,
        children: [
          {
            id: 'manifest',
            name: 'manifest.json',
            type: 'file',
            content: JSON.stringify({
              name: pkg.name,
              display_name: pkg.display_name,
              version: pkg.current_version,
              category: pkg.category,
              author: pkg.author_name
            }, null, 2)
          },
          {
            id: 'readme',
            name: 'README.md',
            type: 'file',
            content: `# ${pkg.display_name}\n\n${pkg.description}\n\n## Installation\n\nVersion: ${pkg.current_version}\nCategory: ${pkg.category}`
          }
        ]
      }
    ];
  };

  // 技能列表过滤逻辑
  const filteredSkills = useMemo(() => {
    return skills.filter(s => {
      const matchCat = activeCategory === '全部' || s.category === activeCategory;
      const matchType = activeType === 'All' || s.type === activeType;
      const matchSearch = s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          s.description.toLowerCase().includes(searchQuery.toLowerCase());
      return matchCat && matchType && matchSearch;
    });
  }, [skills, activeCategory, activeType, searchQuery]);

  useEffect(() => {
    debugEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [debugMessages, debugFullText, streamCurrentText]);

  const handleSaveCreatedSkill = async () => {
    // 从 AI 的最后回复中提取 SKILL.md 内容
    const lastAiMessage = debugMessages
      .filter(m => m.sender === 'ai')
      .pop();

    if (!lastAiMessage) {
      alert('还没有与 AI 对话生成技能内容，请先进行对话');
      return;
    }

    // 构建 SKILL.md 内容
    const skillContent = lastAiMessage.text;

    // 从内容中提取技能名称（第一行或从 YAML frontmatter）
    let skillName = 'my-skill';
    const nameMatch = skillContent.match(/^name:\s*(.+)$/m);
    if (nameMatch) {
      skillName = nameMatch[1].trim().toLowerCase().replace(/\s+/g, '-');
    }

    // 简单描述
    const descriptionMatch = skillContent.match(/^description:\s*(.+)$/m);
    const description = descriptionMatch ? descriptionMatch[1].trim() : '';

    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams({
        skill_name: skillName,
        description: description,
        skill_content: skillContent,
      });

      const response = await fetch(`/api/v1/skills/create-from-conversation?${params}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      if (response.ok) {
        const data = await response.json();
        alert(`技能 "${skillName}" 已保存到调试目录！`);
        // 关闭调试页面
        setDebugSkill(null);
        setDebugMessages([]);
        setStreamSessionId('');  // 清空 session_id
        // 刷新技能列表
        loadSkillsFromDB();
      } else {
        const error = await response.json();
        alert(`保存失败：${error.detail || '未知错误'}`);
      }
    } catch (error: any) {
      console.error('保存技能失败:', error);
      alert(`保存失败：${error.message}`);
    }
  };

  const handleDebugSend = async () => {
    if (!debugInput.trim() || debugLoading) return;
    const txt = debugInput;
    setDebugInput('');
    setDebugLoading(true);
    setDebugFullText('');
    setStreamCurrentText('');
    setStreamToolCalls([]);
    setStreamFinalResult(null);
    setDebugMessages(p => [...p, { id: Date.now().toString(), text: txt, sender: 'user' }]);

    try {
      let collectedResultInfo: any = null;
      let accumulatedText = '';  // 本地变量累积完整文本

      // 创建模式：使用 skill-creator 技能
      const skillsToLoad = debugSkill?.id === 'create' ? ['skill-creator'] : undefined;

      // 使用 streamDebugSkill 函数（复用 ChatInterface 的逻辑）
      // 传递 streamSessionId 以支持多轮对话
      for await (const chunk of streamDebugSkill(
        debugSkill?.title || 'unknown',
        debugSkill?.systemInstruction || '',
        txt,
        skillsToLoad,  // 创建模式下传入 ['skill-creator']
        streamSessionId  // 传递 session_id，保持对话上下文
      )) {
        if (chunk.error) {
          console.error('❌ 调试错误:', chunk.error);
          setDebugFullText(`错误: ${chunk.error}`);
          break;
        }

        // 保存 session_id
        if (chunk.sessionId) {
          setStreamSessionId(chunk.sessionId);
        }

        // 收集 ResultMessage 信息
        if (chunk.resultInfo) {
          collectedResultInfo = chunk.resultInfo;
          setStreamFinalResult(collectedResultInfo);
        }

        // 处理文本增量
        if (chunk.text) {
          accumulatedText += chunk.text;  // 累积到本地变量
          setStreamCurrentText(accumulatedText);  // 更新状态用于实时显示
        }

        // 处理工具调用
        if (chunk.toolCalls && chunk.toolCalls.length > 0) {
          setStreamToolCalls(prev => [...prev, ...chunk.toolCalls]);
        }

        // 处理工具开始
        if (chunk.toolStart) {
          setStreamToolCalls(prev => [...prev, chunk.toolStart]);
        }

        // 检查是否完成
        if (chunk.isComplete) {
          break;
        }
      }

      // 流式完成后，添加最终消息到对话列表（带Markdown转换）
      if (accumulatedText) {
        setDebugMessages(p => [...p, {
          id: Date.now().toString(),
          text: accumulatedText,
          html: simpleMarkdown(accumulatedText),
          sender: 'ai'
        }]);
        // 清空实时显示文本
        setStreamCurrentText('');
      }
    } catch (e) {
      console.error('Chat error:', e);
      setDebugFullText('抱歉，发生了错误。请稍后重试。');
    } finally {
      setDebugLoading(false);
    }
  };

  const renderTree = (nodes: SkillNode[], level = 0) => {
    if (!nodes || nodes.length === 0) {
      return (
        <div className="text-center py-8">
          <File size={28} className="mb-2 opacity-40 mx-auto text-gray-300" />
          <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 px-4">
            {debugSkill?.id === 'create' ? '创建技能后文件将显示在这里' : '暂无文件'}
          </p>
        </div>
      );
    }

    return nodes.map(node => (
      <div key={node.id} className="select-none">
        <div
          onClick={() => {
            if (node.type === 'folder') {
              node.isOpen = !node.isOpen;
            } else {
              setActiveFile(node);
            }
            // 触发重新渲染以显示选中状态
            setDebugSkill({ ...debugSkill });
          }}
          className={`flex items-center py-2 px-3 cursor-pointer hover:bg-black/5 rounded-xl transition-all ${activeFile?.id === node.id ? 'bg-blue-50 text-blue-600' : 'text-gray-600'}`}
          style={{ paddingLeft: `${level * 16 + 8}px` }}
        >
          {node.type === 'folder' ? (
            <ChevronDown size={14} className={`mr-1.5 transition-transform ${node.isOpen ? '' : '-rotate-90'}`} />
          ) : (
            <div className="w-3 mr-2" />
          )}
          {node.type === 'folder' ? <Folder size={14} className="mr-2 text-blue-400 fill-blue-400/5" /> : <File size={14} className="mr-2 text-gray-400" />}
          <span className="text-[12px] font-bold truncate tracking-tight">{node.name}</span>
        </div>
        {node.type === 'folder' && node.isOpen && node.children && (
          <div className="animate-apple-fade">{renderTree(node.children, level + 1)}</div>
        )}
      </div>
    ));
  };

  const categories = ['全部', 'marketing', 'data-analysis', 'productivity', 'development'];

  return (
    <div className="flex-1 flex bg-[#FBFBFD] overflow-hidden relative font-sans">

      {/* GitHub 拉取页面 - 全屏模式 */}
      {showGitHubPanel && (
        <GitHubSkillsPage
          onClose={() => {
            setShowGitHubPanel(false);
            loadSkillsFromDB(); // 重新加载技能列表
          }}
          onSkillInstalled={() => {
            loadSkillsFromDB();
          }}
        />
      )}

      {/* 调试模式激活时，只显示调试界面 */}
      {debugSkill ? (
        <div className="flex-1 flex flex-col bg-white">
          {/* 调试界面 Header */}
          <header className="h-16 px-6 border-b border-black/[0.04] flex items-center justify-between bg-white/95 backdrop-blur-3xl shrink-0">
             <div className="flex items-center space-x-4">
                <div className="w-10 h-10 bg-apple-gray text-white rounded-xl flex items-center justify-center shadow-lg"><Bug size={20}/></div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[14px] font-black text-apple-gray uppercase tracking-tight">Sandbox: {debugSkill.title}</span>
                    <span className="bg-amber-100 text-amber-600 text-[8px] font-black uppercase px-2 py-0.5 rounded-full tracking-[0.2em]">Live Sim</span>
                  </div>
                </div>
             </div>
             <div className="flex items-center space-x-3">
                {/* 保存按钮：仅在创建模式下显示 */}
                {debugSkill?.id === 'create' && (
                  <button
                    onClick={handleSaveCreatedSkill}
                    disabled={debugLoading}
                    className="px-4 py-2 bg-green-600 text-white text-xs font-black uppercase tracking-wider rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center space-x-2"
                  >
                    <Check size={14} />
                    <span>保存技能</span>
                  </button>
                )}
                <button onClick={() => setDebugWsOpen(!debugWsOpen)} className={`p-2.5 rounded-full transition-all ${debugWsOpen ? 'bg-blue-50 text-blue-600' : 'text-gray-300 hover:text-black'}`}><Maximize2 size={18}/></button>
                <div className="w-px h-6 bg-gray-100 mx-2" />
                <button onClick={() => {setDebugSkill(null); setDebugMessages([]); setStreamSessionId('');}} className="p-2.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-all"><X size={24}/></button>
             </div>
          </header>

          <div className="flex-1 flex overflow-hidden" ref={containerRef}>
             {/* 左侧：对话显示区域 + 对话框 */}
             <div className="flex flex-col min-w-0" style={{ width: `${leftPanelWidth}%` }}>
                {/* 对话显示区域：历史消息 + 实时输出 + 统计 */}
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar bg-[#FBFBFD]">
                   <div className="max-w-3xl mx-auto space-y-6">

                     {/* 历史消息 */}
                     {debugMessages.map(m => (
                       <div key={m.id} className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'} animate-apple-slide`}>
                          <div className={`px-5 py-3.5 text-[14px] font-semibold leading-relaxed shadow-sm max-w-[80%] ${
                            m.sender === 'user' ? 'bg-blue-600 text-white rounded-[20px] rounded-tr-sm' : 'bg-white border border-black/[0.04] text-apple-gray rounded-[20px] rounded-tl-sm'
                          }`}>
                            {m.sender === 'user' ? (
                              m.text
                            ) : (
                              <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: m.html || m.text }} />
                            )}
                          </div>
                          <span className="text-[8px] font-black uppercase text-gray-300 mt-1.5 tracking-[0.2em]">{m.sender === 'user' ? 'Test Identity' : 'Kernel Output'}</span>
                       </div>
                     ))}

                     {/* 实时输出 */}
                     {debugLoading && streamCurrentText && (
                       <div className="flex flex-col items-start animate-apple-slide">
                          <div className="px-5 py-3.5 text-[14px] font-semibold leading-relaxed shadow-sm bg-white border border-black/[0.04] text-apple-gray rounded-[20px] rounded-tl-sm max-w-[80%]">
                            <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: simpleMarkdown(streamCurrentText) }} />
                            <span className="inline-block w-2 h-4 bg-gray-400 ml-1 animate-pulse" />
                          </div>
                          <span className="text-[8px] font-black uppercase text-gray-300 mt-1.5 tracking-[0.2em]">Kernel Output (Streaming)</span>
                       </div>
                     )}

                     {debugLoading && !streamCurrentText && (
                       <div className="animate-pulse text-[12px] font-bold text-gray-300 px-4">正在同步多维信号...</div>
                     )}

                     {/* 本轮统计 */}
                     {streamFinalResult && (
                       <div className="mt-6 bg-[#f5f5f5] rounded-lg overflow-hidden">
                         {/* 标题栏 */}
                         <div className="px-4 py-3 flex items-center justify-between">
                           <span className="text-[14px] font-bold text-black">统计信息</span>
                         </div>

                         {/* 表格区域 */}
                         <div className="px-4 pb-4">
                           {/* 第一行 */}
                           <div className="grid grid-cols-4 gap-4 mb-3">
                             <div className="flex justify-between items-center">
                               <span className="text-[12px] text-[#666]">类型</span>
                               <span className="text-[14px] font-bold text-black">
                                 {streamFinalResult.subtype || 'success'}
                               </span>
                             </div>
                             <div className="flex justify-between items-center">
                               <span className="text-[12px] text-[#666]">总耗时</span>
                               <span className="text-[14px] font-bold text-black">
                                 {((streamFinalResult.duration_ms || 0) / 1000).toFixed(2)}秒
                               </span>
                             </div>
                             <div className="flex justify-between items-center">
                               <span className="text-[12px] text-[#666]">API耗时</span>
                               <span className="text-[14px] font-bold text-black">
                                 {((streamFinalResult.duration_api_ms || 0) / 1000).toFixed(2)}秒
                               </span>
                             </div>
                             <div className="flex justify-between items-center">
                               <span className="text-[12px] text-[#666]">轮次</span>
                               <span className="text-[14px] font-bold text-black">
                                 {streamFinalResult.num_turns || 0}
                               </span>
                             </div>
                           </div>

                           {/* 第二行 */}
                           <div className="grid grid-cols-4 gap-4">
                             <div className="flex justify-between items-center">
                               <span className="text-[12px] text-[#666]">费用</span>
                               <span className="text-[14px] font-bold text-black">
                                 ${streamFinalResult.total_cost_usd?.toFixed(6) || '0.000000'}
                               </span>
                             </div>
                             <div className="flex justify-between items-center">
                               <span className="text-[12px] text-[#666]">状态</span>
                               <span className={`text-[14px] font-bold ${streamFinalResult.is_error ? 'text-[#ff4d4f]' : 'text-black'}`}>
                                 {streamFinalResult.is_error ? '错误' : '成功'}
                               </span>
                             </div>
                             <div className="flex justify-between items-center">
                               {/* 空白 */}
                             </div>
                             <div className="flex justify-between items-center">
                               {/* 空白 */}
                             </div>
                           </div>
                         </div>

                         {/* 使用情况卡片 */}
                         <div className="px-4 pb-4">
                           <div className="bg-white rounded-lg p-4">
                             <div className="grid grid-cols-3 gap-6">
                               <div>
                                 <div className="text-[12px] text-[#666] mb-1">输入TOKEN</div>
                                 <div className="text-[14px] font-bold text-black">
                                   {streamFinalResult.usage?.input_tokens?.toLocaleString() || '0'}
                                 </div>
                               </div>
                               <div>
                                 <div className="text-[12px] text-[#666] mb-1">输出TOKEN</div>
                                 <div className="text-[14px] font-bold text-black">
                                   {streamFinalResult.usage?.output_tokens?.toLocaleString() || '0'}
                                 </div>
                               </div>
                               <div>
                                 <div className="text-[12px] text-[#666] mb-1">缓存读取</div>
                                 <div className="text-[14px] font-bold text-black">
                                   {streamFinalResult.usage?.cache_read_tokens?.toLocaleString() || '0'}
                                 </div>
                               </div>
                             </div>
                           </div>
                         </div>

                         {/* 底部信息栏 */}
                         <div className="px-4 pb-4">
                           <div className="flex gap-6 text-[12px]">
                             <div>
                               <span className="text-[#999]">层级：</span>
                               <span className="text-[#999]">{streamFinalResult.model || 'standard'}</span>
                             </div>
                             <div>
                               <span className="text-[#999]">工具：</span>
                               <span className="text-[#999]">无</span>
                             </div>
                           </div>
                         </div>
                       </div>
                     )}
                   </div>
                   <div ref={debugEndRef} />
                </div>

                {/* 对话框 */}
                <div className="p-6 border-t border-black/[0.04] bg-white">
                   <div className="flex items-center bg-[#F2F2F7] rounded-[24px] p-2 border border-black/[0.01]">
                      <input
                        value={debugInput} onChange={e => setDebugInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleDebugSend()}
                        placeholder="在此输入调试指令..." className="flex-1 bg-transparent border-none text-[14px] px-5 outline-none font-semibold text-apple-gray"
                      />
                      <button onClick={handleDebugSend} disabled={debugLoading} className="w-10 h-10 bg-black text-white rounded-2xl flex items-center justify-center shadow-xl active:scale-95 disabled:opacity-20 transition-all">
                         {debugLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                      </button>
                   </div>
                </div>
             </div>

             {/* 可拖拽的分隔条 */}
             <div
               onMouseDown={handleMouseDown}
               className={`w-px hover:bg-blue-400 bg-black/[0.04] cursor-col-resize transition-all relative flex-shrink-0 ${
                 isDragging ? 'bg-blue-400' : ''
               }`}
               style={{ cursor: 'col-resize' }}
             />

             {/* 右侧：工作区（文件树 + 文件预览）*/}
             <div className="bg-white flex flex-col border-l border-black/[0.04] flex-shrink-0" style={{ width: `${100 - leftPanelWidth}%` }}>
                <header className="h-12 px-4 border-b border-black/[0.03] flex items-center bg-[#FBFBFD]">
                  <div className="flex items-center space-x-2">
                    <GitBranch size={14} className="text-blue-500" />
                    <span className="text-[11px] font-black uppercase tracking-widest text-gray-500">Skill Explorer</span>
                  </div>
                </header>

                {/* 工作区主体：左右结构 */}
                <div className="flex-1 flex overflow-hidden">
                  {/* 左侧：文件树 */}
                  <div className="w-[30%] border-r border-black/[0.03] overflow-y-auto p-3 custom-scrollbar bg-[#FBFBFD]">
                    {renderTree(debugSkill.tree)}
                  </div>

                  {/* 右侧：文件内容预览 */}
                  <div className="flex-1 bg-white overflow-y-auto custom-scrollbar">
                    {activeFile && (
                      <div className="h-full flex flex-col">
                        {/* 文件标题栏 */}
                        <div className="px-4 py-3 border-b border-black/[0.03] bg-[#F8F9FA]">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <div className="p-1 bg-blue-50 rounded text-blue-500"><Code size={14} /></div>
                              <h3 className="text-[11px] font-black text-apple-gray tracking-tight uppercase">{activeFile.name}</h3>
                            </div>
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(activeFile.content || '');
                                setCopied(true);
                                setTimeout(() => setCopied(false), 2000);
                              }}
                              className="p-1.5 text-gray-300 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                              title="复制全部"
                            >
                              {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14}/>}
                            </button>
                          </div>
                        </div>

                        {/* 文件内容 */}
                        <div className="flex-1 p-4 overflow-auto bg-[#FAFAFA]">
                          <div className="bg-[#1E1E1E] rounded-xl p-4 shadow-inner font-mono text-[11px] text-gray-300 leading-relaxed border border-black overflow-auto min-h-[200px]">
                            <pre className="whitespace-pre-wrap">{activeFile.content || '// Source protected'}</pre>
                          </div>
                        </div>
                      </div>
                    )}
                    {!activeFile && (
                      <div className="h-full flex flex-col items-center justify-center text-gray-400">
                        <File size={32} className="mb-2 opacity-40" />
                        <p className="text-[10px] font-black uppercase tracking-widest text-center px-4">选择文件以查看内容</p>
                      </div>
                    )}
                  </div>
                </div>
             </div>
          </div>
        </div>
      ) : (
        // 主视图（技能市场）
        <div className="flex-1 flex flex-col overflow-y-auto custom-scrollbar">
          <section className="px-10 pt-16 pb-24 max-w-7xl mx-auto w-full">
            {/* Header */}
            <div className="flex items-end justify-between mb-16">
              <div>
                <p className="text-gray-400 font-bold mt-3 uppercase text-[10px] tracking-[0.4em]">Engineered Intelligence Market</p>
              </div>
              <div className="flex items-center space-x-4">
                 <div className="relative group">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300 group-focus-within:text-blue-500 transition-colors" size={16} />
                  <input
                    value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                    placeholder="全库技能检索..."
                    className="pl-12 pr-6 py-3.5 bg-white border border-black/5 rounded-2xl text-[12px] font-bold outline-none focus:ring-4 focus:ring-blue-50 transition-all w-64 shadow-sm"
                  />
                 </div>
                 <button
                   onClick={() => setShowAddSkillModal(true)}
                   className="px-8 py-3.5 bg-black text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-105 transition-all shadow-2xl flex items-center space-x-3"
                 >
                  <Plus size={18} /> <span>添加技能</span>
                 </button>
              </div>
            </div>

            {/* 筛选条 (类型与分类) */}
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-12 gap-6">
              <div className="flex items-center space-x-2 overflow-x-auto pb-2 scrollbar-hide">
                 {categories.map(cat => (
                   <button
                    key={cat} onClick={() => setActiveCategory(cat)}
                    className={`px-6 py-2.5 rounded-full text-[11px] font-black uppercase tracking-widest transition-all whitespace-nowrap ${
                      activeCategory === cat ? 'bg-blue-600 text-white shadow-xl shadow-blue-500/20' : 'bg-white text-gray-400 border border-black/5 hover:border-black/20'
                    }`}
                   >
                     {cat === '全部' ? '全部' : cat}
                   </button>
                 ))}
              </div>
              <div className="flex bg-gray-200/40 p-1 rounded-xl border border-black/5 self-start md:self-auto">
                 {(['All', 'Core', 'Plugin'] as const).map(t => (
                   <button
                    key={t} onClick={() => setActiveType(t)}
                    className={`px-6 py-1.5 text-[10px] font-black uppercase rounded-lg transition-all ${
                      activeType === t ? 'bg-white shadow-sm text-black' : 'text-gray-400 hover:text-gray-600'
                    }`}
                   >
                     {t}
                   </button>
                 ))}
              </div>
            </div>

            {/* 技能卡片列表 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
              {filteredSkills.map(skill => (
                <div key={skill.id} className="group bg-white rounded-[40px] p-10 border border-black/[0.04] hover:shadow-[0_40px_100px_-20px_rgba(0,0,0,0.08)] transition-all duration-1000 flex flex-col relative overflow-hidden">
                  <div className="absolute top-6 right-6 flex space-x-2">
                     {/* 状态徽章 */}
                     {skill.status === 'testing' && (
                       <span className="px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest bg-orange-50 text-orange-600 border border-orange-100">
                         调试中
                       </span>
                     )}
                     {skill.status === 'official' && (
                       <span className="px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest bg-blue-50 text-blue-600 border border-blue-100">
                         官方
                       </span>
                     )}
                     {skill.status === 'published' && (
                       <span className="px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest bg-green-50 text-green-600 border border-green-100">
                         已发布
                       </span>
                     )}
                     {skill.status === 'draft' && (
                       <span className="px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest bg-gray-50 text-gray-600 border border-gray-100">
                         草稿
                       </span>
                     )}
                     {/* 类型徽章 */}
                     <span className={`px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest ${
                       skill.type === 'Plugin' ? 'bg-purple-50 text-purple-600 border border-purple-100' : 'bg-blue-50 text-blue-600 border border-blue-100'
                     }`}>
                        {skill.type}
                     </span>
                     {/* 来源徽章 */}
                     {skill.source === 'github' && (
                       <span className="px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest bg-purple-50 text-purple-600 border border-purple-100 flex items-center gap-1">
                         <GitBranch size={10} /> GitHub
                       </span>
                     )}
                     {skill.source === 'conversation' && (
                       <span className="px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest bg-blue-50 text-blue-600 border border-blue-100 flex items-center gap-1">
                         <Sparkles size={10} /> 对话
                       </span>
                     )}
                     {skill.source === 'upload' && (
                       <span className="px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest bg-green-50 text-green-600 border border-green-100 flex items-center gap-1">
                         <Upload size={10} /> 上传
                       </span>
                     )}
                     {skill.source === 'official' && (
                       <span className="px-2.5 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest bg-amber-50 text-amber-600 border border-amber-100 flex items-center gap-1">
                         <Crown size={10} /> 官方
                       </span>
                     )}
                  </div>
                  <div className="flex items-center space-x-3 mb-10">
                    <div className="w-16 h-16 bg-[#F2F2F7] rounded-3xl flex items-center justify-center text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-all duration-500 shadow-sm">{IconMap[skill.icon]}</div>
                    <div className="flex items-center space-x-1 text-[10px] font-black text-amber-400 uppercase tracking-widest"><Star size={14} className="fill-amber-400" /> <span>{skill.rating.toFixed(1)}</span></div>
                  </div>
                  <h3 className="text-2xl font-black text-apple-gray mb-4 tracking-tight group-hover:text-blue-600 transition-colors">{skill.title}</h3>
                  <p className="text-gray-400 font-medium leading-relaxed mb-12 line-clamp-2">{skill.description}</p>
                  <div className="mt-auto pt-8 border-t border-black/[0.02] flex items-center justify-between">
                     <div className="flex items-center space-x-2">
                       {/* 删除按钮 - 仅显示调试中的技能 */}
                       {skill.status === 'testing' && (
                         <button
                           onClick={() => handleDeleteSkill(skill.id, skill.title)}
                           className="px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest bg-red-50 text-red-600 border border-red-100 hover:bg-red-100 transition-all flex items-center gap-1"
                           title="删除技能"
                         >
                           <Trash2 size={12} />
                           <span>删除</span>
                         </button>
                       )}
                       <div className="flex items-center space-x-2 text-[10px] font-black text-gray-300 uppercase tracking-widest"><Users size={14}/> <span>{skill.users}</span></div>
                     </div>
                     <button
                      onClick={async () => {
                        // 加载技能的实际文件内容
                        const fileTree = await loadSkillFiles(skill.id, skill);
                        // 创建一个新的 skill 对象，包含实际的文件树
                        const skillWithFiles = { ...skill, tree: fileTree };
                        setDebugSkill(skillWithFiles);
                        const initText = `Nexus Sandbox [${skill.title}] 初始化完成。${skill.type === 'Plugin' ? '插件链路已同步。' : '核心引擎已就绪。'}`;
                        setDebugMessages([{
                          id: 'init',
                          text: initText,
                          html: simpleMarkdown(initText),
                          sender: 'ai'
                        }]);
                        setActiveFile(fileTree[0].children ? fileTree[0].children[0] : fileTree[0]);
                      }}
                      className="px-8 py-3 bg-black text-white rounded-xl text-[11px] font-black uppercase tracking-widest hover:scale-105 transition-all shadow-lg"
                     >进入调试</button>
                  </div>
                </div>
              ))}
              {filteredSkills.length === 0 && (
                <div className="col-span-full py-32 flex flex-col items-center opacity-20">
                   <Boxes size={64} className="mb-6" />
                   <p className="text-2xl font-black">未找到符合条件的技能</p>
                </div>
              )}
            </div>
          </section>
        </div>
      )}

      {/* 添加技能模态框 */}
      {showAddSkillModal && (
        <AddSkillModal
          onClose={() => setShowAddSkillModal(false)}
          onSelectMode={handleSelectAddSkillMode}
        />
      )}

      {/* 上传 ZIP */}
      {uploadZipMode && (
        <UploadSkillZip
          onClose={() => setUploadZipMode(false)}
          onSkillUploaded={() => {
            loadSkillsFromDB();
          }}
        />
      )}
    </div>
  );
};
