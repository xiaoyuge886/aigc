/**
 * Resource Center Component
 * 
 * 资源配置中心，包含：
 * 1. 系统提示词列表
 * 2. 技能列表
 * 3. 业务场景列表
 */
import React, { useState, useEffect } from 'react';
import { FileText, Sparkles, Briefcase, Plus, Edit, Trash2, Search, X, Eye, EyeOff, Zap, ChevronRight, Star, Users, ArrowUpRight, Crown, Palette, Code2, GraduationCap, Megaphone, UserCircle } from 'lucide-react';
import { 
  platformService, 
  SystemPrompt, 
  SystemPromptCreate, 
  Skill, 
  SkillCreate, 
  BusinessScenario,
  BusinessScenarioCreate 
} from '../services/platformService';

type ResourceType = 'prompts' | 'skills' | 'scenarios';

// 可用工具列表
const AVAILABLE_TOOLS = [
  { id: 'Read', name: 'Read', description: '读取文件' },
  { id: 'Write', name: 'Write', description: '写入文件' },
  { id: 'Edit', name: 'Edit', description: '编辑文件' },
  { id: 'Bash', name: 'Bash', description: '执行命令' },
  { id: 'Glob', name: 'Glob', description: '文件匹配' },
  { id: 'Grep', name: 'Grep', description: '内容搜索' },
  { id: 'WebSearch', name: 'WebSearch', description: '网页搜索' },
  { id: 'WebFetch', name: 'WebFetch', description: '网页获取' },
  { id: 'TodoWrite', name: 'TodoWrite', description: '待办事项管理' },
];

interface ResourceCenterProps {
  onEditScenario?: (scenarioId: number) => void; // 编辑业务场景回调（使用整数ID）
  onCreateScenario?: () => void; // 创建业务场景回调
  defaultTab?: ResourceType; // 默认显示的标签
}

export const ResourceCenter: React.FC<ResourceCenterProps> = ({ 
  onEditScenario,
  onCreateScenario,
  defaultTab = 'prompts'
}) => {
  const [activeTab, setActiveTab] = useState<ResourceType>(defaultTab);
  
  // 当 defaultTab 改变时，更新 activeTab
  useEffect(() => {
    if (defaultTab) {
      setActiveTab(defaultTab);
    }
  }, [defaultTab]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Data states
  const [prompts, setPrompts] = useState<SystemPrompt[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [scenarios, setScenarios] = useState<BusinessScenario[]>([]);
  
  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showViewDialog, setShowViewDialog] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  
  // Form states
  const [formData, setFormData] = useState<any>({});
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  // 系统提示词选择状态（用于业务场景表单）
  const [selectedPromptId, setSelectedPromptId] = useState<string>('');
  const [useCustomPrompt, setUseCustomPrompt] = useState<boolean>(false);
  
  // Search
  const [searchQuery, setSearchQuery] = useState('');
  // 技能分类筛选（仅用于技能列表）
  const [activeCategory, setActiveCategory] = useState('全部');
  
  // 技能分类列表（用于筛选）
  const skillCategories = [
    { name: '全部', icon: <Zap size={14} /> },
    { name: '商业助手', icon: <Briefcase size={14} /> },
    { name: '创意辅助', icon: <Palette size={14} /> },
    { name: '技术开发', icon: <Code2 size={14} /> },
    { name: '学术研究', icon: <GraduationCap size={14} /> },
    { name: '数字营销', icon: <Megaphone size={14} /> },
    { name: '私人助理', icon: <UserCircle size={14} /> },
  ];

  // 技能分类选项（用于编辑表单的下拉框，包含所有可用分类）
  const skillCategoryOptions = [
    { value: '商业助手', label: '商业助手', icon: <Briefcase size={16} />, color: 'text-blue-600' },
    { value: '创意辅助', label: '创意辅助', icon: <Palette size={16} />, color: 'text-rose-600' },
    { value: '技术开发', label: '技术开发', icon: <Code2 size={16} />, color: 'text-purple-600' },
    { value: '学术研究', label: '学术研究', icon: <GraduationCap size={16} />, color: 'text-indigo-600' },
    { value: '数字营销', label: '数字营销', icon: <Megaphone size={16} />, color: 'text-amber-600' },
    { value: '私人助理', label: '私人助理', icon: <UserCircle size={16} />, color: 'text-slate-700' },
    { value: '其他', label: '其他', icon: <Sparkles size={16} />, color: 'text-gray-600' },
    { value: '智能指导', label: '智能指导', icon: <Sparkles size={16} />, color: 'text-blue-600' },
    { value: '思考指导', label: '思考指导', icon: <Sparkles size={16} />, color: 'text-indigo-600' },
  ];

  // 根据分类获取图标
  const getIconForCategory = (category: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      '商业助手': <Briefcase size={24} strokeWidth={1.5} />,
      '创意辅助': <Palette size={24} strokeWidth={1.5} />,
      '技术开发': <Code2 size={24} strokeWidth={1.5} />,
      '学术研究': <GraduationCap size={24} strokeWidth={1.5} />,
      '数字营销': <Megaphone size={24} strokeWidth={1.5} />,
      '私人助理': <UserCircle size={24} strokeWidth={1.5} />,
      '其他': <Sparkles size={24} strokeWidth={1.5} />,
      '智能指导': <Sparkles size={24} strokeWidth={1.5} />,
      '思考指导': <Sparkles size={24} strokeWidth={1.5} />,
    };
    return iconMap[category] || <Sparkles size={24} strokeWidth={1.5} />;
  };

  // 根据分类获取颜色和渐变
  const getColorForCategory = (category: string) => {
    const colorMap: Record<string, { color: string; gradient: string }> = {
      '商业助手': { color: 'text-blue-600', gradient: 'from-blue-500/20 to-blue-600/5' },
      '创意辅助': { color: 'text-rose-600', gradient: 'from-rose-500/20 to-rose-600/5' },
      '技术开发': { color: 'text-purple-600', gradient: 'from-purple-500/20 to-purple-600/5' },
      '学术研究': { color: 'text-indigo-600', gradient: 'from-indigo-500/20 to-indigo-600/5' },
      '数字营销': { color: 'text-amber-600', gradient: 'from-amber-500/20 to-amber-600/5' },
      '私人助理': { color: 'text-slate-700', gradient: 'from-slate-500/20 to-slate-600/5' },
      '其他': { color: 'text-gray-600', gradient: 'from-gray-500/20 to-gray-600/5' },
      '智能指导': { color: 'text-blue-600', gradient: 'from-blue-500/20 to-blue-600/5' },
      '思考指导': { color: 'text-indigo-600', gradient: 'from-indigo-500/20 to-indigo-600/5' },
    };
    return colorMap[category] || { color: 'text-gray-600', gradient: 'from-gray-500/20 to-gray-600/5' };
  };

  // Load data
  useEffect(() => {
    loadData();
    // 切换标签时重置筛选条件
    setSearchQuery('');
    if (activeTab === 'skills') {
      setActiveCategory('全部');
    }
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 总是加载skills，因为场景需要显示技能名称
      if (activeTab === 'prompts') {
        const data = await platformService.listSystemPrompts();
        setPrompts(data);
        const skillsData = await platformService.listSkills();
        setSkills(skillsData);
      } else if (activeTab === 'skills') {
        const data = await platformService.listSkills();
        setSkills(data);
      } else if (activeTab === 'scenarios') {
        const data = await platformService.listScenarios(false);
        setScenarios(data);
        const skillsData = await platformService.listSkills();
        setSkills(skillsData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    // 如果是业务场景，调用回调函数导航到新页面
    if (activeTab === 'scenarios' && onCreateScenario) {
      onCreateScenario();
      return;
    }
    
    setSelectedItem(null);
    setFormData({});
    setFormErrors({});
    setSelectedPromptId('');
    setUseCustomPrompt(false);
    
    setShowCreateDialog(true);
  };

  const handleEdit = async (item: any) => {
    // 如果是业务场景，调用回调函数导航到新页面
    if (activeTab === 'scenarios' && onEditScenario && item.id) {  // 使用整数ID
      onEditScenario(item.id);
      return;
    }
    
    setSelectedItem(item);
    
    // 初始化表单数据
    if (activeTab === 'prompts') {
      setFormData({
        name: item.name || '',
        description: item.description || '',
        category: item.category || '',
        content: item.content || '',
        is_default: item.is_default || false,
        is_public: item.is_public || false,
      });
    } else if (activeTab === 'skills') {
      setFormData({
        name: item.name || '',
        description: item.description || '',
        category: item.category || '',
        skill_content: item.skill_content || '',
        skill_config: item.skill_config ? JSON.stringify(item.skill_config, null, 2) : '',
        is_default: item.is_default || false,
        is_public: item.is_public || false,
      });
    } else if (activeTab === 'scenarios') {
      // 检查系统提示词是否匹配已有的提示词
      const matchingPrompt = prompts.find(p => p.content === item.system_prompt);
      const promptId = matchingPrompt ? matchingPrompt.id : undefined;  // 使用整数ID
      
      setFormData({
        // 移除 scenario_id 字段，使用自增整数 id
        name: item.name || '',
        description: item.description || '',
        system_prompt: item.system_prompt || '',
        allowed_tools: item.allowed_tools ? item.allowed_tools : [],
        recommended_model: item.recommended_model || '',
        skills: item.skills ? item.skills : [],
        custom_tools: item.custom_tools ? JSON.stringify(item.custom_tools, null, 2) : '',
        workflow: item.workflow ? JSON.stringify(item.workflow, null, 2) : '',
        permission_mode: item.permission_mode || '',
        max_turns: item.max_turns || '',
        work_dir: item.work_dir || '',
        is_public: item.is_public || false,
        is_default: item.is_default || false,
      });
      
      // 设置提示词选择状态
      if (promptId !== undefined) {
        setSelectedPromptId(String(promptId));  // 转换为字符串用于下拉框
        setUseCustomPrompt(false);
      } else {
        setSelectedPromptId('');
        setUseCustomPrompt(true);
      }
    }
    setFormErrors({});
    setShowEditDialog(true);
  };

  const handleView = (item: any) => {
    setSelectedItem(item);
    setShowViewDialog(true);
  };

  const handleDelete = async (item: any) => {
    if (!confirm(`确定要删除 "${item.name || item.id}" 吗？`)) {  // 使用整数ID
      return;
    }
    
    try {
      if (activeTab === 'prompts') {
        await platformService.deleteSystemPrompt(item.id);  // 使用整数ID
      } else if (activeTab === 'skills') {
        await platformService.deleteSkill(item.id);  // 使用整数ID
      } else if (activeTab === 'scenarios') {
        await platformService.deleteScenario(item.id);  // 使用整数ID
      }
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : '删除失败');
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (activeTab === 'prompts') {
      if (!formData.prompt_id?.trim()) errors.prompt_id = '提示词ID不能为空';
      if (!formData.name?.trim()) errors.name = '名称不能为空';
      if (!formData.content?.trim()) errors.content = '内容不能为空';
    } else if (activeTab === 'skills') {
      // 创建时需要 skill_id，编辑时不需要（使用 selectedItem.skill_id）
      if (showCreateDialog && !formData.skill_id?.trim()) {
        errors.skill_id = '技能ID不能为空';
      }
      if (!formData.name?.trim()) errors.name = '名称不能为空';
      if (!formData.skill_content?.trim()) errors.skill_content = '技能内容不能为空';
    } else if (activeTab === 'scenarios') {
      // 移除 scenario_id 验证，使用自增整数 id
      if (!formData.name?.trim()) errors.name = '名称不能为空';
      // 系统提示词：如果使用自定义提示词，需要检查 formData.system_prompt；如果使用下拉框选择，需要检查 selectedPromptId
      if (useCustomPrompt && !formData.system_prompt?.trim()) {
        errors.system_prompt = '系统提示词不能为空';
      } else if (!useCustomPrompt && !selectedPromptId) {
        errors.system_prompt = '请选择系统提示词';
      }
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    console.log('[ResourceCenter] handleSubmit called', {
      activeTab,
      showCreateDialog,
      showEditDialog,
      formData: {
        ...formData,
        skill_content: formData.skill_content ? formData.skill_content.substring(0, 50) + '...' : '',
      },
      selectedItem: selectedItem ? { skill_id: selectedItem.skill_id, id: selectedItem.id } : null
    });
    
    if (!validateForm()) {
      console.log('[ResourceCenter] Validation failed', formErrors);
      return;
    }
    
    console.log('[ResourceCenter] Validation passed, submitting...');
    setSubmitting(true);
    try {
      if (activeTab === 'prompts') {
        if (showCreateDialog) {
          await platformService.createSystemPrompt({
            prompt_id: formData.prompt_id.trim(),
            name: formData.name.trim(),
            description: formData.description?.trim() || undefined,
            category: formData.category?.trim() || undefined,
            content: formData.content.trim(),
            is_default: formData.is_default || false,
            is_public: formData.is_public || false,
          });
        } else {
          await platformService.updateSystemPrompt(selectedItem.prompt_id, {
            name: formData.name.trim(),
            description: formData.description?.trim() || undefined,
            category: formData.category?.trim() || undefined,
            content: formData.content.trim(),
            is_default: formData.is_default || false,
            is_public: formData.is_public || false,
          });
        }
      } else if (activeTab === 'skills') {
        let skillConfig: Record<string, any> | undefined;
        if (formData.skill_config?.trim()) {
          try {
            skillConfig = JSON.parse(formData.skill_config);
          } catch (e) {
            setFormErrors({ skill_config: '技能配置必须是有效的JSON格式' });
            setSubmitting(false);
            return;
          }
        }
        
        if (showCreateDialog) {
          await platformService.createSkill({
            skill_id: formData.skill_id.trim(),
            name: formData.name.trim(),
            description: formData.description?.trim() || undefined,
            category: formData.category?.trim() || undefined,
            skill_content: formData.skill_content.trim(),
            skill_config: skillConfig,
            is_default: formData.is_default || false,
            is_public: formData.is_public || false,
          });
        } else {
          // 检查技能是否在数据库中（id !== 0 且 id !== null）
          // 如果技能来自文件系统（id === 0），则创建新记录而不是更新
          console.log('[ResourceCenter] Editing skill', {
            skill_id: selectedItem.skill_id,
            id: selectedItem.id,
            isFileSystemSkill: !selectedItem.id || selectedItem.id === 0
          });
          
          if (!selectedItem.id || selectedItem.id === 0) {
            // 文件系统技能，创建数据库记录
            console.log('[ResourceCenter] Creating database record for file system skill');
            await platformService.createSkill({
              skill_id: selectedItem.skill_id,
              name: formData.name.trim(),
              description: formData.description?.trim() || undefined,
              category: formData.category?.trim() || undefined,
              skill_content: formData.skill_content.trim(),
              skill_config: skillConfig,
              is_default: formData.is_default || false,
              is_public: formData.is_public || false,
            });
            console.log('[ResourceCenter] Skill created successfully');
          } else {
            // 数据库技能，更新现有记录
            console.log('[ResourceCenter] Updating database skill');
            await platformService.updateSkill(selectedItem.id, {
              name: formData.name.trim(),
              description: formData.description?.trim() || undefined,
              category: formData.category?.trim() || undefined,
              skill_content: formData.skill_content.trim(),
              skill_config: skillConfig,
              is_default: formData.is_default || false,
              is_public: formData.is_public || false,
            });
            console.log('[ResourceCenter] Skill updated successfully');
          }
        }
      } else if (activeTab === 'scenarios') {
        // allowed_tools 现在是数组，直接使用
        const allowedTools = Array.isArray(formData.allowed_tools) && formData.allowed_tools.length > 0
          ? formData.allowed_tools
          : undefined;
        // skills 现在已经是数组格式
        const skills = Array.isArray(formData.skills) && formData.skills.length > 0
          ? formData.skills
          : undefined;
        
        // 解析 custom_tools JSON
        let customTools: Record<string, any> | undefined;
        if (formData.custom_tools?.trim()) {
          try {
            customTools = JSON.parse(formData.custom_tools);
          } catch (e) {
            setFormErrors({ custom_tools: '自定义工具配置必须是有效的JSON格式' });
            setSubmitting(false);
            return;
          }
        }
        
        // 解析 workflow JSON
        let workflow: Record<string, any> | undefined;
        if (formData.workflow?.trim()) {
          try {
            workflow = JSON.parse(formData.workflow);
          } catch (e) {
            setFormErrors({ workflow: '工作流配置必须是有效的JSON格式' });
            setSubmitting(false);
            return;
          }
        }
        
        // 确定系统提示词：如果使用下拉框选择，从 prompts 中获取；否则使用自定义输入
        let systemPrompt = '';
        if (useCustomPrompt) {
          systemPrompt = formData.system_prompt?.trim() || '';
        } else if (selectedPromptId) {
          const selectedPrompt = prompts.find(p => p.prompt_id === selectedPromptId);
          if (selectedPrompt) {
            systemPrompt = selectedPrompt.content;
          } else {
            setFormErrors({ system_prompt: '选择的系统提示词不存在' });
            setSubmitting(false);
            return;
          }
        }
        
        if (showCreateDialog) {
          await platformService.createScenario({
            // 移除 scenario_id 字段，使用自增整数 id
            name: formData.name.trim(),
            description: formData.description?.trim() || undefined,
            system_prompt: systemPrompt,
            allowed_tools: allowedTools,
            recommended_model: formData.recommended_model?.trim() || undefined,
            skills: skills,
            custom_tools: customTools,
            workflow: workflow,
            permission_mode: formData.permission_mode?.trim() || undefined,
            max_turns: formData.max_turns ? parseInt(String(formData.max_turns)) : undefined,
            work_dir: formData.work_dir?.trim() || undefined,
            is_public: formData.is_public || false,
            is_default: formData.is_default || false,
          });
        } else {
          await platformService.updateScenario(selectedItem.id, {  // 使用整数ID
            name: formData.name.trim(),
            description: formData.description?.trim() || undefined,
            system_prompt: systemPrompt,
            allowed_tools: allowedTools,
            recommended_model: formData.recommended_model?.trim() || undefined,
            skills: skills,
            custom_tools: customTools,
            workflow: workflow,
            permission_mode: formData.permission_mode?.trim() || undefined,
            max_turns: formData.max_turns ? parseInt(String(formData.max_turns)) : undefined,
            work_dir: formData.work_dir?.trim() || undefined,
            is_public: formData.is_public || false,
            is_default: formData.is_default !== undefined && formData.is_default !== null ? formData.is_default : undefined,
          });
        }
      }
      
      setShowCreateDialog(false);
      setShowEditDialog(false);
      setSelectedItem(null);
      setFormData({});
      setFormErrors({});
      console.log('[ResourceCenter] Submit successful, closing dialog and reloading data');
      await loadData();
      console.log('[ResourceCenter] Data reloaded');
    } catch (err) {
      console.error('[ResourceCenter] Submit error:', err);
      alert(err instanceof Error ? err.message : '操作失败');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredItems = () => {
    let items: any[] = [];
    if (activeTab === 'prompts') items = prompts;
    else if (activeTab === 'skills') items = skills;
    else if (activeTab === 'scenarios') items = scenarios;
    
    // 技能列表：按分类筛选
    if (activeTab === 'skills' && activeCategory !== '全部') {
      items = items.filter(item => item.category === activeCategory);
    }
    
    // 搜索筛选
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      items = items.filter(item => 
        item.name?.toLowerCase().includes(query) ||
        item.description?.toLowerCase().includes(query) ||
        String(item.id || '').includes(query)  // 使用整数ID
      );
    }
    
    return items;
  };

  const tabs = [
    { id: 'prompts' as ResourceType, label: '系统提示词', icon: <FileText size={16} /> },
    { id: 'skills' as ResourceType, label: '技能列表', icon: <Sparkles size={16} /> },
    { id: 'scenarios' as ResourceType, label: '业务场景', icon: <Briefcase size={16} /> },
  ];

  return (
    <div className="flex h-full space-x-6 min-h-[600px]">
      {/* 左侧垂直标签栏 */}
      <div className="w-52 flex-shrink-0 bg-white rounded-2xl border border-gray-200 p-3 shadow-sm">
        <div className="mb-4 px-3">
          <h3 className="text-sm font-bold text-gray-900 mb-1">资源配置中心</h3>
          <p className="text-xs text-gray-500">管理系统资源</p>
        </div>
        <div className="space-y-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition-all text-sm font-semibold ${
                activeTab === tab.id
                  ? 'bg-blue-50 text-blue-600 border border-blue-200'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 右侧内容区 */}
      <div className="flex-1 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-black text-gray-900">
              {tabs.find(t => t.id === activeTab)?.label}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {activeTab === 'prompts' && '管理系统提示词模板'}
              {activeTab === 'skills' && '管理技能模板'}
              {activeTab === 'scenarios' && '管理业务场景模板'}
            </p>
          </div>
          <button
            onClick={handleCreate}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors text-sm font-semibold"
          >
            <Plus size={16} />
            <span>新建</span>
          </button>
        </div>

        {/* 技能列表：分类导航 */}
        {activeTab === 'skills' && (
          <div className="mb-6">
            <nav className="flex items-center p-1.5 bg-[#F5F5F7] rounded-2xl border border-[#D2D2D7]/20 overflow-x-auto">
              {skillCategories.slice(0, 6).map((cat) => (
                <button
                  key={cat.name}
                  onClick={() => setActiveCategory(cat.name)}
                  className={`px-6 py-2 rounded-xl text-xs font-black transition-all whitespace-nowrap uppercase tracking-wider flex items-center space-x-2 ${
                    activeCategory === cat.name
                      ? 'bg-white text-[#0066CC] shadow-md shadow-black/5'
                      : 'text-[#86868B] hover:text-[#1D1D1F]'
                  }`}
                >
                  <span>{cat.icon}</span>
                  <span>{cat.name}</span>
                </button>
              ))}
              {skillCategories.length > 6 && (
                <button className="p-2 text-[#86868B] hover:text-[#1D1D1F]">
                  <ChevronRight size={16} />
                </button>
              )}
            </nav>
          </div>
        )}

        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-[#D2D2D7]" size={18} />
          <input
            type="text"
            placeholder={activeTab === 'skills' ? '搜索技能...' : '搜索...'}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-10 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-[13px] font-bold focus:outline-none focus:bg-white focus:border-[#D2D2D7]/50 focus:shadow-xl transition-all placeholder-[#D2D2D7]"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-600 text-sm">
            {error}
          </div>
        ) : (
          <div className={activeTab === 'skills' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8' : 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'}>
            {filteredItems().map((item, index) => (
              activeTab === 'skills' ? (
                // 技能列表：使用技能市场的卡片样式
                <div
                  key={item.skill_id}
                  className="group bg-white rounded-[40px] p-8 border border-[#D2D2D7]/30 hover:border-[#0066CC]/20 hover:shadow-[0_40px_100px_-20px_rgba(0,0,0,0.06)] transition-all duration-700 transform"
                >
                  <div className="flex justify-between items-start mb-6">
                    {(() => {
                      const category = item.category || '其他';
                      const colors = getColorForCategory(category);
                      return (
                        <div className={`w-16 h-16 bg-gradient-to-br ${colors.gradient} rounded-[24px] flex items-center justify-center ${colors.color} shadow-sm group-hover:scale-110 group-hover:shadow-lg transition-all duration-500`}>
                          {getIconForCategory(category)}
                        </div>
                      );
                    })()}
                    <div className="flex items-center space-x-2">
                      {item.is_public ? (
                        <Eye size={14} className="text-green-500" title="公开" />
                      ) : (
                        <EyeOff size={14} className="text-gray-400" title="私有" />
                      )}
                      {item.is_default && (
                        <div className="bg-[#FFF8E1] border border-[#FFE082]/30 px-3 py-1 rounded-full flex items-center space-x-1.5 shadow-sm">
                          <Crown size={12} className="text-[#FFA000]" />
                          <span className="text-[10px] font-black text-[#FFA000] uppercase tracking-widest">默认</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="space-y-4 mb-6">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xl font-black text-[#1D1D1F] tracking-tight group-hover:text-[#0066CC] transition-colors">
                        {item.name}
                      </h4>
                      <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="text-[10px] font-black text-[#0066CC] uppercase tracking-wider">查看详情</span>
                        <ArrowUpRight size={12} className="text-[#0066CC]" />
                      </div>
                    </div>
                    
                    <p className="text-[14px] text-[#86868B] font-medium leading-relaxed line-clamp-2 min-h-[3rem]">
                      {item.description || '暂无描述'}
                    </p>

                    {item.category && (
                      <div className="flex flex-wrap gap-2 pt-2">
                        <span className="text-[10px] font-bold text-[#86868B] bg-[#F5F5F7] px-2.5 py-1 rounded-lg uppercase tracking-wider border border-transparent group-hover:border-[#D2D2D7]/30 transition-all">
                          {item.category}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="mt-auto pt-6 border-t border-[#D2D2D7]/10 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-1">
                        <Users size={12} className="text-[#86868B]" />
                        <span className="text-xs font-bold text-[#86868B]">{item.usage_count || 0}</span>
                      </div>
                      <span className="text-xs text-[#86868B]">使用次数</span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleView(item)}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-xl text-xs font-bold hover:bg-gray-200 transition-all"
                      >
                        查看
                      </button>
                      <button
                        onClick={() => handleEdit(item)}
                        className="px-4 py-2 bg-blue-50 text-blue-600 rounded-xl text-xs font-bold hover:bg-blue-100 transition-all"
                      >
                        <Edit size={14} />
                      </button>
                      <button
                        onClick={() => handleDelete(item)}
                        className="px-4 py-2 bg-red-50 text-red-600 rounded-xl text-xs font-bold hover:bg-red-100 transition-all"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                // 其他列表：保持原有样式
                <div
                  key={item.id}  // 使用整数ID
                  className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-bold text-gray-900 mb-1">{item.name}</h3>
                      <p className="text-xs text-gray-500">
                        ID: {item.id}  {/* 使用整数ID */}
                      </p>
                    </div>
                    <div className="flex items-center space-x-1">
                      {item.is_public ? (
                        <Eye size={14} className="text-green-500" title="公开" />
                      ) : (
                        <EyeOff size={14} className="text-gray-400" title="私有" />
                      )}
                      {item.is_default && (
                        <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full font-semibold">
                          默认
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {item.description && (
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">{item.description}</p>
                  )}
                  
                  {/* 场景列表：显示 system_prompt 预览 */}
                  {activeTab === 'scenarios' && item.system_prompt && (
                    <div className="mb-3 p-2 bg-gray-50 rounded-lg border border-gray-200">
                      <p className="text-xs font-semibold text-gray-700 mb-1">系统提示词预览：</p>
                      <p className="text-xs text-gray-600 line-clamp-3 font-mono whitespace-pre-wrap">
                        {item.system_prompt.length > 150 
                          ? item.system_prompt.substring(0, 150) + '...' 
                          : item.system_prompt}
                      </p>
                      {item.system_prompt.length > 150 && (
                        <p className="text-xs text-gray-400 mt-1">
                          总长度: {item.system_prompt.length} 字符
                        </p>
                      )}
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                    <span>使用次数: {item.usage_count || 0}</span>
                    {item.category && (
                      <span className="bg-gray-100 px-2 py-1 rounded-full">{item.category}</span>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleView(item)}
                      className="flex-1 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-xs font-semibold"
                    >
                      查看
                    </button>
                    <button
                      onClick={() => handleEdit(item)}
                      className="px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
                    >
                      <Edit size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(item)}
                      className="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              )
            ))}
          </div>
        )}
        
        {/* 空状态提示 */}
        {!loading && !error && filteredItems().length === 0 && (
          <div className="py-32 text-center">
            <div className="w-20 h-20 bg-[#F5F5F7] rounded-[40px] flex items-center justify-center mx-auto mb-8">
              <Search size={32} className="text-[#D2D2D7]" />
            </div>
            <p className="text-xl text-[#1D1D1F] font-black mb-2">未找到匹配项</p>
            <p className="text-[#86868B] font-medium mb-8">
              {activeTab === 'skills' ? '尝试更改搜索词或选择不同的分类。' : '尝试更改搜索词。'}
            </p>
            <button 
              onClick={() => {
                setSearchQuery('');
                if (activeTab === 'skills') setActiveCategory('全部');
              }}
              className="px-8 py-3 bg-[#1D1D1F] text-white rounded-2xl font-black text-sm transition-all hover:bg-black active:scale-95"
            >
              重置筛选器
            </button>
          </div>
        )}

        {/* Create/Edit Dialog */}
        {(showCreateDialog || showEditDialog) && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl p-6 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold">
                  {showCreateDialog ? '新建' : '编辑'} {tabs.find(t => t.id === activeTab)?.label}
                </h3>
                <button
                  onClick={() => {
                    setShowCreateDialog(false);
                    setShowEditDialog(false);
                    setSelectedItem(null);
                    setFormData({});
                    setFormErrors({});
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="space-y-4">
                {/* System Prompt Form */}
                {activeTab === 'prompts' && (
                  <>
                    {showCreateDialog && (
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1">
                          提示词ID <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={formData.prompt_id || ''}
                          onChange={(e) => setFormData({ ...formData, prompt_id: e.target.value })}
                          className={`w-full px-3 py-2 border rounded-lg text-sm ${
                            formErrors.prompt_id ? 'border-red-500' : 'border-gray-300'
                          }`}
                          placeholder="例如: default_prompt"
                        />
                        {formErrors.prompt_id && (
                          <p className="text-xs text-red-500 mt-1">{formErrors.prompt_id}</p>
                        )}
                      </div>
                    )}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        名称 <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={formData.name || ''}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className={`w-full px-3 py-2 border rounded-lg text-sm ${
                          formErrors.name ? 'border-red-500' : 'border-gray-300'
                        }`}
                        placeholder="提示词名称"
                      />
                      {formErrors.name && (
                        <p className="text-xs text-red-500 mt-1">{formErrors.name}</p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">描述</label>
                      <textarea
                        value={formData.description || ''}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        rows={2}
                        placeholder="提示词描述"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">分类</label>
                      <input
                        type="text"
                        value={formData.category || ''}
                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        placeholder="例如: 通用、专业、定制"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        内容 <span className="text-red-500">*</span>
                      </label>
                      <textarea
                        value={formData.content || ''}
                        onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                        className={`w-full px-3 py-2 border rounded-lg text-sm font-mono ${
                          formErrors.content ? 'border-red-500' : 'border-gray-300'
                        }`}
                        rows={10}
                        placeholder="输入提示词内容..."
                      />
                      {formErrors.content && (
                        <p className="text-xs text-red-500 mt-1">{formErrors.content}</p>
                      )}
                    </div>
                    <div className="flex items-center space-x-4">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={formData.is_default || false}
                          onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                          className="rounded"
                        />
                        <span className="text-sm text-gray-700">设为默认</span>
                      </label>
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={formData.is_public || false}
                          onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                          className="rounded"
                        />
                        <span className="text-sm text-gray-700">公开</span>
                      </label>
                    </div>
                  </>
                )}

                {/* Skill Form */}
                {activeTab === 'skills' && (
                  <>
                    {showCreateDialog && (
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1">
                          技能ID <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={formData.skill_id || ''}
                          onChange={(e) => setFormData({ ...formData, skill_id: e.target.value })}
                          className={`w-full px-3 py-2 border rounded-lg text-sm ${
                            formErrors.skill_id ? 'border-red-500' : 'border-gray-300'
                          }`}
                          placeholder="例如: data_analysis"
                        />
                        {formErrors.skill_id && (
                          <p className="text-xs text-red-500 mt-1">{formErrors.skill_id}</p>
                        )}
                      </div>
                    )}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        名称 <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={formData.name || ''}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className={`w-full px-3 py-2 border rounded-lg text-sm ${
                          formErrors.name ? 'border-red-500' : 'border-gray-300'
                        }`}
                        placeholder="技能名称"
                      />
                      {formErrors.name && (
                        <p className="text-xs text-red-500 mt-1">{formErrors.name}</p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">描述</label>
                      <textarea
                        value={formData.description || ''}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        rows={2}
                        placeholder="技能描述"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">分类</label>
                      <select
                        value={formData.category || ''}
                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">-- 请选择分类 --</option>
                        {skillCategoryOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      {formData.category && (
                        <div className="mt-2 flex items-center space-x-2 text-xs text-gray-500">
                          {(() => {
                            const selectedOption = skillCategoryOptions.find(opt => opt.value === formData.category);
                            return selectedOption ? (
                              <>
                                <span className={selectedOption.color}>{selectedOption.icon}</span>
                                <span>已选择: {selectedOption.label}</span>
                              </>
                            ) : null;
                          })()}
                        </div>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        技能内容 <span className="text-red-500">*</span>
                      </label>
                      <textarea
                        value={formData.skill_content || ''}
                        onChange={(e) => setFormData({ ...formData, skill_content: e.target.value })}
                        className={`w-full px-3 py-2 border rounded-lg text-sm font-mono ${
                          formErrors.skill_content ? 'border-red-500' : 'border-gray-300'
                        }`}
                        rows={10}
                        placeholder="输入技能内容（Markdown格式）..."
                      />
                      {formErrors.skill_content && (
                        <p className="text-xs text-red-500 mt-1">{formErrors.skill_content}</p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">技能配置 (JSON)</label>
                      <textarea
                        value={formData.skill_config || ''}
                        onChange={(e) => setFormData({ ...formData, skill_config: e.target.value })}
                        className={`w-full px-3 py-2 border rounded-lg text-sm font-mono ${
                          formErrors.skill_config ? 'border-red-500' : 'border-gray-300'
                        }`}
                        rows={5}
                        placeholder='{"key": "value"}'
                      />
                      {formErrors.skill_config && (
                        <p className="text-xs text-red-500 mt-1">{formErrors.skill_config}</p>
                      )}
                    </div>
                    <div className="flex items-center space-x-4">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={formData.is_default || false}
                          onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                          className="rounded"
                        />
                        <span className="text-sm text-gray-700">设为默认</span>
                      </label>
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={formData.is_public || false}
                          onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                          className="rounded"
                        />
                        <span className="text-sm text-gray-700">公开</span>
                      </label>
                    </div>
                  </>
                )}

                {/* Business Scenario Form */}
                {activeTab === 'scenarios' && (
                  <>
                    {/* 基本信息 */}
                    <div className="border-b border-gray-200 pb-4 mb-4">
                      <h4 className="text-sm font-bold text-gray-900 mb-3">基本信息</h4>
                      {/* 移除场景ID输入框，使用自增整数ID */}
                      <div className="mb-4">
                        <label className="block text-sm font-semibold text-gray-700 mb-1">
                          名称 <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={formData.name || ''}
                          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                          className={`w-full px-3 py-2 border rounded-lg text-sm ${
                            formErrors.name ? 'border-red-500' : 'border-gray-300'
                          }`}
                          placeholder="场景名称"
                        />
                        {formErrors.name && (
                          <p className="text-xs text-red-500 mt-1">{formErrors.name}</p>
                        )}
                      </div>
                      <div className="mb-4">
                        <label className="block text-sm font-semibold text-gray-700 mb-1">描述</label>
                        <textarea
                          value={formData.description || ''}
                          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          rows={3}
                          placeholder="场景描述，说明此场景的用途和特点"
                        />
                      </div>
                    </div>

                    {/* 核心配置 */}
                    <div className="border-b border-gray-200 pb-4 mb-4">
                      <h4 className="text-sm font-bold text-gray-900 mb-3">核心配置</h4>
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <label className="block text-sm font-semibold text-gray-700">
                            系统提示词 <span className="text-red-500">*</span>
                          </label>
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={useCustomPrompt}
                              onChange={(e) => {
                                setUseCustomPrompt(e.target.checked);
                                if (!e.target.checked) {
                                  // 切换到选择模式，清空自定义内容
                                  setSelectedPromptId('');
                                  setFormData({ ...formData, system_prompt: '' });
                                }
                              }}
                              className="rounded"
                            />
                            <span className="text-xs text-gray-600">使用自定义提示词</span>
                          </label>
                        </div>
                        
                        {!useCustomPrompt ? (
                          // 选择已有系统提示词
                          <div className="space-y-2">
                            <select
                              value={selectedPromptId}
                              onChange={(e) => {
                                const promptId = e.target.value;
                                setSelectedPromptId(promptId);
                                if (promptId) {
                                  // 找到选中的提示词并填充内容
                                  const selectedPrompt = prompts.find(p => p.prompt_id === promptId);
                                  if (selectedPrompt) {
                                    setFormData({ ...formData, system_prompt: selectedPrompt.content });
                                  }
                                } else {
                                  setFormData({ ...formData, system_prompt: '' });
                                }
                              }}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            >
                              <option value="">-- 请选择系统提示词 --</option>
                              {prompts.map((prompt) => (
                                <option key={prompt.prompt_id} value={prompt.prompt_id}>
                                  {prompt.name} {prompt.is_default ? '(默认)' : ''}
                                </option>
                              ))}
                            </select>
                            {selectedPromptId && (
                              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                <p className="text-xs text-blue-700">
                                  <strong>已选择：</strong>
                                  {prompts.find(p => p.prompt_id === selectedPromptId)?.name}
                                  {prompts.find(p => p.prompt_id === selectedPromptId)?.description && (
                                    <span className="ml-2 text-gray-600">
                                      - {prompts.find(p => p.prompt_id === selectedPromptId)?.description}
                                    </span>
                                  )}
                                </p>
                              </div>
                            )}
                          </div>
                        ) : (
                          // 自定义系统提示词
                          <textarea
                            value={formData.system_prompt || ''}
                            onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                            className={`w-full px-3 py-2 border rounded-lg text-sm font-mono ${
                              formErrors.system_prompt ? 'border-red-500' : 'border-gray-300'
                            }`}
                            rows={10}
                            placeholder="输入自定义系统提示词，定义 Agent 的行为和角色..."
                          />
                        )}
                        
                        {/* 显示选中的提示词内容预览 */}
                        {!useCustomPrompt && selectedPromptId && formData.system_prompt && (
                          <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-lg max-h-48 overflow-y-auto">
                            <p className="text-xs font-semibold text-gray-700 mb-2">提示词内容预览：</p>
                            <pre className="text-xs text-gray-600 font-mono whitespace-pre-wrap">
                              {formData.system_prompt.substring(0, 500)}
                              {formData.system_prompt.length > 500 && '...'}
                            </pre>
                            {formData.system_prompt.length > 500 && (
                              <p className="text-xs text-gray-500 mt-1">
                                提示词总长度: {formData.system_prompt.length} 字符
                              </p>
                            )}
                          </div>
                        )}
                        
                        {formErrors.system_prompt && (
                          <p className="text-xs text-red-500 mt-1">{formErrors.system_prompt}</p>
                        )}
                        <p className="text-xs text-gray-500 mt-1">
                          {useCustomPrompt 
                            ? '定义 Agent 在此场景下的行为、角色和任务要求'
                            : '从已有系统提示词中选择，或勾选"使用自定义提示词"手动输入'}
                        </p>
                      </div>
                    </div>

                    {/* 工具和模型配置 */}
                    <div className="border-b border-gray-200 pb-4 mb-4">
                      <h4 className="text-sm font-bold text-gray-900 mb-3">工具和模型配置</h4>
                      <div className="mb-4">
                        <label className="block text-sm font-semibold text-gray-700 mb-2">允许的工具</label>
                        <div className="grid grid-cols-3 gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200 max-h-48 overflow-y-auto">
                          {AVAILABLE_TOOLS.map((tool) => {
                            const isSelected = Array.isArray(formData.allowed_tools) && formData.allowed_tools.includes(tool.id);
                            return (
                              <label
                                key={tool.id}
                                className={`flex items-center space-x-2 p-2 rounded-lg cursor-pointer transition-all ${
                                  isSelected
                                    ? 'bg-blue-100 border-2 border-blue-500'
                                    : 'bg-white border-2 border-gray-200 hover:border-gray-300'
                                }`}
                              >
                                <input
                                  type="checkbox"
                                  checked={isSelected}
                                  onChange={(e) => {
                                    const current = Array.isArray(formData.allowed_tools) ? formData.allowed_tools : [];
                                    if (e.target.checked) {
                                      setFormData({ ...formData, allowed_tools: [...current, tool.id] });
                                    } else {
                                      setFormData({ ...formData, allowed_tools: current.filter((t: string) => t !== tool.id) });
                                    }
                                  }}
                                  className="rounded"
                                />
                                <div className="flex-1">
                                  <div className="text-xs font-semibold text-gray-900">{tool.name}</div>
                                  <div className="text-xs text-gray-500">{tool.description}</div>
                                </div>
                              </label>
                            );
                          })}
                        </div>
                        <p className="text-xs text-gray-500 mt-2">
                          已选择 {Array.isArray(formData.allowed_tools) ? formData.allowed_tools.length : 0} 个工具
                          {Array.isArray(formData.allowed_tools) && formData.allowed_tools.length === 0 && '（留空表示使用默认工具）'}
                        </p>
                      </div>
                      <div className="mb-4">
                        <label className="block text-sm font-semibold text-gray-700 mb-1">推荐模型</label>
                        <input
                          type="text"
                          value={formData.recommended_model || ''}
                          onChange={(e) => setFormData({ ...formData, recommended_model: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          placeholder="例如: claude-3-5-sonnet-20241022"
                        />
                        <p className="text-xs text-gray-500 mt-1">建议使用的 Claude 模型，留空使用系统默认</p>
                      </div>
                      <div className="mb-4">
                        <label className="block text-sm font-semibold text-gray-700 mb-1">权限模式</label>
                        <select
                          value={formData.permission_mode || ''}
                          onChange={(e) => setFormData({ ...formData, permission_mode: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                        >
                          <option value="">使用系统默认</option>
                          <option value="acceptEdits">acceptEdits - 自动接受编辑</option>
                          <option value="plan">plan - 规划模式，不执行</option>
                          <option value="bypassPermissions">bypassPermissions - 跳过权限检查</option>
                          <option value="default">default - 标准权限行为</option>
                        </select>
                        <p className="text-xs text-gray-500 mt-1">控制 Agent 的权限行为，留空使用系统默认</p>
                      </div>
                      <div className="mb-4">
                        <label className="block text-sm font-semibold text-gray-700 mb-1">最大对话轮数</label>
                        <input
                          type="number"
                          value={formData.max_turns || ''}
                          onChange={(e) => setFormData({ ...formData, max_turns: e.target.value ? parseInt(e.target.value) : '' })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          placeholder="例如: 20"
                          min={1}
                          max={100}
                        />
                        <p className="text-xs text-gray-500 mt-1">限制对话的最大轮数，留空使用系统默认</p>
                      </div>
                      <div className="mb-4">
                        <label className="block text-sm font-semibold text-gray-700 mb-1">工作目录</label>
                        <input
                          type="text"
                          value={formData.work_dir || ''}
                          onChange={(e) => setFormData({ ...formData, work_dir: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                          placeholder="例如: /path/to/workdir"
                        />
                        <p className="text-xs text-gray-500 mt-1">Agent 的工作目录路径，留空使用系统默认</p>
                      </div>
                      <div className="mb-4">
                        <label className="block text-sm font-semibold text-gray-700 mb-2">关联技能</label>
                        {skills.length === 0 ? (
                          <div className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm min-h-[120px] flex items-center justify-center text-gray-500">
                            正在加载技能列表...
                          </div>
                        ) : (
                          <div className="grid grid-cols-3 gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200 max-h-48 overflow-y-auto">
                            {skills.map((skill) => {
                              const skillIdStr = String(skill.id); // 转换为字符串进行比较
                              const isSelected = Array.isArray(formData.skills) && formData.skills.includes(skillIdStr);
                              return (
                                <div
                                  key={skill.id}
                                  className={`flex items-center space-x-2 p-2 rounded-lg transition-all ${
                                    isSelected
                                      ? 'bg-blue-100 border-2 border-blue-500'
                                      : 'bg-white border-2 border-gray-200'
                                  }`}
                                >
                                  <input
                                    type="checkbox"
                                    id={`resource-skill-${skill.id}`}
                                    checked={isSelected}
                                    onChange={(e) => {
                                      e.stopPropagation();
                                      const current = Array.isArray(formData.skills) ? formData.skills : [];
                                      if (e.target.checked) {
                                        setFormData({ ...formData, skills: [...current, skillIdStr] });
                                      } else {
                                        setFormData({ ...formData, skills: current.filter((s: string) => s !== skillIdStr) });
                                      }
                                    }}
                                    className="rounded"
                                  />
                                  <label
                                    htmlFor={`resource-skill-${skill.id}`}
                                    className="flex-1 cursor-pointer select-none"
                                  >
                                    <div className="text-xs font-semibold text-gray-900">{skill.name}</div>
                                    <div className="text-xs text-gray-500">{skill.description || skill.category || '无描述'}</div>
                                  </label>
                                </div>
                              );
                            })}
                          </div>
                        )}
                        <p className="text-xs text-gray-500 mt-2">
                          已选择 {Array.isArray(formData.skills) ? formData.skills.length : 0} 个技能
                          {Array.isArray(formData.skills) && formData.skills.length === 0 && '（留空表示不限制技能使用）'}
                        </p>
                      </div>
                    </div>

                    {/* 高级配置 */}
                    <div className="border-b border-gray-200 pb-4 mb-4">
                      <h4 className="text-sm font-bold text-gray-900 mb-3">高级配置</h4>
                      <div className="mb-4">
                        <label className="block text-sm font-semibold text-gray-700 mb-1">
                          自定义工具配置 (MCP Servers)
                        </label>
                        <textarea
                          value={formData.custom_tools || ''}
                          onChange={(e) => setFormData({ ...formData, custom_tools: e.target.value })}
                          className={`w-full px-3 py-2 border rounded-lg text-sm font-mono ${
                            formErrors.custom_tools ? 'border-red-500' : 'border-gray-300'
                          }`}
                          rows={8}
                          placeholder={`{
  "mcp_server_name": {
    "url": "http://localhost:3000",
    "config": {
      "api_key": "...",
      "timeout": 30
    }
  }
}`}
                        />
                        {formErrors.custom_tools && (
                          <p className="text-xs text-red-500 mt-1">{formErrors.custom_tools}</p>
                        )}
                        <p className="text-xs text-gray-500 mt-1">
                          MCP (Model Context Protocol) 服务器配置，JSON 格式。定义自定义工具服务器。
                        </p>
                      </div>
                      <div className="mb-4">
                        <label className="block text-sm font-semibold text-gray-700 mb-1">
                          工作流配置
                        </label>
                        <textarea
                          value={formData.workflow || ''}
                          onChange={(e) => setFormData({ ...formData, workflow: e.target.value })}
                          className={`w-full px-3 py-2 border rounded-lg text-sm font-mono ${
                            formErrors.workflow ? 'border-red-500' : 'border-gray-300'
                          }`}
                          rows={8}
                          placeholder={`{
  "steps": [
    {"name": "step1", "action": "...", "condition": "..."},
    {"name": "step2", "action": "...", "condition": "..."}
  ],
  "conditions": {
    "on_success": "...",
    "on_failure": "..."
  }
}`}
                        />
                        {formErrors.workflow && (
                          <p className="text-xs text-red-500 mt-1">{formErrors.workflow}</p>
                        )}
                        <p className="text-xs text-gray-500 mt-1">
                          工作流定义，JSON 格式。定义任务执行的步骤和条件。
                        </p>
                      </div>
                    </div>

                    {/* 可见性设置 */}
                    <div>
                      <h4 className="text-sm font-bold text-gray-900 mb-3">可见性设置</h4>
                      <div className="space-y-2">
                        <label className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={formData.is_public || false}
                            onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                            className="rounded"
                          />
                          <span className="text-sm text-gray-700">公开此场景</span>
                        </label>
                        <p className="text-xs text-gray-500 ml-6">
                          公开的场景可以被所有用户查看和使用，私有场景仅创建者可见
                        </p>
                        <label className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={formData.is_default || false}
                            onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                            className="rounded"
                            disabled={!showCreateDialog && !selectedItem?.is_default} // 编辑模式下，只有已经是默认场景的才能修改
                          />
                          <span className="text-sm text-gray-700">系统默认场景（仅管理员）</span>
                        </label>
                        <p className="text-xs text-gray-500 ml-6">
                          标识为系统默认场景，只有管理员可以设置
                        </p>
                      </div>
                    </div>
                  </>
                )}

                {/* Action Buttons */}
                <div className="flex items-center justify-end space-x-3 pt-4 border-t">
                  <button
                    onClick={() => {
                      setShowCreateDialog(false);
                      setShowEditDialog(false);
                      setSelectedItem(null);
                      setFormData({});
                      setFormErrors({});
                    }}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-semibold"
                    disabled={submitting}
                  >
                    取消
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submitting ? '提交中...' : showCreateDialog ? '创建' : '保存'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* View Dialog */}
        {showViewDialog && selectedItem && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold">{selectedItem.name}</h3>
              <button
                onClick={() => {
                  setShowViewDialog(false);
                  setSelectedItem(null);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="space-y-6">
              {/* 基本信息 */}
              <div className="border-b border-gray-200 pb-4">
                <h4 className="text-sm font-bold text-gray-900 mb-3">基本信息</h4>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-semibold text-gray-500 uppercase">ID</label>
                    <p className="text-sm text-gray-900 mt-1 font-mono">
                      {selectedItem.id}  {/* 使用整数ID */}
                    </p>
                  </div>
                  
                  {selectedItem.description && (
                    <div>
                      <label className="text-xs font-semibold text-gray-500 uppercase">描述</label>
                      <p className="text-sm text-gray-900 mt-1">{selectedItem.description}</p>
                    </div>
                  )}
                  
                  {selectedItem.category && (
                    <div>
                      <label className="text-xs font-semibold text-gray-500 uppercase">分类</label>
                      <p className="text-sm text-gray-900 mt-1">{selectedItem.category}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* 系统提示词/内容 */}
              <div className="border-b border-gray-200 pb-4">
                <h4 className="text-sm font-bold text-gray-900 mb-3">
                  {activeTab === 'prompts' ? '提示词内容' : activeTab === 'skills' ? '技能内容' : '系统提示词'}
                </h4>
                <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-x-auto max-h-96 overflow-y-auto font-mono whitespace-pre-wrap">
                  {activeTab === 'prompts' 
                    ? selectedItem.content 
                    : activeTab === 'skills' 
                    ? selectedItem.skill_content 
                    : selectedItem.system_prompt}
                </pre>
              </div>

              {/* 业务场景特有字段 */}
              {activeTab === 'scenarios' && (
                <>
                  <div className="border-b border-gray-200 pb-4">
                    <h4 className="text-sm font-bold text-gray-900 mb-3">工具和模型配置</h4>
                    <div className="space-y-3">
                      {selectedItem.allowed_tools && selectedItem.allowed_tools.length > 0 && (
                        <div>
                          <label className="text-xs font-semibold text-gray-500 uppercase">允许的工具</label>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {selectedItem.allowed_tools.map((tool: string, idx: number) => (
                              <span key={idx} className="px-2 py-1 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium">
                                {tool}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {selectedItem.recommended_model && (
                        <div>
                          <label className="text-xs font-semibold text-gray-500 uppercase">推荐模型</label>
                          <p className="text-sm text-gray-900 mt-1 font-mono">{selectedItem.recommended_model}</p>
                        </div>
                      )}
                      
                      {selectedItem.permission_mode && (
                        <div>
                          <label className="text-xs font-semibold text-gray-500 uppercase">权限模式</label>
                          <p className="text-sm text-gray-900 mt-1 font-mono">{selectedItem.permission_mode}</p>
                        </div>
                      )}
                      
                      {selectedItem.max_turns && (
                        <div>
                          <label className="text-xs font-semibold text-gray-500 uppercase">最大对话轮数</label>
                          <p className="text-sm text-gray-900 mt-1">{selectedItem.max_turns}</p>
                        </div>
                      )}
                      
                      {selectedItem.work_dir && (
                        <div>
                          <label className="text-xs font-semibold text-gray-500 uppercase">工作目录</label>
                          <p className="text-sm text-gray-900 mt-1 font-mono break-all">{selectedItem.work_dir}</p>
                        </div>
                      )}
                      
                      {selectedItem.skills && selectedItem.skills.length > 0 && (
                        <div>
                          <label className="text-xs font-semibold text-gray-500 uppercase">关联技能</label>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {selectedItem.skills.map((skillId: string, idx: number) => {
                              // 查找skill对象并显示名称
                              const skillObj = skills.find(s => String(s.id) === String(skillId));
                              const displayName = skillObj ? skillObj.name : skillId;
                              return (
                                <span key={idx} className="px-2 py-1 bg-purple-50 text-purple-700 rounded-lg text-xs font-medium">
                                  {displayName}
                                </span>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {selectedItem.custom_tools && (
                    <div className="border-b border-gray-200 pb-4">
                      <h4 className="text-sm font-bold text-gray-900 mb-3">自定义工具配置 (MCP Servers)</h4>
                      <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-x-auto max-h-64 overflow-y-auto font-mono">
                        {JSON.stringify(selectedItem.custom_tools, null, 2)}
                      </pre>
                    </div>
                  )}

                  {selectedItem.workflow && (
                    <div className="border-b border-gray-200 pb-4">
                      <h4 className="text-sm font-bold text-gray-900 mb-3">工作流配置</h4>
                      <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-x-auto max-h-64 overflow-y-auto font-mono">
                        {JSON.stringify(selectedItem.workflow, null, 2)}
                      </pre>
                    </div>
                  )}
                </>
              )}

              {/* 技能特有字段 */}
              {activeTab === 'skills' && selectedItem.skill_config && (
                <div className="border-b border-gray-200 pb-4">
                  <h4 className="text-sm font-bold text-gray-900 mb-3">技能配置</h4>
                  <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-x-auto max-h-64 overflow-y-auto font-mono">
                    {typeof selectedItem.skill_config === 'string' 
                      ? selectedItem.skill_config 
                      : JSON.stringify(selectedItem.skill_config, null, 2)}
                  </pre>
                </div>
              )}

              {/* 元数据 */}
              <div className="border-b border-gray-200 pb-4">
                <h4 className="text-sm font-bold text-gray-900 mb-3">元数据</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <label className="text-xs font-semibold text-gray-500 uppercase">可见性</label>
                    <div className="mt-1">
                      {selectedItem.is_public ? (
                        <span className="inline-flex items-center px-2 py-1 bg-green-50 text-green-700 rounded-lg text-xs font-medium">
                          <Eye size={12} className="mr-1" />
                          公开
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 bg-gray-50 text-gray-700 rounded-lg text-xs font-medium">
                          <EyeOff size={12} className="mr-1" />
                          私有
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {selectedItem.is_default !== undefined && (
                    <div>
                      <label className="text-xs font-semibold text-gray-500 uppercase">默认</label>
                      <div className="mt-1">
                        {selectedItem.is_default ? (
                          <span className="inline-flex items-center px-2 py-1 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium">
                            是
                          </span>
                        ) : (
                          <span className="text-xs text-gray-500">否</span>
                        )}
                      </div>
                    </div>
                  )}
                  
                  <div>
                    <label className="text-xs font-semibold text-gray-500 uppercase">使用次数</label>
                    <p className="text-sm text-gray-900 mt-1">{selectedItem.usage_count || 0}</p>
                  </div>
                  
                  {selectedItem.created_by && (
                    <div>
                      <label className="text-xs font-semibold text-gray-500 uppercase">创建者</label>
                      <p className="text-sm text-gray-900 mt-1">ID: {selectedItem.created_by}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* 时间信息 */}
              <div>
                <h4 className="text-sm font-bold text-gray-900 mb-3">时间信息</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <label className="text-xs font-semibold text-gray-500 uppercase">创建时间</label>
                    <p className="text-sm text-gray-900 mt-1">
                      {selectedItem.created_at ? new Date(selectedItem.created_at).toLocaleString('zh-CN') : '-'}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-gray-500 uppercase">更新时间</label>
                    <p className="text-sm text-gray-900 mt-1">
                      {selectedItem.updated_at ? new Date(selectedItem.updated_at).toLocaleString('zh-CN') : '-'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          </div>
        )}
      </div>
    </div>
  );
};
