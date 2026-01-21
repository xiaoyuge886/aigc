/**
 * 用户偏好查看界面
 * 
 * Phase 3: UI-003
 * 功能：用户可以查看自己的偏好设置（模型学习到的偏好）
 */
import React, { useState, useEffect } from 'react';
import { User, Sparkles, TrendingUp, Settings, RefreshCw, AlertCircle } from 'lucide-react';
import { apiClient } from '../services/api';
import { authService } from '../services/authService';

interface UserPreferences {
  preferred_scenarios?: string[];
  preferred_style?: string;
  common_question_types?: string[];
  learned_rules?: string[];
  work_pattern?: string;
  reasoning?: string;
}

export const UserPreferences: React.FC = () => {
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [currentUser, setCurrentUser] = useState<{ id: number; username: string } | null>(null);

  useEffect(() => {
    loadUserInfo();
  }, []);

  useEffect(() => {
    if (currentUser) {
      loadPreferences();
    }
  }, [currentUser]);

  const loadUserInfo = async () => {
    try {
      const result = await authService.getCurrentUser();
      if (result.success && result.data && result.data.id) {
        setCurrentUser({ id: result.data.id, username: result.data.username });
      }
    } catch (err) {
      console.error('获取用户信息失败:', err);
    }
  };

  const loadPreferences = async () => {
    if (!currentUser) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // 注意：这里需要后端提供获取用户偏好的API
      // 由于偏好是缓存在 user_preferences_cache 表中的，我们需要一个API来获取
      // 暂时使用模拟数据，实际应该调用后端API
      const response = await apiClient.get<{ preferences: UserPreferences }>(
        `/api/v1/platform/users/${currentUser.id}/preferences`
      );
      
      if (response.error) {
        if (response.status === 404) {
          // 偏好不存在，这是正常的（用户还没有足够的反馈数据）
          setPreferences(null);
        } else {
          throw new Error(response.error);
        }
      } else {
        setPreferences(response.data?.preferences || null);
      }
    } catch (err) {
      console.error('加载用户偏好失败:', err);
      setError(err instanceof Error ? err.message : '加载偏好失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!currentUser) return;
    
    setRefreshing(true);
    try {
      // 触发重新分析用户偏好（强制刷新）
      await apiClient.post(`/api/v1/platform/users/${currentUser.id}/preferences/refresh`);
      // 重新加载偏好
      await loadPreferences();
    } catch (err) {
      console.error('刷新偏好失败:', err);
      alert('刷新失败: ' + (err instanceof Error ? err.message : '未知错误'));
    } finally {
      setRefreshing(false);
    }
  };

  const getStyleLabel = (style: string) => {
    const styleMap: Record<string, string> = {
      'detailed': '详细回答',
      'concise': '简洁回答',
      'professional': '专业风格',
      'casual': '轻松风格'
    };
    return styleMap[style] || style;
  };

  if (loading) {
    return (
      <div className="p-8 text-center">
        <RefreshCw className="animate-spin mx-auto mb-4 text-gray-400" size={32} />
        <p className="text-gray-500">加载偏好中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
          <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <h3 className="font-semibold text-red-800 mb-1">加载失败</h3>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!preferences) {
    return (
      <div className="p-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <Sparkles className="mx-auto mb-4 text-blue-500" size={48} />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">还没有偏好数据</h3>
          <p className="text-sm text-gray-600 mb-4">
            系统会根据你的使用习惯和反馈自动学习你的偏好。
            <br />
            当你提供足够的反馈后，偏好信息会显示在这里。
          </p>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {refreshing ? '刷新中...' : '手动刷新'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <User className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">我的偏好</h2>
            <p className="text-sm text-gray-500">系统根据你的使用习惯自动学习</p>
          </div>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 flex items-center space-x-2"
        >
          <RefreshCw className={refreshing ? 'animate-spin' : ''} size={16} />
          <span>{refreshing ? '刷新中...' : '刷新偏好'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 常用场景偏好 */}
        {preferences.preferred_scenarios && preferences.preferred_scenarios.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-center space-x-2 mb-4">
              <Sparkles className="text-blue-500" size={20} />
              <h3 className="font-semibold text-gray-900">常用场景</h3>
            </div>
            <div className="space-y-2">
              {preferences.preferred_scenarios.map((scenario, index) => (
                <div
                  key={index}
                  className="px-3 py-2 bg-blue-50 rounded-lg text-sm text-gray-700"
                >
                  {scenario}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 回答风格偏好 */}
        {preferences.preferred_style && (
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-center space-x-2 mb-4">
              <Settings className="text-purple-500" size={20} />
              <h3 className="font-semibold text-gray-900">回答风格</h3>
            </div>
            <div className="px-3 py-2 bg-purple-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">
                {getStyleLabel(preferences.preferred_style)}
              </span>
            </div>
          </div>
        )}

        {/* 问题类型模式 */}
        {preferences.common_question_types && preferences.common_question_types.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-center space-x-2 mb-4">
              <TrendingUp className="text-green-500" size={20} />
              <h3 className="font-semibold text-gray-900">常见问题类型</h3>
            </div>
            <div className="space-y-2">
              {preferences.common_question_types.map((type, index) => (
                <div
                  key={index}
                  className="px-3 py-1.5 bg-green-50 rounded-lg text-sm text-gray-700"
                >
                  {type}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 工作模式 */}
        {preferences.work_pattern && (
          <div className="bg-white rounded-lg border border-gray-200 p-5">
            <div className="flex items-center space-x-2 mb-4">
              <User className="text-orange-500" size={20} />
              <h3 className="font-semibold text-gray-900">工作模式</h3>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">
              {preferences.work_pattern}
            </p>
          </div>
        )}
      </div>

      {/* 从反馈中学习的规则 */}
      {preferences.learned_rules && preferences.learned_rules.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <div className="flex items-center space-x-2 mb-4">
            <Sparkles className="text-indigo-500" size={20} />
            <h3 className="font-semibold text-gray-900">学习到的规则</h3>
          </div>
          <div className="space-y-2">
            {preferences.learned_rules.map((rule, index) => (
              <div
                key={index}
                className="flex items-start space-x-3 px-3 py-2 bg-indigo-50 rounded-lg"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-2 flex-shrink-0" />
                <p className="text-sm text-gray-700 flex-1">{rule}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 分析推理过程 */}
      {preferences.reasoning && (
        <div className="bg-gray-50 rounded-lg border border-gray-200 p-5">
          <h3 className="font-semibold text-gray-900 mb-3">分析说明</h3>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
            {preferences.reasoning}
          </p>
        </div>
      )}
    </div>
  );
};
