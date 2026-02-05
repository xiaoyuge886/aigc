/**
 * GitHub Skills Page
 * GitHub 技能拉取页面 - 全屏页面
 * Apple Design Style
 */
import React, { useState } from 'react';
import { Download, Loader2, AlertCircle, Check, X, ArrowLeft } from 'lucide-react';
import skillService from '../services/skillService';

interface GitHubSkillsPageProps {
  onClose: () => void;
  onSkillInstalled?: () => void;
}

export const GitHubSkillsPage: React.FC<GitHubSkillsPageProps> = ({ onClose, onSkillInstalled }) => {
  const [step, setStep] = useState<'input' | 'select' | 'installing' | 'success'>('input');
  const [repoUrl, setRepoUrl] = useState('');
  const [isLoadingSkills, setIsLoadingSkills] = useState(false);
  const [repoSkills, setRepoSkills] = useState<any[]>([]);
  const [installingSkill, setInstallingSkill] = useState<string | null>(null);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  // 从仓库 URL 获取技能列表
  const handleFetchSkills = async () => {
    if (!repoUrl.trim()) {
      setError('请输入仓库 URL');
      return;
    }

    setIsLoadingSkills(true);
    setError('');
    try {
      const skills = await skillService.listRepoSkills(repoUrl);
      setRepoSkills(skills);
      if (skills.length === 0) {
        setError('该仓库中没有找到技能文件');
      } else {
        setStep('select');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '获取技能列表失败');
    } finally {
      setIsLoadingSkills(false);
    }
  };

  // 安装技能
  const handleInstallSkill = async (skill: any) => {
    setInstallingSkill(skill.name);
    setError('');
    try {
      await skillService.installSkillFromGitHub({
        repo_url: repoUrl,
        skill_name: skill.name,
        subpath: skill.relative_path,
      });
      setSuccess(`技能 "${skill.name}" 已成功安装`);
      setStep('success');
      onSkillInstalled?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || '安装失败');
    } finally {
      setInstallingSkill(null);
    }
  };

  return (
    <div className="fixed inset-0 bg-white z-50 flex flex-col">
      {/* Header */}
      <header className="h-16 px-6 border-b border-gray-200 flex items-center justify-between bg-white">
        <div className="flex items-center space-x-4">
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors"
          >
            <X size={18} className="text-gray-600" />
          </button>
          <h1 className="text-lg font-semibold text-gray-900">GitHub 技能拉取</h1>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-10">
        <div className="max-w-3xl mx-auto">
          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl flex items-start gap-3">
              <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-700">{success}</p>
            </div>
          )}

          {/* Step 1: Input Repo URL */}
          {step === 'input' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">从 GitHub 拉取技能</h2>
                <p className="text-gray-500">输入 GitHub 仓库地址，系统将自动检测并拉取技能</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  GitHub 仓库 URL
                </label>
                <input
                  type="text"
                  placeholder="https://github.com/owner/repo"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleFetchSkills()}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  disabled={isLoadingSkills}
                />
                <p className="text-xs text-gray-500 mt-2">
                  示例：https://github.com/LeastBit/Claude_skills_zh-CN.git
                </p>
              </div>

              <button
                onClick={handleFetchSkills}
                disabled={isLoadingSkills || !repoUrl.trim()}
                className="w-full px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors font-medium"
              >
                {isLoadingSkills ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    获取技能列表...
                  </>
                ) : (
                  '获取技能列表'
                )}
              </button>
            </div>
          )}

          {/* Step 2: Select Skills */}
          {step === 'select' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    setStep('input');
                    setRepoSkills([]);
                  }}
                  className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                >
                  <ArrowLeft size={16} />
                  返回
                </button>
                <div className="flex-1" />
              </div>

              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  仓库中的技能
                </h2>
                <p className="text-sm text-gray-600">选择要安装的技能</p>
              </div>

              <div className="space-y-3">
                {repoSkills.map((skill) => (
                  <div
                    key={skill.name}
                    className="p-5 border border-gray-200 rounded-xl hover:border-blue-300 hover:bg-blue-50/30 transition-all"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 mb-1">{skill.name}</h3>
                        <p className="text-sm text-gray-600 mb-2">{skill.description}</p>
                        <p className="text-xs text-gray-500 font-mono">{skill.relative_path}</p>
                      </div>
                      <button
                        onClick={() => handleInstallSkill(skill)}
                        disabled={installingSkill === skill.name}
                        className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors text-sm font-medium whitespace-nowrap"
                      >
                        {installingSkill === skill.name ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            安装中...
                          </>
                        ) : (
                          <>
                            <Download className="w-4 h-4" />
                            安装
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 3: Installing */}
          {step === 'installing' && (
            <div className="flex flex-col items-center justify-center py-24">
              <Loader2 className="w-16 h-16 text-blue-600 animate-spin mb-6" />
              <p className="text-lg font-semibold text-gray-900 mb-2">正在安装技能...</p>
              <p className="text-sm text-gray-500">这可能需要几秒钟</p>
            </div>
          )}

          {/* Step 4: Success */}
          {step === 'success' && (
            <div className="flex flex-col items-center justify-center py-24">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
                <Check className="w-10 h-10 text-green-600" />
              </div>
              <p className="text-2xl font-semibold text-gray-900 mb-2">安装成功！</p>
              <p className="text-gray-500 mb-8">技能已添加到调试目录</p>
              <button
                onClick={onClose}
                className="px-8 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-medium"
              >
                完成
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
