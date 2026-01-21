import React, { useState } from 'react';
import { NexusMetricsChart } from './NexusMetricsChart';
import { GlassCard } from './GlassCard';
import { Activity, Zap, Users, BarChart3, TrendingUp, Clock, AlertCircle } from 'lucide-react';

/**
 * Nexus AI 指标仪表板
 * 完整的项目关键指标分析展示
 */
const MetricsDashboard: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);

  // 实时指标数据
  const realtimeMetrics = [
    {
      title: '当前在线会话',
      value: '47',
      unit: '个',
      icon: Activity,
      color: 'blue',
      trend: '+3',
      status: 'normal'
    },
    {
      title: 'API 调用频率',
      value: '128',
      unit: '次/分',
      icon: Zap,
      color: 'green',
      trend: '+12%',
      status: 'normal'
    },
    {
      title: '活跃用户数',
      value: '89',
      unit: '人',
      icon: Users,
      color: 'purple',
      trend: '+5',
      status: 'normal'
    },
    {
      title: '系统负载',
      value: '42',
      unit: '%',
      icon: BarChart3,
      color: 'orange',
      trend: '-8%',
      status: 'warning'
    }
  ];

  // 告警信息
  const alerts = [
    {
      level: 'info',
      message: '会话并发数接近阈值 (47/100)',
      time: '2分钟前'
    },
    {
      level: 'success',
      message: '系统自动扩容完成',
      time: '15分钟前'
    },
    {
      level: 'warning',
      message: '响应时间略有上升',
      time: '1小时前'
    }
  ];

  const getStatusColor = (level: string) => {
    switch (level) {
      case 'error': return 'bg-red-50 text-red-700 border-red-200';
      case 'warning': return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'success': return 'bg-green-50 text-green-700 border-green-200';
      default: return 'bg-blue-50 text-blue-700 border-blue-200';
    }
  };

  const getIconColor = (color: string) => {
    const colors = {
      blue: 'text-blue-600 bg-blue-100',
      green: 'text-green-600 bg-green-100',
      purple: 'text-purple-600 bg-purple-100',
      orange: 'text-orange-600 bg-orange-100',
      red: 'text-red-600 bg-red-100'
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      {/* 页面头部 */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Nexus AI 指标分析中心
            </h1>
            <p className="text-gray-600">
              实时监控系统核心性能指标与用户行为趋势
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600 font-medium">系统运行正常</span>
          </div>
        </div>
      </div>

      {/* 实时指标卡片 */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        {realtimeMetrics.map((metric, index) => {
          const Icon = metric.icon;
          return (
            <GlassCard key={index} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm text-gray-500 font-medium mb-2">
                    {metric.title}
                  </p>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-3xl font-bold text-gray-900">
                      {metric.value}
                    </span>
                    <span className="text-sm text-gray-500">{metric.unit}</span>
                  </div>
                  <div className="mt-2 flex items-center space-x-2">
                    <span
                      className={`text-xs font-medium ${
                        metric.trend.startsWith('+') ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {metric.trend}
                    </span>
                    <span className="text-xs text-gray-400">vs 上一小时</span>
                  </div>
                </div>
                <div className={`p-3 rounded-xl ${getIconColor(metric.color)}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </GlassCard>
          );
        })}
      </div>

      {/* 主图表区域 */}
      <div className="mb-8">
        <NexusMetricsChart />
      </div>

      {/* 底部信息面板 */}
      <div className="grid grid-cols-3 gap-6">
        {/* 系统告警 */}
        <div className="col-span-1">
          <GlassCard className="p-6 h-full">
            <div className="flex items-center space-x-2 mb-4">
              <AlertCircle className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">系统告警</h3>
            </div>
            <div className="space-y-3">
              {alerts.map((alert, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg border ${getStatusColor(alert.level)}`}
                >
                  <p className="text-sm font-medium mb-1">{alert.message}</p>
                  <p className="text-xs opacity-75">{alert.time}</p>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* 性能指标详解 */}
        <div className="col-span-2">
          <GlassCard className="p-6 h-full">
            <div className="flex items-center space-x-2 mb-4">
              <TrendingUp className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">性能指标详解</h3>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">平均响应时间</span>
                  <Clock className="w-4 h-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold text-gray-900 mb-1">142ms</p>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: '71%' }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-2">目标: &lt;200ms</p>
              </div>

              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">任务成功率</span>
                  <Activity className="w-4 h-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold text-gray-900 mb-1">96.8%</p>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: '96.8%' }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-2">目标: &gt;95%</p>
              </div>

              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">并发会话峰值</span>
                  <Users className="w-4 h-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold text-gray-900 mb-1">67</p>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-purple-500 h-2 rounded-full"
                    style={{ width: '67%' }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-2">最大容量: 100</p>
              </div>

              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">CPU 平均使用率</span>
                  <Zap className="w-4 h-4 text-gray-400" />
                </div>
                <p className="text-2xl font-bold text-gray-900 mb-1">45%</p>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-orange-500 h-2 rounded-full"
                    style={{ width: '45%' }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 mt-2">健康范围: &lt;70%</p>
              </div>
            </div>
          </GlassCard>
        </div>
      </div>

      {/* 使用说明 */}
      <div className="mt-8 p-6 bg-white rounded-2xl shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 图表使用说明</h3>
        <div className="grid grid-cols-3 gap-6 text-sm">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">交互功能</h4>
            <ul className="space-y-1 text-gray-600">
              <li>• 点击图例可显示/隐藏数据系列</li>
              <li>• 悬停查看详细数值</li>
              <li>• 支持鼠标滚轮缩放</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">指标切换</h4>
            <ul className="space-y-1 text-gray-600">
              <li>• 总览：核心业务指标</li>
              <li>• 性能：系统资源监控</li>
              <li>• 用户：活跃度分析</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">时间范围</h4>
            <ul className="space-y-1 text-gray-600">
              <li>• 7天：近期趋势</li>
              <li>• 30天：月度分析</li>
              <li>• 90天：长期洞察</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsDashboard;
