/**
 * 用户自定义Prompt编辑器组件
 * 
 * Phase 2: CUSTOM-001 (前端部分)
 * 功能：用户可以在场景基础上添加自定义prompt
 */
import React, { useState, useEffect } from 'react';
import { Save, X } from 'lucide-react';
import { platformService } from '../services/platformService';

export interface UserPromptEditorProps {
  userId: number;
  initialPrompt?: string;
  onSave?: (prompt: string) => Promise<void>;
  onCancel?: () => void;
}

export const UserPromptEditor: React.FC<UserPromptEditorProps> = ({
  userId,
  initialPrompt = '',
  onSave,
  onCancel
}) => {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setPrompt(initialPrompt);
  }, [initialPrompt]);

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    
    try {
      if (onSave) {
        await onSave(prompt);
      } else {
        // 默认保存逻辑：更新用户场景配置中的 user_custom_prompt
        const config = await platformService.getUserScenarioConfig(userId);
        const scenarioIds = config?.scenario_ids || [];
        await platformService.updateUserScenarioConfig(
          userId,
          scenarioIds,
          prompt.trim() || undefined
        );
      }
      
      if (onCancel) {
        onCancel();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败');
      console.error('保存用户自定义prompt失败:', err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          用户自定义规则
        </label>
        <p className="text-xs text-gray-500 mb-3">
          在这里添加你的自定义规则和偏好，这些规则会与场景prompt合并。
        </p>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="例如：\n- 回答时使用简洁的语言\n- 优先使用图表展示数据\n- 技术问题需要提供代码示例"
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono"
          rows={8}
        />
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {error}
        </div>
      )}

      <div className="flex justify-end space-x-2">
        {onCancel && (
          <button
            onClick={onCancel}
            disabled={isSaving}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            取消
          </button>
        )}
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          <Save size={16} />
          <span>{isSaving ? '保存中...' : '保存'}</span>
        </button>
      </div>
    </div>
  );
};
