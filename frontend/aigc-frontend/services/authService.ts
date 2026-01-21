// 认证服务
import { apiClient } from './api';

// 认证相关类型定义
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  role_id?: number;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

class AuthService {
  private readonly TOKEN_KEY = 'access_token';
  private readonly USER_KEY = 'current_user';

  // 登录
  async login(username: string, password: string): Promise<{ success: boolean; data?: TokenResponse; error?: string }> {
    const response = await apiClient.post<TokenResponse>('/api/v1/auth/login', {
      username,
      password,
    });

    if (response.error) {
      return { success: false, error: response.error };
    }

    // 保存 token 和用户信息
    if (response.data) {
      this.setToken(response.data.access_token);
      this.setUser(response.data.user);
    }

    return { success: true, data: response.data };
  }

  // 注册
  async register(data: RegisterRequest): Promise<{ success: boolean; data?: User; error?: string }> {
    const response = await apiClient.post<User>('/api/v1/auth/register', data);

    if (response.error) {
      return { success: false, error: response.error };
    }

    return { success: true, data: response.data };
  }

  // 获取当前用户信息
  async getCurrentUser(): Promise<{ success: boolean; data?: User; error?: string }> {
    const response = await apiClient.get<User>('/api/v1/auth/me');

    if (response.error) {
      return { success: false, error: response.error };
    }

    if (response.data) {
      this.setUser(response.data);
    }

    return { success: true, data: response.data };
  }

  // 更新用户信息
  async updateProfile(data: Partial<User>): Promise<{ success: boolean; data?: User; error?: string }> {
    const response = await apiClient.put<User>('/api/v1/auth/me', data);

    if (response.error) {
      return { success: false, error: response.error };
    }

    if (response.data) {
      this.setUser(response.data);
    }

    return { success: true, data: response.data };
  }

  // 修改密码
  async changePassword(data: ChangePasswordRequest): Promise<{ success: boolean; error?: string }> {
    const response = await apiClient.post('/api/v1/auth/change-password', data);

    if (response.error) {
      return { success: false, error: response.error };
    }

    return { success: true };
  }

  // 登出
  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  // Token 管理
  setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  // 用户信息管理
  setUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  getUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
    return null;
  }

  // 检查是否已登录
  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  // 获取用户角色
  getUserRole(): string | null {
    const user = this.getUser();
    return user?.role_id ? `ROLE_${user.role_id}` : null;
  }

  // Admin: 获取所有用户列表
  async getAllUsers(limit?: number, offset: number = 0): Promise<{ success: boolean; data?: User[]; error?: string }> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    
    const queryString = params.toString();
    const endpoint = `/api/v1/auth/users${queryString ? `?${queryString}` : ''}`;
    
    const response = await apiClient.get<User[]>(endpoint);
    
    if (response.error) {
      return { success: false, error: response.error };
    }
    
    return { success: true, data: response.data || [] };
  }
}

export const authService = new AuthService();
