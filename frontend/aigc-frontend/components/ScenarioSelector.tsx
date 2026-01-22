/**
 * 场景选择器组件（支持多选）
 * 
 * Phase 2: SCENARIO-004
 * 功能：支持用户选择多个场景
 */
import React, { useState, useEffect } from 'react';
import { Check, X } from 'lucide-react';
import { platformService, BusinessScenario } from '../services/platformService';

export interface ScenarioSelectorProps {
  userId: number;
  selectedScenarioIds: number[];  // 改为整数ID数组
  onSelectionChange: (scenarioIds: number[]) => void;
  onSave?: (scenarioIds: number[]) => Promise<void>;
}

export const ScenarioSelector: React.FC<ScenarioSelectorProps> = ({
  userId,
  selectedScenarioIds,
  onSelectionChange,
  onSave
}) => {
  const [scenarios, setScenarios] = useState<BusinessScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [localSelected, setLocalSelected] = useState<number[]>(selectedScenarioIds);  // 改为整数ID数组
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadScenarios();
  }, []);

  useEffect(() => {
    setLocalSelected(selectedScenarioIds);
  }, [selectedScenarioIds]);

  const loadScenarios = async () => {
    try {
      setLoading(true);
      setError(null);
      const availableScenarios = await platformService.getAvailableScenarios();
      setScenarios(availableScenarios);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载场景失败');
      console.error('Failed to load scenarios:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleScenario = (scenarioId: number) => {  // 改为整数ID
    const newSelected = localSelected.includes(scenarioId)
      ? localSelected.filter(id => id !== scenarioId)
      : [...localSelected, scenarioId];
    
    setLocalSelected(newSelected);
    onSelectionChange(newSelected);
  };

  const handleSave = async () => {
    if (!onSave) return;
    
    setIsSaving(true);
    try {
      await onSave(localSelected);
    } catch (err) {
      console.error('保存场景配置失败:', err);
      alert('保存失败: ' + (err instanceof Error ? err.message : '未知错误'));
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-500">
        加载场景中...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-500">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-600 mb-3">
        选择你需要的场景（可多选）。系统会根据你的选择组合场景能力。
      </div>
      
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {scenarios.map((scenario) => {
          const isSelected = localSelected.includes(scenario.id);  // 使用整数ID
          
          return (
            <div
              key={scenario.id}  // 使用整数ID作为key
              onClick={() => handleToggleScenario(scenario.id)}  // 使用整数ID
              className={`
                p-3 rounded-lg border cursor-pointer transition-all
                ${isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }
              `}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <div className={`
                      w-5 h-5 rounded border-2 flex items-center justify-center
                      ${isSelected
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300'
                      }
                    `}>
                      {isSelected && <Check size={12} className="text-white" />}
                    </div>
                    <h3 className="font-semibold text-gray-900">{scenario.name}</h3>
                  </div>
                  {scenario.description && (
                    <p className="text-sm text-gray-600 mt-1 ml-7">
                      {scenario.description}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {scenarios.length === 0 && (
        <div className="p-4 text-center text-gray-500">
          暂无可用场景
        </div>
      )}

      {onSave && (
        <div className="flex justify-end space-x-2 pt-4 border-t">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? '保存中...' : '保存配置'}
          </button>
        </div>
      )}

      {localSelected.length > 0 && (
        <div className="text-sm text-gray-600 pt-2 border-t">
          已选择 {localSelected.length} 个场景
        </div>
      )}
    </div>
  );
};
