/**
 * 用户设置页面
 *
 * 集成：
 * 1. 场景选择器（ScenarioSelector）
 * 2. 用户自定义Prompt编辑器（UserPromptEditor）
 * 3. 用户偏好查看（UserPreferences）
 * 4. 工具配置（ToolSelector）
 */
import React, { useState, useEffect } from 'react';
import { Settings, Sparkles, FileText, User, ChevronRight, Wrench } from 'lucide-react';
import { ScenarioSelector } from './ScenarioSelector';
import { UserPromptEditor } from './UserPromptEditor';
import { UserPreferences } from './UserPreferences';
import { ToolSelector } from './ToolSelector';
import { platformService } from '../services/platformService';
import { authService } from '../services/authService';

type SettingsTab = 'scenarios' | 'prompt' | 'preferences' | 'tools';

export const UserSettings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('scenarios');
  const [userId, setUserId] = useState<number | null>(null);
  const [selectedScenarioIds, setSelectedScenarioIds] = useState<number[]>([]);  // 改为整数ID数组
  const [userCustomPrompt, setUserCustomPrompt] = useState<string>('');
  const [selectedTools, setSelectedTools] = useState<string[]>([]);  // 用户选择的工具
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserInfo();
  }, []);

  useEffect(() => {
    if (userId) {
      loadUserConfig();
    }
  }, [userId]);

  const loadUserInfo = async () => {
    try {
      const result = await authService.getCurrentUser();
      if (result.success && result.data && result.data.id) {
        setUserId(result.data.id);
      }
    } catch (err) {
      console.error('获取用户信息失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadUserConfig = async () => {
    if (!userId) return;

    try {
      const config = await platformService.getUserScenarioConfig(userId);
      if (config) {
        setSelectedScenarioIds(config.scenario_ids || []);
        setUserCustomPrompt(config.user_custom_prompt || '');
      }

      // 单独加载用户工具配置
      const token = authService.getToken();
      if (token) {
        const response = await fetch(`/api/v1/platform/users/${userId}/config`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const userConfig = await response.json();
          if (userConfig.default_allowed_tools && Array.isArray(userConfig.default_allowed_tools)) {
            setSelectedTools(userConfig.default_allowed_tools);
          }
        }
      }
    } catch (err) {
      console.error('加载用户配置失败:', err);
    }
  };

  const handleSaveScenarios = async (scenarioIds: number[]) => {  // 改为整数ID数组
    if (!userId) return;
    
    try {
      await platformService.updateUserScenarioConfig(
        userId,
        scenarioIds,
        userCustomPrompt || undefined
      );
      setSelectedScenarioIds(scenarioIds);
      alert('场景配置已保存');
    } catch (err) {
      console.error('保存场景配置失败:', err);
      alert('保存失败: ' + (err instanceof Error ? err.message : '未知错误'));
      throw err;
    }
  };

  const handleSavePrompt = async (prompt: string) => {
    if (!userId) return;

    try {
      await platformService.updateUserScenarioConfig(
        userId,
        selectedScenarioIds,
        prompt || undefined
      );
      setUserCustomPrompt(prompt);
      alert('自定义规则已保存');
    } catch (err) {
      console.error('保存自定义规则失败:', err);
      alert('保存失败: ' + (err instanceof Error ? err.message : '未知错误'));
      throw err;
    }
  };

  const handleSaveTools = async (tools: string[]) => {
    if (!userId) return;

    try {
      // 保存工具配置到 user_configs 表
      const response = await fetch(`/api/v1/platform/users/${userId}/config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`,
        },
        body: JSON.stringify({
          default_allowed_tools: tools,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '保存失败');
      }

      setSelectedTools(tools);
      alert('工具配置已保存');
    } catch (err) {
      console.error('保存工具配置失败:', err);
      alert('保存失败: ' + (err instanceof Error ? err.message : '未知错误'));
      throw err;
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

  if (!userId) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500">请先登录</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'scenarios' as SettingsTab, label: '场景配置', icon: <Sparkles size={18} /> },
    { id: 'prompt' as SettingsTab, label: '自定义规则', icon: <FileText size={18} /> },
    { id: 'preferences' as SettingsTab, label: '我的偏好', icon: <User size={18} /> },
    { id: 'tools' as SettingsTab, label: '工具配置', icon: <Wrench size={18} /> },
  ];

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* 头部 */}
      <div className="border-b border-gray-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Settings className="text-white" size={20} />
            </div>
            <div>
              <h1 className="text-2xl font-black text-gray-900">用户设置</h1>
              <p className="text-sm text-gray-500 mt-1">配置你的场景、自定义规则和查看偏好</p>
            </div>
          </div>

          {/* 标签页 */}
          <div className="flex space-x-1 border-b border-gray-200">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  px-6 py-3 text-sm font-semibold transition-colors relative
                  ${activeTab === tab.id
                    ? 'text-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                  }
                `}
              >
                <div className="flex items-center space-x-2">
                  {tab.icon}
                  <span>{tab.label}</span>
                </div>
                {activeTab === tab.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">
          {activeTab === 'scenarios' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-4">场景配置</h2>
              <p className="text-sm text-gray-600 mb-6">
                选择你需要的场景（可多选）。系统会根据你的选择组合场景能力，让AI更好地理解你的需求。
              </p>
              <ScenarioSelector
                userId={userId}
                selectedScenarioIds={selectedScenarioIds}
                onSelectionChange={setSelectedScenarioIds}
                onSave={handleSaveScenarios}
              />
            </div>
          )}

          {activeTab === 'prompt' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-4">自定义规则</h2>
              <p className="text-sm text-gray-600 mb-6">
                在这里添加你的自定义规则和偏好，这些规则会与场景prompt合并，让AI更符合你的使用习惯。
              </p>
              <UserPromptEditor
                userId={userId}
                initialPrompt={userCustomPrompt}
                onSave={handleSavePrompt}
              />
            </div>
          )}

          {activeTab === 'preferences' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-4">我的偏好</h2>
              <p className="text-sm text-gray-600 mb-6">
                系统根据你的使用习惯和反馈自动学习的偏好信息。
              </p>
              <UserPreferences />
            </div>
          )}

          {activeTab === 'tools' && (
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-4">工具配置</h2>
              <p className="text-sm text-gray-600 mb-6">
                选择你需要的工具（可多选）。这些工具将作为你的默认工具集，可以在场景中进一步配置。
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <p className="text-sm text-blue-800">
                  💡 <strong>提示：</strong>这里配置的是你的默认工具集。场景配置中的工具会与这些工具合并使用。
                </p>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">已选择工具</span>
                  <button
                    onClick={() => handleSaveTools(selectedTools)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                  >
                    保存工具配置
                  </button>
                </div>
                <ToolSelector
                  selectedTools={selectedTools}
                  onChange={setSelectedTools}
                  category="all"
                  multiSelect={true}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
