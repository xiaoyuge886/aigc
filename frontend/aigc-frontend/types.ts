
import React from 'react';

export enum Sender {
  User = 'user',
  AI = 'ai'
}

export enum UserRole {
  Admin = 'ADMIN',
  User = 'USER',
  Developer = 'DEVELOPER'
}

export interface SystemUser {
  id: number;
  username: string;
  role: UserRole;
  email: string;
  full_name?: string;
  avatar_url?: string;
  role_id?: number;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
  // 用于显示的可选字段
  status?: 'active' | 'suspended';
  tokenLimit?: number;
  tokenUsed?: number;
  joinDate?: string;
}

export interface UsageLog {
  id: string;
  userId: string;
  username: string;
  model: string;
  tokens: number;
  cost: number;
  timestamp: string;
}

export interface AppFile {
  id: string;
  name: string;
  type: string;
  content: string; // base64 or raw text
  url?: string;
  size?: number;
}

export interface ResultInfo {
  subtype?: string;
  duration_ms?: number;
  duration_api_ms?: number;
  is_error?: boolean;
  num_turns?: number;
  session_id?: string;
  total_cost_usd?: number | null;
  usage?: Record<string, any> | null;
}

export interface ToolCallInfo {
  tool_use_id: string;
  tool_name: string;
  tool_input: Record<string, any>;
  tool_output?: string | null;
  conversation_turn_id?: string | null; // 工具调用所属的对话轮次ID
}

export interface Message {
  id: string;
  text: string;
  sender: Sender;
  timestamp: Date;
  isThinking?: boolean;
  file?: AppFile;
  resultInfo?: ResultInfo; // ResultMessage 信息
  conversation_turn_id?: string | null; // 对话轮次ID
  parent_message_id?: number | null; // 父消息ID
  tool_calls?: ToolCallInfo[]; // 工具调用列表
}

export interface HistoryItem {
  id: string;
  userId?: string;
  username?: string;
  title: string;
  date: string;
  status: string;
  tokenCount: string;
  cost: string;
  messageCount: string;
}

export interface ChartDataPoint {
  name: string;
  value: number;
  tokens: number;
}

export interface StatCardProps {
  title: string;
  value: string;
  trend?: string;
  icon: React.ReactNode;
  color?: string;
}
