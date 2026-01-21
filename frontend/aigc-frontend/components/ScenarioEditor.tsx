/**
 * Scenario Editor Component
 * 
 * 业务场景编辑页面，支持创建和编辑业务场景
 */
import React, { useState, useEffect } from 'react';
import { ArrowLeft, Save, X, ChevronDown, ChevronUp, Sparkles, CheckCircle2, Galaxy, Copy, Share2, Eye, EyeOff } from 'lucide-react';
import { SkillGalaxy } from './SkillGalaxy';
import { ToolSelector } from './ToolSelector';
import {
  platformService,
  BusinessScenario,
  BusinessScenarioCreate
} from '../services/platformService';
import { apiClient } from '../services/api';
import { authService } from '../services/authService';
import { UserRole } from '../types';

interface ScenarioEditorProps {
  scenarioId?: number; // 如果提供，则为编辑模式；否则为创建模式（使用整数ID）
  onBack: () => void; // 返回回调
  onSave?: () => void; // 保存成功后的回调
}

export const ScenarioEditor: React.FC<ScenarioEditorProps> = ({ 
  scenarioId, 
  onBack,
  onSave 
}) => {
  const isEditMode = !!scenarioId;
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 表单数据（移除 scenario_id 字段，使用自增整数 id）
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    system_prompt: '',
    allowed_tools: [] as string[],
    recommended_model: '',
    skills: [] as string[],
    custom_tools: '',
    workflow: '',
    permission_mode: '',
    max_turns: '',
    work_dir: '',
    is_public: false,
    is_default: false,
  });
  
  // 当前用户信息（用于判断是否是管理员）
  const [currentUser, setCurrentUser] = useState<{ role?: UserRole } | null>(null);
  const isAdmin = currentUser?.role === UserRole.Admin;
  
  // 表单错误
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  
  // 下拉框数据
  const [prompts, setPrompts] = useState<any[]>([]);
  const [skills, setSkills] = useState<any[]>([]);
  const [selectedPromptId, setSelectedPromptId] = useState<string>('');
  const [useCustomPrompt, setUseCustomPrompt] = useState<boolean>(false);
  const [expandedSkills, setExpandedSkills] = useState<Set<string>>(new Set()); // 展开的技能ID集合
  const [showGalaxy, setShowGalaxy] = useState(false); // 是否显示银河视图
  
  // 加载当前用户信息
  useEffect(() => {
    const loadCurrentUser = async () => {
      const result = await authService.getCurrentUser();
      if (result.success && result.data) {
        const roleId = result.data.role_id;
        const username = result.data.username;
        const isAdminRole = roleId === 1 || String(roleId) === '1' || 
                           (roleId == null && username?.toLowerCase() === 'admin');
        setCurrentUser({
          role: isAdminRole ? UserRole.Admin : UserRole.User
        });
      }
    };
    loadCurrentUser();
  }, []);
  
  // 加载数据
  useEffect(() => {
    loadData();
  }, [scenarioId]);
  
  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 加载系统提示词列表
      const promptsData = await platformService.listSystemPrompts();
      setPrompts(promptsData);
      
      // 加载技能列表
      const skillsData = await platformService.listSkills();
      setSkills(skillsData);
      
      // 如果是编辑模式，加载业务场景数据
      if (scenarioId) {
        const scenario = await platformService.getScenario(scenarioId);
        if (scenario) {
          // 检查系统提示词是否匹配已有的提示词
          const matchingPrompt = promptsData.find(p => p.content === scenario.system_prompt);
          const promptId = matchingPrompt ? matchingPrompt.id : undefined;  // 使用整数ID
          
          setFormData({
            name: scenario.name || '',
            description: scenario.description || '',
            system_prompt: scenario.system_prompt || '',
            allowed_tools: scenario.allowed_tools ? scenario.allowed_tools : [],
            recommended_model: scenario.recommended_model || '',
            skills: scenario.skills ? scenario.skills : [],
            custom_tools: scenario.custom_tools ? JSON.stringify(scenario.custom_tools, null, 2) : '',
            workflow: scenario.workflow ? JSON.stringify(scenario.workflow, null, 2) : '',
            permission_mode: scenario.permission_mode || '',
            max_turns: scenario.max_turns || '',
            work_dir: scenario.work_dir || '',
            is_public: scenario.is_public || false,
            is_default: scenario.is_default || false,
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
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载数据失败');
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    // 移除 scenario_id 验证，使用自增整数 id
    if (!formData.name?.trim()) {
      errors.name = '名称不能为空';
    }
    // 系统提示词：如果使用自定义提示词，需要检查 formData.system_prompt；如果使用下拉框选择，需要检查 selectedPromptId
    if (useCustomPrompt && !formData.system_prompt?.trim()) {
      errors.system_prompt = '系统提示词不能为空';
    } else if (!useCustomPrompt && !selectedPromptId) {
      errors.system_prompt = '请选择系统提示词';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  const handleDuplicate = async () => {
    if (!scenarioId) return;
    
    try {
      const newName = prompt('请输入新场景名称（留空使用默认名称）:');
      
      const response = await apiClient.post(
        `/api/v1/platform/scenarios/${scenarioId}/duplicate`,
        {
          new_name: newName || undefined  // 移除 new_scenario_id，使用自增ID
        }
      );
      
      if (response.error) {
        alert('复制失败: ' + response.error);
      } else {
        alert('场景复制成功！');
        if (onSave) {
          onSave();
        }
        onBack();
      }
    } catch (err) {
      console.error('复制场景失败:', err);
      alert('复制失败: ' + (err instanceof Error ? err.message : '未知错误'));
    }
  };

  const handleToggleShare = async () => {
    if (!scenarioId) return;
    
    const makePublic = !formData.is_public;
    const confirmText = makePublic
      ? '确定要分享这个场景吗？其他用户将可以看到和使用它。'
      : '确定要取消分享这个场景吗？其他用户将无法再看到它。';
    
    if (!confirm(confirmText)) {
      return;
    }
    
    try {
      const response = await apiClient.post(
        `/api/v1/platform/scenarios/${scenarioId}/share`,
        { make_public: makePublic }
      );
      
      if (response.error) {
        alert('操作失败: ' + response.error);
      } else {
        setFormData({ ...formData, is_public: makePublic });
        alert(makePublic ? '场景已分享' : '已取消分享');
      }
    } catch (err) {
      console.error('分享场景失败:', err);
      alert('操作失败: ' + (err instanceof Error ? err.message : '未知错误'));
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }
    
    setSubmitting(true);
    setError(null);
    
    try {
      // allowed_tools 现在是数组，直接使用
      const allowedTools = Array.isArray(formData.allowed_tools) && formData.allowed_tools.length > 0
        ? formData.allowed_tools
        : undefined;
      // skills 现在已经是数组格式
      const skillsArray = Array.isArray(formData.skills) && formData.skills.length > 0
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
      
      if (isEditMode) {
        await platformService.updateScenario(scenarioId!, {
          name: formData.name.trim(),
          description: formData.description?.trim() || undefined,
          system_prompt: systemPrompt,
          allowed_tools: allowedTools,
          recommended_model: formData.recommended_model?.trim() || undefined,
          skills: skillsArray,
          custom_tools: customTools,
          workflow: workflow,
          permission_mode: formData.permission_mode?.trim() || undefined,
          max_turns: formData.max_turns ? parseInt(String(formData.max_turns)) : undefined,
          work_dir: formData.work_dir?.trim() || undefined,
          is_public: formData.is_public || false,
          is_default: isAdmin ? (formData.is_default !== undefined ? formData.is_default : undefined) : undefined, // 只有管理员可以设置
        });
      } else {
        await platformService.createScenario({
          // 移除 scenario_id 字段，使用自增整数 id
          name: formData.name.trim(),
          description: formData.description?.trim() || undefined,
          system_prompt: systemPrompt,
          allowed_tools: allowedTools,
          recommended_model: formData.recommended_model?.trim() || undefined,
          skills: skillsArray,
          custom_tools: customTools,
          workflow: workflow,
          permission_mode: formData.permission_mode?.trim() || undefined,
          max_turns: formData.max_turns ? parseInt(String(formData.max_turns)) : undefined,
          work_dir: formData.work_dir?.trim() || undefined,
          is_public: formData.is_public || false,
          is_default: isAdmin ? formData.is_default : false, // 只有管理员可以设置
        });
      }
      
      // 保存成功，调用回调
      if (onSave) {
        onSave();
      }
      onBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败');
      console.error('Submit error:', err);
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }
  
  return (
    <>
      {/* 银河视图 */}
      {showGalaxy && (
        <SkillGalaxy
          skills={skills}
          selectedSkills={Array.isArray(formData.skills) ? formData.skills : []}
          onSelect={(skillId) => {
            const current = Array.isArray(formData.skills) ? formData.skills : [];
            if (!current.includes(skillId)) {
              setFormData({ ...formData, skills: [...current, skillId] });
            }
          }}
          onDeselect={(skillId) => {
            const current = Array.isArray(formData.skills) ? formData.skills : [];
            setFormData({ ...formData, skills: current.filter((s: string) => s !== skillId) });
          }}
          onClose={() => setShowGalaxy(false)}
        />
      )}

      <div className="flex-1 overflow-y-auto bg-white custom-scrollbar">
      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* 头部 */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft size={20} className="text-gray-600" />
            </button>
            <div>
              <h1 className="text-2xl font-black text-gray-900">
                {isEditMode ? '编辑业务场景' : '创建业务场景'}
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                {isEditMode ? '修改业务场景配置' : '创建新的业务场景配置'}
              </p>
            </div>
          </div>
          
          {/* 操作按钮 */}
          {isEditMode && (
            <div className="flex items-center space-x-2">
              <button
                onClick={handleDuplicate}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors flex items-center space-x-2"
                title="复制场景"
              >
                <Copy size={16} />
                <span>复制</span>
              </button>
              <button
                onClick={handleToggleShare}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors flex items-center space-x-2 ${
                  formData.is_public
                    ? 'text-green-700 bg-green-50 hover:bg-green-100'
                    : 'text-gray-700 bg-gray-100 hover:bg-gray-200'
                }`}
                title={formData.is_public ? '取消分享' : '分享场景'}
              >
                {formData.is_public ? <EyeOff size={16} /> : <Share2 size={16} />}
                <span>{formData.is_public ? '已分享' : '分享'}</span>
              </button>
            </div>
          )}
        </div>
        
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
            {error}
          </div>
        )}
        
        {/* 表单 */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="p-6 space-y-6">
            {/* 基本信息 */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">基本信息</h3>
              
              <div className="space-y-4">
                {/* 移除场景ID输入框，使用自增整数ID */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">
                    名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className={`w-full px-3 py-2 border rounded-lg text-sm ${
                      formErrors.name ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="例如: 默认业务场景"
                  />
                  {formErrors.name && (
                    <p className="text-xs text-red-500 mt-1">{formErrors.name}</p>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">描述</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    placeholder="业务场景的详细描述"
                  />
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="is_public"
                      checked={formData.is_public}
                      onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                      className="rounded"
                    />
                    <label htmlFor="is_public" className="text-sm text-gray-700">
                      公开（其他用户可见）
                    </label>
                  </div>
                  
                  {isAdmin && (
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="is_default"
                        checked={formData.is_default}
                        onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                        className="rounded"
                      />
                      <label htmlFor="is_default" className="text-sm text-gray-700">
                        系统默认场景（仅管理员）
                      </label>
                      <span className="text-xs text-gray-500">标识为系统默认场景</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            {/* 核心配置 */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">核心配置</h3>
              
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
                  <select
                    value={selectedPromptId}
                    onChange={(e) => {
                      const promptId = e.target.value;
                      setSelectedPromptId(promptId);
                      if (promptId) {
                        const selectedPrompt = prompts.find(p => p.id === Number(promptId));  // 使用整数ID
                        if (selectedPrompt) {
                          setFormData({ ...formData, system_prompt: selectedPrompt.content });
                        }
                      } else {
                        setFormData({ ...formData, system_prompt: '' });
                      }
                    }}
                    className={`w-full px-3 py-2 border rounded-lg text-sm ${
                      formErrors.system_prompt ? 'border-red-500' : 'border-gray-300'
                    }`}
                  >
                    <option value="">-- 请选择系统提示词 --</option>
                    {prompts.map((prompt) => (
                      <option key={prompt.id} value={String(prompt.id)}>  {/* 使用整数ID */}
                        {prompt.name} {prompt.is_default ? '(默认)' : ''}
                      </option>
                    ))}
                  </select>
                ) : (
                  <textarea
                    value={formData.system_prompt}
                    onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                    rows={8}
                    className={`w-full px-3 py-2 border rounded-lg text-sm font-mono ${
                      formErrors.system_prompt ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="输入自定义系统提示词..."
                  />
                )}
                {formErrors.system_prompt && (
                  <p className="text-xs text-red-500 mt-1">{formErrors.system_prompt}</p>
                )}
              </div>
            </div>
            
            {/* 工具和模型配置 */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">工具和模型配置</h3>

              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-2">允许的工具</label>
                <ToolSelector
                  selectedTools={Array.isArray(formData.allowed_tools) ? formData.allowed_tools : []}
                  onChange={(tools) => setFormData({ ...formData, allowed_tools: tools })}
                  category="all"
                  multiSelect={true}
                  className="border border-gray-200 rounded-lg p-4"
                />
                <p className="text-xs text-gray-500 mt-2">
                  {Array.isArray(formData.allowed_tools) && formData.allowed_tools.length === 0
                    ? '留空表示使用默认工具'
                    : `已选择 ${formData.allowed_tools.length} 个工具`
                  }
                </p>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-1">推荐模型</label>
                <input
                  type="text"
                  value={formData.recommended_model}
                  onChange={(e) => setFormData({ ...formData, recommended_model: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  placeholder="例如: claude-3-5-sonnet-20241022"
                />
                <p className="text-xs text-gray-500 mt-1">建议使用的 Claude 模型，留空使用系统默认</p>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-1">权限模式</label>
                <select
                  value={formData.permission_mode}
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
                  value={formData.max_turns}
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
                  value={formData.work_dir}
                  onChange={(e) => setFormData({ ...formData, work_dir: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  placeholder="例如: /path/to/workdir"
                />
                <p className="text-xs text-gray-500 mt-1">Agent 的工作目录路径，留空使用系统默认</p>
              </div>
            </div>
            
            {/* 技能配置 */}
            <div className="border-b border-gray-200 pb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900">技能配置</h3>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => setShowGalaxy(true)}
                    className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl"
                  >
                    <Sparkles size={16} />
                    <span className="text-sm font-semibold">银河视图</span>
                  </button>
                  <div className="flex items-center space-x-2 px-3 py-1.5 bg-blue-50 rounded-full border border-blue-200">
                    <Sparkles size={14} className="text-blue-600 animate-pulse" />
                    <span className="text-sm font-bold text-blue-600">
                      已选择 <span className="text-blue-700">{Array.isArray(formData.skills) ? formData.skills.length : 0}</span> 个技能
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-3">关联技能</label>
                {skills.length === 0 ? (
                  <div className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm min-h-[120px] flex items-center justify-center text-gray-500">
                    正在加载技能列表...
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[600px] overflow-y-auto custom-scrollbar pr-2">
                    {skills.map((skill) => {
                      // 使用技能名称而不是ID进行比较（数据库现在存储的是名称数组）
                      const isSelected = Array.isArray(formData.skills) && formData.skills.includes(skill.name);
                      const isExpanded = expandedSkills.has(skill.name);
                      const skillContent = skill.skill_content || skill.description || '暂无详细内容';
                      const previewContent = skillContent.length > 150 ? skillContent.substring(0, 150) + '...' : skillContent;

                      return (
                        <div
                          key={skill.id}  // 使用整数ID作为key
                          className={`relative group rounded-xl border-2 transition-all duration-300 overflow-hidden ${
                            isSelected
                              ? 'bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-400 shadow-lg shadow-blue-200/50'
                              : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-md'
                          }`}
                        >
                          {/* 闪光点效果 */}
                          {isSelected && (
                            <div className="absolute inset-0 pointer-events-none">
                              <div className="absolute top-2 right-2 w-2 h-2 bg-blue-500 rounded-full animate-ping opacity-75"></div>
                              <div className="absolute top-2 right-2 w-2 h-2 bg-blue-500 rounded-full"></div>
                            </div>
                          )}

                          {/* 卡片头部 - 可点击展开/收缩 */}
                          <div
                            className="flex items-center space-x-3 p-4 cursor-pointer"
                            onClick={() => {
                              const newExpanded = new Set(expandedSkills);
                              if (isExpanded) {
                                newExpanded.delete(skill.name);
                              } else {
                                newExpanded.add(skill.name);
                              }
                              setExpandedSkills(newExpanded);
                            }}
                          >
                            {/* 选中复选框 */}
                            <div
                              className="flex-shrink-0"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={(e) => {
                                  const current = Array.isArray(formData.skills) ? formData.skills : [];
                                  if (e.target.checked) {
                                    setFormData({ ...formData, skills: [...current, skill.name] });  // 使用技能名称
                                    // 选中后自动展开
                                    const newExpanded = new Set(expandedSkills);
                                    newExpanded.add(skill.name);
                                    setExpandedSkills(newExpanded);
                                  } else {
                                    setFormData({ ...formData, skills: current.filter((s: string) => s !== skill.name) });  // 使用技能名称
                                    // 取消选中后自动收缩
                                    const newExpanded = new Set(expandedSkills);
                                    newExpanded.delete(skill.name);
                                    setExpandedSkills(newExpanded);
                                  }
                                }}
                                className="w-5 h-5 rounded border-2 border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 cursor-pointer transition-all"
                                style={{
                                  accentColor: isSelected ? '#2563eb' : undefined
                                }}
                              />
                            </div>
                            
                            {/* 技能信息 */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-2 mb-1">
                                <h4 className={`text-sm font-bold ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                                  {skill.name}
                                </h4>
                                {isSelected && (
                                  <CheckCircle2 size={16} className="text-blue-600 flex-shrink-0" />
                                )}
                                {skill.category && (
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                                    isSelected 
                                      ? 'bg-blue-200 text-blue-800' 
                                      : 'bg-gray-100 text-gray-600'
                                  }`}>
                                    {skill.category}
                                  </span>
                                )}
                              </div>
                              <p className={`text-xs ${isSelected ? 'text-blue-700' : 'text-gray-500'} line-clamp-2`}>
                                {skill.description || '暂无描述'}
                              </p>
                            </div>
                            
                            {/* 展开/收缩图标 */}
                            <div className="flex-shrink-0">
                              {isExpanded ? (
                                <ChevronUp size={20} className={`${isSelected ? 'text-blue-600' : 'text-gray-400'} transition-transform`} />
                              ) : (
                                <ChevronDown size={20} className={`${isSelected ? 'text-blue-600' : 'text-gray-400'} transition-transform`} />
                              )}
                            </div>
                          </div>
                          
                          {/* 展开的内容区域 */}
                          {isExpanded && (
                            <div className="px-4 pb-4 border-t border-gray-200/50 animate-in slide-in-from-top-2 duration-300">
                              <div className="pt-4 space-y-3">
                                {skill.description && (
                                  <div>
                                    <h5 className="text-xs font-semibold text-gray-700 mb-1">描述</h5>
                                    <p className="text-xs text-gray-600 leading-relaxed">{skill.description}</p>
                                  </div>
                                )}
                                
                                {skillContent && (
                                  <div>
                                    <h5 className="text-xs font-semibold text-gray-700 mb-1">技能内容</h5>
                                    <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                                      <p className="text-xs text-gray-700 leading-relaxed whitespace-pre-wrap font-mono">
                                        {isExpanded ? skillContent : previewContent}
                                      </p>
                                    </div>
                                  </div>
                                )}
                                
                                {skill.skill_config && (
                                  <div>
                                    <h5 className="text-xs font-semibold text-gray-700 mb-1">配置信息</h5>
                                    <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                                      <pre className="text-xs text-gray-700 overflow-x-auto">
                                        {typeof skill.skill_config === 'string' 
                                          ? skill.skill_config 
                                          : JSON.stringify(skill.skill_config, null, 2)}
                                      </pre>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
                <p className="text-xs text-gray-500 mt-3">
                  {Array.isArray(formData.skills) && formData.skills.length === 0 
                    ? '（留空表示不限制技能使用）' 
                    : '点击技能卡片可查看详情，选中后会自动展开'}
                </p>
              </div>
            </div>
            
            {/* 高级配置 */}
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-4">高级配置</h3>
              
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-1">自定义工具配置 (JSON)</label>
                <textarea
                  value={formData.custom_tools}
                  onChange={(e) => setFormData({ ...formData, custom_tools: e.target.value })}
                  rows={6}
                  className={`w-full px-3 py-2 border rounded-lg text-sm font-mono ${
                    formErrors.custom_tools ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder='{"tool_name": {"param": "value"}}'
                />
                {formErrors.custom_tools && (
                  <p className="text-xs text-red-500 mt-1">{formErrors.custom_tools}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">自定义工具配置，JSON 格式，留空则不使用</p>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-700 mb-1">工作流配置 (JSON)</label>
                <textarea
                  value={formData.workflow}
                  onChange={(e) => setFormData({ ...formData, workflow: e.target.value })}
                  rows={6}
                  className={`w-full px-3 py-2 border rounded-lg text-sm font-mono ${
                    formErrors.workflow ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder='{"step1": {"action": "value"}}'
                />
                {formErrors.workflow && (
                  <p className="text-xs text-red-500 mt-1">{formErrors.workflow}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">工作流配置，JSON 格式，留空则不使用</p>
              </div>
            </div>
          </div>
          
          {/* 底部操作按钮 */}
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-end space-x-3">
            <button
              onClick={onBack}
              disabled={submitting}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-semibold disabled:opacity-50"
            >
              取消
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>保存中...</span>
                </>
              ) : (
                <>
                  <Save size={16} />
                  <span>保存</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
    </>
  );
};
