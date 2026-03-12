// Platform management service
import { apiClient } from './api';

export type { SystemPrompt, SystemPromptCreate, SystemPromptUpdate, Skill, SkillCreate, SkillUpdate };
export type { CapabilityPackage, CapabilityPackageCreate, CapabilityPackageUpdate, UserCapabilityBinding, UserCapabilityBindingCreate, UserCapabilityBindingUpdate };

// User Configuration Types
export interface UserConfig {
  user_id: number;
  default_system_prompt?: string;
  default_allowed_tools?: string[];
  default_model?: string;
  permission_mode?: string;
  max_turns?: number;
  work_dir?: string;
  custom_tools?: Record<string, any>;
  custom_skills?: string[];
  associated_scenario_id?: number;  // 改为整数ID
  created_at?: string;
  updated_at?: string;
}

export interface UserConfigCreate {
  default_system_prompt?: string;
  default_allowed_tools?: string[];
  default_model?: string;
  permission_mode?: string;
  max_turns?: number;
  work_dir?: string;
  custom_tools?: Record<string, any>;
  custom_skills?: string[];
  associated_scenario_id?: number;  // 改为整数ID
}

export interface UserConfigUpdate {
  default_system_prompt?: string;
  default_allowed_tools?: string[];
  default_model?: string;
  permission_mode?: string;
  max_turns?: number;
  work_dir?: string;
  custom_tools?: Record<string, any>;
  custom_skills?: string[];
}

// System Prompt Types
export interface SystemPrompt {
  id: number;  // 使用整数ID作为业务标识
  name: string;
  description?: string;
  category?: string;
  content: string;
  usage_count: number;
  is_default: boolean;
  created_by?: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface SystemPromptCreate {
  // 移除 prompt_id 字段，使用自增整数 id
  name: string;
  description?: string;
  category?: string;
  content: string;
  is_default?: boolean;
  is_public?: boolean;
}

export interface SystemPromptUpdate {
  name?: string;
  description?: string;
  category?: string;
  content?: string;
  is_default?: boolean;
  is_public?: boolean;
}

// Skill Types
export interface Skill {
  id: number;  // 使用整数ID作为业务标识
  name: string;
  description?: string;
  category?: string;
  skill_content: string;
  skill_config?: Record<string, any>;
  usage_count: number;
  is_default: boolean;
  created_by?: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface SkillCreate {
  // 移除 skill_id 字段，使用自增整数 id
  name: string;
  description?: string;
  category?: string;
  skill_content: string;
  skill_config?: Record<string, any>;
  is_default?: boolean;
  is_public?: boolean;
}

export interface SkillUpdate {
  name?: string;
  description?: string;
  category?: string;
  skill_content?: string;
  skill_config?: Record<string, any>;
  is_default?: boolean;
  is_public?: boolean;
}

// Business Scenario Types (保留用于向后兼容)
export interface BusinessScenario {
  id: number;  // 使用整数ID作为业务标识
  name: string;
  description?: string;
  category?: string;
  meta?: Record<string, any>;
  system_prompt: string;
  allowed_tools?: string[];
  recommended_model?: string;
  custom_tools?: Record<string, any>;
  skills?: string[];
  workflow?: Record<string, any>;
  permission_mode?: string;
  max_turns?: number;
  work_dir?: string;
  created_by?: number;
  is_public: boolean;
  is_default?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface BusinessScenarioCreate {
  // 移除 scenario_id 字段，使用自增整数 id
  name: string;
  description?: string;
  category?: string;
  meta?: Record<string, any>;
  system_prompt: string;
  allowed_tools?: string[];
  recommended_model?: string;
  custom_tools?: Record<string, any>;
  skills?: string[];
  workflow?: Record<string, any>;
  permission_mode?: string;
  max_turns?: number;
  work_dir?: string;
  is_public?: boolean;
  is_default?: boolean;
}

export interface BusinessScenarioUpdate {
  name?: string;
  description?: string;
  category?: string;
  meta?: Record<string, any>;
  system_prompt?: string;
  allowed_tools?: string[];
  recommended_model?: string;
  custom_tools?: Record<string, any>;
  skills?: string[];
  workflow?: Record<string, any>;
  permission_mode?: string;
  max_turns?: number;
  work_dir?: string;
  is_public?: boolean;
  is_default?: boolean;
}

// =========================================================================
// Capability Package Types (能力包) ⭐ 核心功能
// =========================================================================

export interface CapabilityPackage {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  version?: string;
  category?: string;
  is_public: boolean;
  is_official: boolean;

  // 能力定义
  skills?: string[];
  allowed_tools?: string[];
  mcp_servers?: Record<string, any>;
  custom_prompt_extension?: string;
  plugin_path?: string;

  // 元数据
  icon_url?: string;
  tags?: string[];

  // 统计
  usage_count?: number;
  author_id?: number;
  created_at: string;
  updated_at: string;
}

export interface CapabilityPackageCreate {
  name: string;
  display_name: string;
  description?: string;
  version?: string;
  category?: string;
  is_public?: boolean;
  is_official?: boolean;

  // 能力定义
  skills?: string[];
  allowed_tools?: string[];
  mcp_servers?: Record<string, any>;
  custom_prompt_extension?: string;
  plugin_path?: string;

  // 元数据
  icon_url?: string;
  tags?: string[];
}

export interface CapabilityPackageUpdate {
  name?: string;
  display_name?: string;
  description?: string;
  version?: string;
  category?: string;
  is_public?: boolean;
  is_official?: boolean;

  // 能力定义
  skills?: string[];
  allowed_tools?: string[];
  mcp_servers?: Record<string, any>;
  custom_prompt_extension?: string;
  plugin_path?: string;

  // 元数据
  icon_url?: string;
  tags?: string[];
}

// User Capability Binding Types
export interface UserCapabilityBinding {
  id: number;
  user_id: number;
  package_id: number;
  package_name?: string;
  package_display_name?: string;
  is_enabled: boolean;
  granted_at: string;
  granted_by?: number;
  usage_count: number;
  last_used_at?: string;
  created_at: string;
}

export interface UserCapabilityBindingCreate {
  user_id: number;
  package_id: number;
  is_enabled?: boolean;
}

export interface UserCapabilityBindingUpdate {
  is_enabled?: boolean;
}

class PlatformService {
  // User Configuration APIs
  async getUserConfig(userId: number): Promise<UserConfig | null> {
    try {
      const response = await apiClient.get<UserConfig>(`/api/v1/platform/users/${userId}/config`);
      
      // 网络错误（status: 0）表示请求失败
      if (response.status === 0 && response.error) {
        throw new Error(response.error);
      }
      
      // HTTP 错误抛出异常
      if (response.error) {
        throw new Error(response.error);
      }
      
      // 成功返回数据
      const config = response.data;
      
      // 如果所有配置字段都是 null/undefined，表示配置不存在，返回 null
      if (config && !config.default_system_prompt && 
          (!config.default_allowed_tools || config.default_allowed_tools.length === 0) &&
          !config.default_model && !config.permission_mode && 
          !config.max_turns && !config.work_dir &&
          (!config.custom_tools || Object.keys(config.custom_tools).length === 0) &&
          (!config.custom_skills || config.custom_skills.length === 0)) {
        return null;
      }
      
      return config || null;
    } catch (error) {
      // 如果已经是 Error 对象，直接抛出
      if (error instanceof Error) {
        throw error;
      }
      // 其他情况转换为 Error
      throw new Error(error instanceof Error ? error.message : '加载用户配置失败');
    }
  }

  async createUserConfig(userId: number, config: UserConfigCreate): Promise<UserConfig> {
    const response = await apiClient.post<UserConfig>(
      `/api/v1/platform/users/${userId}/config`,
      config
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('创建用户配置失败');
    }
    return response.data;
  }

  async updateUserConfig(userId: number, config: UserConfigUpdate): Promise<UserConfig> {
    const response = await apiClient.put<UserConfig>(
      `/api/v1/platform/users/${userId}/config`,
      config
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('更新用户配置失败');
    }
    return response.data;
  }

  async deleteUserConfig(userId: number): Promise<void> {
    const response = await apiClient.delete(`/api/v1/platform/users/${userId}/config`);
    if (response.error) {
      throw new Error(response.error);
    }
  }

  // Business Scenario APIs
  async listScenarios(publicOnly: boolean = false): Promise<BusinessScenario[]> {
    const response = await apiClient.get<BusinessScenario[]>(
      `/api/v1/platform/scenarios?public_only=${publicOnly}`
    );
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data || [];
  }

  async getScenario(scenarioId: number): Promise<BusinessScenario> {  // 改为整数ID
    const response = await apiClient.get<BusinessScenario>(
      `/api/v1/platform/scenarios/${scenarioId}`
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('获取业务场景失败');
    }
    return response.data;
  }

  async createScenario(scenario: BusinessScenarioCreate): Promise<BusinessScenario> {
    const response = await apiClient.post<BusinessScenario>(
      '/api/v1/platform/scenarios',
      scenario
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('创建业务场景失败');
    }
    return response.data;
  }

  async updateScenario(scenarioId: number, scenario: BusinessScenarioUpdate): Promise<BusinessScenario> {  // 改为整数ID
    const response = await apiClient.put<BusinessScenario>(
      `/api/v1/platform/scenarios/${scenarioId}`,
      scenario
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('更新业务场景失败');
    }
    return response.data;
  }

  async deleteScenario(scenarioId: number): Promise<void> {  // 改为整数ID
    const response = await apiClient.delete(`/api/v1/platform/scenarios/${scenarioId}`);
    if (response.error) {
      throw new Error(response.error);
    }
  }

  // Available Scenarios API (for scenario selector)
  async getAvailableScenarios(): Promise<BusinessScenario[]> {
    const response = await apiClient.get<BusinessScenario[]>(
      '/api/v1/platform/scenarios/available'
    );
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data || [];
  }

  // User Scenario Config APIs
  async getUserScenarioConfig(userId: number): Promise<{ scenario_ids: number[]; user_custom_prompt?: string } | null> {  // 改为整数ID数组
    const response = await apiClient.get<{ scenario_ids: number[]; user_custom_prompt?: string }>(
      `/api/v1/platform/users/${userId}/scenario-config`
    );
    if (response.error) {
      if (response.status === 404) {
        return null; // 配置不存在
      }
      throw new Error(response.error);
    }
    return response.data || null;
  }

  async updateUserScenarioConfig(
    userId: number,
    scenarioIds: number[],  // 改为整数ID数组
    userCustomPrompt?: string
  ): Promise<{ scenario_ids: number[]; user_custom_prompt?: string }> {
    const response = await apiClient.put<{ scenario_ids: number[]; user_custom_prompt?: string }>(
      `/api/v1/platform/users/${userId}/scenario-config`,
      {
        scenario_ids: scenarioIds,
        user_custom_prompt: userCustomPrompt
      }
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('更新用户场景配置失败');
    }
    return response.data;
  }

  // System Prompt APIs
  async listSystemPrompts(category?: string, isPublic?: boolean): Promise<SystemPrompt[]> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (isPublic !== undefined) params.append('is_public', String(isPublic));
    const response = await apiClient.get<SystemPrompt[]>(`/api/v1/platform/system-prompts?${params.toString()}`);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data || [];
  }

  async getSystemPrompt(promptId: number): Promise<SystemPrompt> {  // 改为整数ID
    const response = await apiClient.get<SystemPrompt>(`/api/v1/platform/system-prompts/${promptId}`);
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('获取系统提示词失败');
    }
    return response.data;
  }

  async createSystemPrompt(data: SystemPromptCreate): Promise<SystemPrompt> {
    const response = await apiClient.post<SystemPrompt>('/api/v1/platform/system-prompts', data);
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('创建系统提示词失败');
    }
    return response.data;
  }

  async updateSystemPrompt(promptId: number, data: SystemPromptUpdate): Promise<SystemPrompt> {  // 改为整数ID
    const response = await apiClient.put<SystemPrompt>(`/api/v1/platform/system-prompts/${promptId}`, data);
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('更新系统提示词失败');
    }
    return response.data;
  }

  async deleteSystemPrompt(promptId: number): Promise<void> {  // 改为整数ID
    const response = await apiClient.delete(`/api/v1/platform/system-prompts/${promptId}`);
    if (response.error) {
      throw new Error(response.error);
    }
  }

  // Skill APIs
  async listSkills(category?: string, isPublic?: boolean): Promise<Skill[]> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (isPublic !== undefined) params.append('is_public', String(isPublic));
    const response = await apiClient.get<Skill[]>(`/api/v1/platform/skills?${params.toString()}`);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data || [];
  }

  async getSkill(skillId: number): Promise<Skill> {  // 改为整数ID
    const response = await apiClient.get<Skill>(`/api/v1/platform/skills/${skillId}`);
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('获取技能失败');
    }
    return response.data;
  }

  async createSkill(data: SkillCreate): Promise<Skill> {
    const response = await apiClient.post<Skill>('/api/v1/platform/skills', data);
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('创建技能失败');
    }
    return response.data;
  }

  async updateSkill(skillId: number, data: SkillUpdate): Promise<Skill> {  // 改为整数ID
    const response = await apiClient.put<Skill>(`/api/v1/platform/skills/${skillId}`, data);
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('更新技能失败');
    }
    return response.data;
  }

  async deleteSkill(skillId: number): Promise<void> {  // 改为整数ID
    const response = await apiClient.delete(`/api/v1/platform/skills/${skillId}`);
    if (response.error) {
      throw new Error(response.error);
    }
  }

  // User Log APIs
  async getUserLogs(userId: number, limit?: number, offset?: number): Promise<any> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', String(limit));
    if (offset) params.append('offset', String(offset));
    const response = await apiClient.get<any>(`/api/v1/platform/users/${userId}/logs?${params.toString()}`);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data;
  }

  // 获取用户会话列表（适配 SessionHistory 组件格式）
  // 使用新的专门接口 /api/v1/platform/users/{user_id}/sessions
  async getUserSessionsList(userId: number, limit?: number, offset: number = 0): Promise<{
    total: number;
    limit?: number | null;
    offset: number;
    has_more: boolean;
    sessions: Array<{
      session_id: string;
      created_at: string;
      last_activity: string;
      is_connected: boolean;
      model?: string;
    }>;
    stats?: {
      total_sessions: number;
      total_messages: number;
      total_cost_usd: number;
    };
  }> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', String(limit));
    if (offset) params.append('offset', String(offset));
    
    const response = await apiClient.get<any>(`/api/v1/platform/users/${userId}/sessions?${params.toString()}`);
    if (response.error) {
      throw new Error(response.error);
    }
    
    const data = response.data;
    
    // 统计信息应该从后端接口直接返回
    // 如果后端没有返回，则使用默认值
    const stats = data.stats || {
      total_sessions: data.total || 0,
      total_messages: 0,
      total_cost_usd: 0.0,
    };
    
    return {
      total: data.total || 0,
      limit: data.limit || null,
      offset: data.offset || 0,
      has_more: data.has_more || false,
      sessions: data.sessions || [],
      stats,
    };
  }

  // Scenario Share & Duplicate APIs
  async duplicateScenario(
    scenarioId: number,  // 改为整数ID
    newName?: string  // 移除 newScenarioId，使用自增ID
  ): Promise<BusinessScenario> {
    const response = await apiClient.post<BusinessScenario>(
      `/api/v1/platform/scenarios/${scenarioId}/duplicate`,
      {
        new_name: newName
      }
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('复制场景失败');
    }
    return response.data;
  }

  async shareScenario(scenarioId: number, makePublic: boolean): Promise<void> {  // 改为整数ID
    const response = await apiClient.post(
      `/api/v1/platform/scenarios/${scenarioId}/share`,
      { make_public: makePublic }
    );
    if (response.error) {
      throw new Error(response.error);
    }
  }

  // User Preferences APIs
  async getUserPreferences(userId: number): Promise<{
    preferred_scenarios: string[];
    preferred_style: string;
    common_question_types: string[];
    learned_rules: string[];
    work_pattern: string;
    reasoning: string;
  } | null> {
    const response = await apiClient.get<{
      preferences: {
        preferred_scenarios: string[];
        preferred_style: string;
        common_question_types: string[];
        learned_rules: string[];
        work_pattern: string;
        reasoning: string;
      };
    }>(`/api/v1/platform/users/${userId}/preferences`);
    if (response.error) {
      if (response.status === 404) {
        return null; // 偏好不存在
      }
      throw new Error(response.error);
    }
    return response.data?.preferences || null;
  }

  // Session Preferences API
  async getSessionPreferences(sessionId: string): Promise<{
    corrections: string[];
    context_preferences: string;
    feedback_summary: string;
  } | null> {
    const response = await apiClient.get<{
      preferences: {
        corrections: string[];
        context_preferences: string;
        feedback_summary: string;
      };
    }>(`/api/v1/platform/sessions/${sessionId}/preferences`);
    if (response.error) {
      if (response.status === 404) {
        return null; // 偏好不存在
      }
      throw new Error(response.error);
    }
    return response.data?.preferences || null;
  }

  // =========================================================================
  // Capability Package APIs (能力包) ⭐ 核心功能
  // =========================================================================

  // 列出所有能力包
  async listPackages(publicOnly: boolean = false): Promise<CapabilityPackage[]> {
    const response = await apiClient.get<{ packages: CapabilityPackage[]; total: number }>(
      `/api/v1/platform/packages?public_only=${publicOnly}`
    );
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data?.packages || [];
  }

  // 获取能力包详情
  async getPackage(packageId: number): Promise<CapabilityPackage> {
    const response = await apiClient.get<CapabilityPackage>(
      `/api/v1/platform/packages/${packageId}`
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('获取能力包失败');
    }
    return response.data;
  }

  // 创建能力包
  async createPackage(pkg: CapabilityPackageCreate): Promise<CapabilityPackage> {
    const response = await apiClient.post<CapabilityPackage>(
      '/api/v1/platform/packages',
      pkg
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('创建能力包失败');
    }
    return response.data;
  }

  // 更新能力包
  async updatePackage(packageId: number, pkg: CapabilityPackageUpdate): Promise<CapabilityPackage> {
    const response = await apiClient.put<CapabilityPackage>(
      `/api/v1/platform/packages/${packageId}`,
      pkg
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('更新能力包失败');
    }
    return response.data;
  }

  // 删除能力包
  async deletePackage(packageId: number): Promise<void> {
    const response = await apiClient.delete(`/api/v1/platform/packages/${packageId}`);
    if (response.error) {
      throw new Error(response.error);
    }
  }

  // =========================================================================
  // User Capability Binding APIs (用户能力绑定)
  // =========================================================================

  // 获取用户的能力包绑定列表
  async getUserPackages(userId: number): Promise<{
    bindings: UserCapabilityBinding[];
    available_packages: CapabilityPackage[];
  }> {
    const response = await apiClient.get<{
      bindings: UserCapabilityBinding[];
      available_packages: CapabilityPackage[];
    }>(`/api/v1/platform/users/${userId}/packages`);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data || { bindings: [], available_packages: [] };
  }

  // 绑定能力包给用户
  async bindPackageToUser(userId: number, packageId: number): Promise<UserCapabilityBinding> {
    const response = await apiClient.post<UserCapabilityBinding>(
      `/api/v1/platform/users/${userId}/packages/${packageId}/bind`
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('绑定能力包失败');
    }
    return response.data;
  }

  // 解绑用户的能力包
  async unbindPackageFromUser(userId: number, packageId: number): Promise<void> {
    const response = await apiClient.delete(
      `/api/v1/platform/users/${userId}/packages/${packageId}/unbind`
    );
    if (response.error) {
      throw new Error(response.error);
    }
  }

  // 更新用户能力绑定状态
  async updateUserPackageBinding(
    userId: number,
    packageId: number,
    update: UserCapabilityBindingUpdate
  ): Promise<UserCapabilityBinding> {
    const response = await apiClient.put<UserCapabilityBinding>(
      `/api/v1/platform/users/${userId}/packages/${packageId}`,
      update
    );
    if (response.error) {
      throw new Error(response.error);
    }
    if (!response.data) {
      throw new Error('更新能力包绑定失败');
    }
    return response.data;
  }

  // 获取当前用户可用的能力包
  async getMyPackages(): Promise<{
    bindings: UserCapabilityBinding[];
    available_packages: CapabilityPackage[];
  }> {
    const response = await apiClient.get<{
      bindings: UserCapabilityBinding[];
      available_packages: CapabilityPackage[];
    }>('/api/v1/platform/users/me/packages');
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data || { bindings: [], available_packages: [] };
  }

  // =========================================================================
  // Package Files API (能力包文件)
  // =========================================================================

  // 获取能力包文件结构
  async getPackageFiles(packageId: number, path?: string): Promise<{
    type: 'plugin' | 'database';
    plugin_path?: string;
    base_path?: string;
    current_path?: string;
    files: PackageFile[];
  }> {
    const params = path ? `?path=${encodeURIComponent(path)}` : '';
    const response = await apiClient.get<{
      type: 'plugin' | 'database';
      plugin_path?: string;
      base_path?: string;
      current_path?: string;
      files: PackageFile[];
    }>(`/api/v1/platform/packages/${packageId}/files${params}`);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data || { type: 'database', files: [] };
  }
}

// 能力包文件类型
export interface PackageFile {
  name: string;
  type: 'file' | 'folder';
  path: string;
  content?: string;
  size?: number;
  children?: PackageFile[];
}

export const platformService = new PlatformService();
