import React, { useRef, useEffect, useState } from 'react';
import * as echarts from 'echarts';
import { Activity, Users, Zap, TrendingUp } from 'lucide-react';

interface MetricsChartProps {
  className?: string;
}

/**
 * Nexus AI 关键指标趋势图表
 * 展示系统核心性能指标的多维度分析
 */
export const NexusMetricsChart: React.FC<MetricsChartProps> = ({ className = '' }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('7d');
  const [metricType, setMetricType] = useState<'overview' | 'performance' | 'usage'>('overview');

  // 模拟数据生成器
  const generateData = (days: number, baseValue: number, volatility: number) => {
    const data = [];
    const now = new Date();
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      const randomFactor = 1 + (Math.random() - 0.5) * volatility;
      const trendFactor = 1 + (days - i) * 0.002; // 轻微上升趋势
      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.round(baseValue * randomFactor * trendFactor)
      });
    }
    return data;
  };

  // 获取天数配置
  const getDays = () => {
    switch (timeRange) {
      case '7d': return 7;
      case '30d': return 30;
      case '90d': return 90;
      default: return 7;
    }
  };

  // 生成图表配置
  const getChartOption = (): echarts.EChartsOption => {
    const days = getDays();

    // 根据指标类型生成不同数据
    const dataConfigs = {
      overview: {
        title: '系统核心指标总览',
        metrics: [
          {
            name: '活跃会话数',
            data: generateData(days, 45, 0.3),
            color: '#007AFF',
            unit: '个'
          },
          {
            name: 'API 调用次数',
            data: generateData(days, 1200, 0.4),
            color: '#34C759',
            unit: '次'
          },
          {
            name: '平均响应时间',
            data: generateData(days, 150, 0.2).map(d => ({ ...d, value: Math.round(d.value * 0.8) })),
            color: '#FF9500',
            unit: 'ms'
          }
        ]
      },
      performance: {
        title: '性能指标监控',
        metrics: [
          {
            name: 'CPU 使用率',
            data: generateData(days, 45, 0.5),
            color: '#FF3B30',
            unit: '%'
          },
          {
            name: '内存占用',
            data: generateData(days, 60, 0.3),
            color: '#5856D6',
            unit: '%'
          },
          {
            name: '任务完成率',
            data: generateData(days, 92, 0.1),
            color: '#34C759',
            unit: '%'
          }
        ]
      },
      usage: {
        title: '用户活跃度分析',
        metrics: [
          {
            name: '日活用户',
            data: generateData(days, 230, 0.25),
            color: '#007AFF',
            unit: '人'
          },
          {
            name: '新增用户',
            data: generateData(days, 35, 0.6),
            color: '#FF9500',
            unit: '人'
          },
          {
            name: '平均会话时长',
            data: generateData(days, 18, 0.35),
            color: '#AF52DE',
            unit: 'min'
          }
        ]
      }
    };

    const config = dataConfigs[metricType];
    const dates = config.metrics[0].data.map(d => d.date);

    return {
      title: {
        text: config.title,
        left: 'center',
        top: 10,
        textStyle: {
          color: '#1D1D1F',
          fontSize: 18,
          fontWeight: 700,
          fontFamily: 'SF Pro Display, -apple-system, sans-serif'
        }
      },
      legend: {
        data: config.metrics.map(m => m.name),
        bottom: 0,
        left: 'center',
        itemWidth: 12,
        itemHeight: 12,
        icon: 'circle',
        textStyle: {
          color: '#86868B',
          fontSize: 12,
          fontWeight: 500
        },
        gap: 20
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#E5E5E7',
        borderWidth: 1,
        borderRadius: 12,
        padding: [12, 16],
        textStyle: {
          color: '#1D1D1F',
          fontSize: 13,
          fontFamily: 'SF Pro Text, sans-serif'
        },
        axisPointer: {
          type: 'cross',
          lineStyle: {
            color: '#C7C7CC',
            type: 'dashed'
          }
        },
        formatter: (params: any) => {
          let html = `<div style="font-weight: 600; margin-bottom: 8px;">${params[0].axisValue}</div>`;
          params.forEach((param: any) => {
            const metric = config.metrics.find(m => m.name === param.seriesName);
            html += `
              <div style="display: flex; justify-content: space-between; align-items: center; margin: 4px 0;">
                <span style="display: flex; align-items: center;">
                  <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${param.color}; margin-right: 8px;"></span>
                  ${param.seriesName}
                </span>
                <span style="font-weight: 600; margin-left: 20px;">${param.value} ${metric?.unit || ''}</span>
              </div>
            `;
          });
          return html;
        }
      },
      grid: {
        top: 70,
        left: 60,
        right: 40,
        bottom: 60,
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: dates,
        boundaryGap: false,
        axisLine: {
          show: true,
          lineStyle: { color: '#E5E5E7' }
        },
        axisLabel: {
          color: '#86868B',
          fontSize: 11,
          fontWeight: '500',
          fontFamily: 'SF Pro Text, sans-serif'
        },
        axisTick: { show: false },
        splitLine: { show: false }
      },
      yAxis: [
        {
          type: 'value',
          name: config.metrics[0].unit,
          nameTextStyle: {
            color: '#86868B',
            fontSize: 11,
            fontWeight: '500'
          },
          splitLine: {
            show: true,
            lineStyle: { color: '#F2F2F7', type: 'dashed' }
          },
          axisLabel: {
            color: '#86868B',
            fontSize: 11
          },
          axisLine: { show: false }
        }
      ],
      series: config.metrics.map(metric => ({
        name: metric.name,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: metric.data.map(d => d.value),
        itemStyle: {
          color: metric.color,
          borderWidth: 2,
          borderColor: '#fff'
        },
        lineStyle: {
          width: 2.5,
          color: metric.color
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: `${metric.color}30` },
              { offset: 1, color: `${metric.color}05` }
            ]
          }
        },
        emphasis: {
          focus: 'series',
          scale: true
        }
      })),
      animationDuration: 1000,
      animationEasing: 'cubicOut'
    };
  };

  // 初始化图表
  useEffect(() => {
    if (!chartRef.current) return;

    // 初始化 ECharts 实例
    chartInstance.current = echarts.init(chartRef.current, null, {
      renderer: 'canvas',
      useDirtyRect: true
    });

    // 渲染初始图表
    chartInstance.current.setOption(getChartOption());

    // 响应式调整
    const resizeObserver = new ResizeObserver(() => {
      chartInstance.current?.resize();
    });
    resizeObserver.observe(chartRef.current);

    return () => {
      resizeObserver.disconnect();
      chartInstance.current?.dispose();
    };
  }, []);

  // 更新图表
  useEffect(() => {
    if (chartInstance.current) {
      chartInstance.current.setOption(getChartOption(), true);
    }
  }, [timeRange, metricType]);

  // 统计卡片数据
  const statsCards = [
    {
      title: '总会话数',
      value: '1,284',
      change: '+12.5%',
      trend: 'up',
      icon: Activity,
      color: '#007AFF'
    },
    {
      title: '活跃用户',
      value: '892',
      change: '+8.3%',
      trend: 'up',
      icon: Users,
      color: '#34C759'
    },
    {
      title: '平均响应',
      value: '142ms',
      change: '-15.2%',
      trend: 'down',
      icon: Zap,
      color: '#FF9500'
    },
    {
      title: '任务成功率',
      value: '96.8%',
      change: '+2.1%',
      trend: 'up',
      icon: TrendingUp,
      color: '#5856D6'
    }
  ];

  return (
    <div className={`bg-white rounded-3xl shadow-lg overflow-hidden ${className}`}>
      {/* 顶部统计卡片 */}
      <div className="grid grid-cols-4 gap-4 p-6 border-b border-gray-100">
        {statsCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="flex items-center space-x-3">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: `${stat.color}10` }}
              >
                <Icon className="w-6 h-6" style={{ color: stat.color }} />
              </div>
              <div className="flex-1">
                <p className="text-xs text-gray-500 font-medium">{stat.title}</p>
                <p className="text-lg font-bold text-gray-900">{stat.value}</p>
                <p
                  className={`text-xs font-medium ${
                    stat.trend === 'up' ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {stat.change}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* 控制栏 */}
      <div className="flex items-center justify-between px-6 py-3 bg-gray-50 border-b border-gray-100">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600 font-medium">指标类型:</span>
          <div className="flex bg-gray-200 rounded-lg p-1">
            {(['overview', 'performance', 'usage'] as const).map((type) => (
              <button
                key={type}
                onClick={() => setMetricType(type)}
                className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
                  metricType === type
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {type === 'overview' ? '总览' : type === 'performance' ? '性能' : '用户'}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600 font-medium">时间范围:</span>
          <div className="flex bg-gray-200 rounded-lg p-1">
            {(['7d', '30d', '90d'] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  timeRange === range
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {range === '7d' ? '7天' : range === '30d' ? '30天' : '90天'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 图表容器 */}
      <div ref={chartRef} className="w-full" style={{ height: '400px' }} />
    </div>
  );
};

export default NexusMetricsChart;
