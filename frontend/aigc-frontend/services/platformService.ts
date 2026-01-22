// Platform management service
import { apiClient } from './api';

export type { SystemPrompt, SystemPromptCreate, SystemPromptUpdate, Skill, SkillCreate, SkillUpdate };

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

// Business Scenario Types
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
}

export const platformService = new PlatformService();
