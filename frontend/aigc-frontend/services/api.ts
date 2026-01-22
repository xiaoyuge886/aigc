// API 基础配置和请求封装
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      ...this.defaultHeaders,
      ...this.getAuthHeaders(),
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Check if response is JSON
      const contentType = response.headers.get('content-type');
      let data: any;
      
      if (contentType && contentType.includes('application/json')) {
        try {
          data = await response.json();
        } catch (jsonError) {
          // If JSON parsing fails, try to get text
          const text = await response.text();
          data = { detail: text || '请求失败' };
        }
      } else {
        // Non-JSON response (e.g., 204 No Content)
        const text = await response.text();
        data = text ? { detail: text } : {};
      }

      if (!response.ok) {
        // 确保错误消息是字符串
        let errorMessage = '请求失败';
        if (data.detail) {
          errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        } else if (data.error) {
          errorMessage = typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
        }

        return {
          error: errorMessage,
          status: response.status,
        };
      }

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      // Handle network errors (e.g., ERR_INSUFFICIENT_RESOURCES)
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        return {
          error: '网络连接失败，请检查网络或稍后重试',
          status: 0,
        };
      }
      return {
        error: error instanceof Error ? error.message : '网络错误',
        status: 0,
      };
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async put<T>(endpoint: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient();

// =========================================================================
// Phase 3: 反馈收集 API
// =========================================================================

export interface FeedbackRequest {
  message_id?: number;
  session_id?: string;
  conversation_turn_id?: string;
  feedback_type: 'like' | 'dislike' | 'correct' | 'regenerate' | 'implicit_retry' | 'implicit_modify';
  feedback_data?: Record<string, any>;
  user_prompt?: string;
  assistant_response?: string;
  scenario_ids?: string[];
}

export interface ImplicitFeedbackRequest {
  session_id?: string;
  implicit_type: 'retry' | 'modify' | 'regenerate';
  original_prompt?: string;
  modified_prompt?: string;
  context?: Record<string, any>;
}

/**
 * 提交用户反馈
 */
export async function submitFeedback(request: FeedbackRequest): Promise<void> {
  const response = await apiClient.post('/api/v1/feedback', request);
  if (response.error) {
    throw new Error(response.error);
  }
}

/**
 * 提交隐式反馈
 */
export async function submitImplicitFeedback(request: ImplicitFeedbackRequest): Promise<void> {
  const response = await apiClient.post('/api/v1/feedback/implicit', request);
  if (response.error) {
    throw new Error(response.error);
  }
}
