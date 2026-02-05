/**
 * Skills Service
 * 技能市场服务 - 处理技能的增删改查和 GitHub 拉取
 */
import { apiClient } from './api';

// ==================== 类型定义 ====================

export interface Skill {
  id: number;
  name: string;
  description: string | null;
  status: 'draft' | 'testing' | 'published' | 'official' | 'archived';
  usage_count: number;
  author_id: number | null;
  is_official: boolean;
  source?: 'github' | 'conversation' | 'upload' | 'official';
  skill_path?: string;
  can_debug_online?: boolean;
  can_load_in_chat?: boolean;
  created_at: string;
  updated_at: string;
}

export interface SkillMarketResponse {
  skills: Skill[];
  total: number;
  page: number;
  page_size: number;
}

export interface GitHubRepo {
  name: string;
  full_name: string;
  description: string;
  url: string;
  clone_url: string;
  stars: number;
  language: string | null;
  updated_at: string | null;
}

export interface GitHubSkillItem {
  name: string;
  description: string;
  relative_path: string;
  has_config: boolean;
}

export interface InstallSkillRequest {
  repo_url: string;
  skill_name: string;
  subpath?: string;
  branch?: string;
}

export interface InstallSkillResponse {
  id: number;
  name: string;
  description: string | null;
  skill_path: string;
  status: string;
  author_id: number | null;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

// ==================== 技能市场 API ====================

/**
 * 获取技能市场列表
 */
export const getSkillMarket = async (params: {
  search?: string;
  sort?: 'latest' | 'popular';
  page?: number;
  page_size?: number;
  include_testing?: boolean;
}): Promise<SkillMarketResponse> => {
  const response = await apiClient.get('/api/v1/skills/market', params);
  return response.data;
};

/**
 * 获取我的技能列表
 */
export const getMySkills = async (params: {
  status_filter?: string;
}): Promise<{ skills: Skill[]; total: number }> => {
  const response = await apiClient.get('/api/v1/skills/my-skills', params);
  return response.data;
};

// ==================== GitHub 技能 API ====================

/**
 * 搜索 GitHub 仓库
 */
export const searchGitHubRepos = async (params: {
  query: string;
  limit?: number;
}): Promise<GitHubRepo[]> => {
  const response = await apiClient.get('/api/v1/github-skills/search', params);
  return response.data;
};

/**
 * 列出仓库中的技能
 */
export const listRepoSkills = async (repoUrl: string): Promise<GitHubSkillItem[]> => {
  const response = await apiClient.get(`/api/v1/github-skills/repos/${repoUrl}/skills`);
  return response.data;
};

/**
 * 从 GitHub 安装技能
 */
export const installSkillFromGitHub = async (data: InstallSkillRequest): Promise<InstallSkillResponse> => {
  const response = await apiClient.post('/api/v1/github-skills/install', data);
  return response.data;
};

/**
 * 获取调试中的技能列表
 */
export const getDebugSkills = async (): Promise<InstallSkillResponse[]> => {
  const response = await apiClient.get('/api/v1/github-skills/debug-skills');
  return response.data;
};

/**
 * 发布技能到生产环境
 */
export const publishSkill = async (skillId: number): Promise<InstallSkillResponse> => {
  const response = await apiClient.post(`/api/v1/github-skills/publish/${skillId}`);
  return response.data;
};

/**
 * 删除调试中的技能
 */
export const deleteDebugSkill = async (skillId: number): Promise<{ status: string; skill_id: number }> => {
  const response = await apiClient.delete(`/api/v1/github-skills/debug-skills/${skillId}`);
  return response.data;
};

/**
 * 删除技能（通用接口 - 可删除任何状态的技能）
 */
export const deleteSkill = async (skillId: number): Promise<void> => {
  const response = await apiClient.delete(`/api/v1/skills/${skillId}`);
  if (response.error) {
    throw new Error(response.error);
  }
};

// ==================== 辅助函数 ====================

/**
 * 获取技能状态标签
 */
export const getSkillStatusBadge = (status: string): { label: string; color: string } => {
  const statusMap: Record<string, { label: string; color: string }> = {
    draft: { label: '草稿', color: 'default' },
    testing: { label: '调试中', color: 'warning' },
    published: { label: '已发布', color: 'success' },
    official: { label: '官方', color: 'primary' },
    archived: { label: '已归档', color: 'secondary' }
  };
  return statusMap[status] || { label: status, color: 'default' };
};

/**
 * 获取技能来源标签
 */
export const getSkillSourceBadge = (source?: string): { label: string; icon: string; color: string } => {
  const sourceMap: Record<string, { label: string; icon: string; color: string }> = {
    github: { label: 'GitHub', icon: 'GitBranch', color: 'purple' },
    conversation: { label: '对话生成', icon: 'Sparkles', color: 'blue' },
    upload: { label: '手动上传', icon: 'Upload', color: 'green' },
    official: { label: '官方预设', icon: 'Crown', color: 'amber' }
  };
  return sourceMap[source || 'conversation'] || sourceMap['conversation'];
};

/**
 * 判断技能是否可以编辑
 */
export const canEditSkill = (skill: Skill, currentUserId: number | null): boolean => {
  return skill.author_id === currentUserId;
};

/**
 * 判断技能是否可以发布
 */
export const canPublishSkill = (skill: Skill): boolean => {
  return skill.status === 'testing';
};

/**
 * 判断技能是否可以删除
 */
export const canDeleteSkill = (skill: Skill): boolean => {
  return skill.status === 'testing' || skill.status === 'draft';
};

export default {
  getSkillMarket,
  getMySkills,
  searchGitHubRepos,
  listRepoSkills,
  installSkillFromGitHub,
  getDebugSkills,
  publishSkill,
  deleteDebugSkill,
  getSkillStatusBadge,
  canEditSkill,
  canPublishSkill,
  canDeleteSkill
};
