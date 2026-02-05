/**
 * Add Skill Modal
 * 添加技能模态框 - 提供三种方式：对话创建、GitHub 拉取、上传 ZIP
 * Apple Design Style - 简洁无图标
 */
import React from 'react';
import { X } from 'lucide-react';

interface AddSkillModalProps {
  onClose: () => void;
  onSelectMode: (mode: 'github' | 'upload' | 'create') => void;
}

export const AddSkillModal: React.FC<AddSkillModalProps> = ({ onClose, onSelectMode }) => {
  const modes = [
    {
      id: 'create' as const,
      title: '对话创建',
      description: '与 AI 对话，智能生成专业技能',
      color: 'blue'
    },
    {
      id: 'github' as const,
      title: 'GitHub 拉取',
      description: '从 GitHub 仓库快速导入技能',
      color: 'purple'
    },
    {
      id: 'upload' as const,
      title: '上传 ZIP',
      description: '上传本地技能压缩包',
      color: 'green'
    }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="bg-white rounded-[32px] p-10 max-w-2xl w-full mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">添加技能</h2>
            <p className="text-gray-500 text-sm mt-1">选择创建方式</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors"
          >
            <X size={18} className="text-gray-600" />
          </button>
        </div>

        {/* Mode Selection */}
        <div className="space-y-3">
          {modes.map((mode) => (
            <button
              key={mode.id}
              onClick={() => onSelectMode(mode.id)}
              className="w-full group p-5 rounded-2xl border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all duration-200 text-left"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                {mode.title}
              </h3>
              <p className="text-sm text-gray-500">
                {mode.description}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
