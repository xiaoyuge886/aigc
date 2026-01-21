import React, { useRef, useEffect, useCallback, useState } from 'react';
import * as echarts from 'echarts';
import {
  LineChart, BarChart3, PieChart, GitGraph, Activity, Zap
} from 'lucide-react';

// --- 图表类型定义 ---
export type ChartType = 'line' | 'bar' | 'pie' | 'radar' | 'scatter' | 'effectScatter' | 'funnel' | 'gauge' | 'heatmap' | 'tree' | 'treemap' | 'sunburst' | 'graph' | 'sankey' | 'parallel';

export const CHART_CONFIGS: Record<ChartType, { icon: any; label: string; description: string }> = {
  line: { icon: LineChart, label: '折线图', description: '趋势分析' },
  bar: { icon: BarChart3, label: '柱状图', description: '数量对比' },
  pie: { icon: PieChart, label: '饼图', description: '占比分布' },
  radar: { icon: GitGraph, label: '雷达图', description: '多维评估' },
  scatter: { icon: Activity, label: '散点图', description: '相关性分析' },
  effectScatter: { icon: Zap, label: '动态散点', description: '带动画散点' },
  funnel: { icon: BarChart3, label: '漏斗图', description: '转化流程' },
  gauge: { icon: Activity, label: '仪表盘', description: '指标仪表' },
  heatmap: { icon: Activity, label: '热力图', description: '密度分布' },
  tree: { icon: GitGraph, label: '树形图', description: '层级结构' },
  treemap: { icon: BarChart3, label: '矩形树图', description: '占比层级' },
  sunburst: { icon: PieChart, label: '旭日图', description: '多级饼图' },
  graph: { icon: GitGraph, label: '关系图', description: '网络关系' },
  sankey: { icon: GitGraph, label: '桑基图', description: '流向分析' },
  parallel: { icon: BarChart3, label: '平行坐标', description: '多维对比' }
};

// --- Apple 风格精简 ECharts ---
export const AppleECharts: React.FC<{ option: any; chartType?: ChartType }> = ({ option, chartType = 'line' }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  // Listen for container size changes and auto-resize chart
  useEffect(() => {
    if (!chartRef.current || !chartInstance.current) return;
    const resizeObserver = new ResizeObserver(() => {
      chartInstance.current?.resize();
    });
    resizeObserver.observe(chartRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  const updateChart = useCallback((type: ChartType) => {
    if (!chartInstance.current || !option) {
      return;
    }
    
    try {
      const baseOption = JSON.parse(JSON.stringify(option));
      const appleColors = ['#007AFF', '#34C759', '#FF9500', '#5856D6', '#FF2D55', '#AF52DE'];
      
      const grid = {
        top: baseOption.title ? 80 : 40,
        bottom: 40,
        left: 20,
        right: 20,
        containLabel: true
      };

      const title = baseOption.title ? {
        ...baseOption.title,
        top: 10,
        left: 'center',
        textStyle: { 
          color: '#1D1D1F', 
          fontSize: 16, 
          fontWeight: 700,
          fontFamily: 'SF Pro Text, Inter, sans-serif'
        }
      } : undefined;

      const legend = {
        show: true,
        bottom: 0,
        left: 'center',
        itemWidth: 10,
        itemHeight: 10,
        icon: 'circle',
        textStyle: { color: '#86868B', fontSize: 11, fontWeight: 500 }
      };

      const xAxis = {
        ...baseOption.xAxis,
        axisLine: { show: true, lineStyle: { color: '#E5E5E7' } },
        axisLabel: { 
          color: '#86868B', 
          fontSize: 10,
          fontWeight: 500,
          interval: 'auto'
        },
        axisTick: { show: false },
        splitLine: { show: false }
      };

      const yAxis = {
        ...baseOption.yAxis,
        splitLine: { show: true, lineStyle: { color: '#F2F2F7', type: 'dashed' } },
        axisLabel: { color: '#86868B', fontSize: 10 },
        axisLine: { show: false }
      };

      let series: any[] = [];
      let specialConfig: any = {};

      if (type === 'pie') {
        const data = baseOption.series?.[0]?.data || [];
        const cats = baseOption.xAxis?.data || [];
        const pieData = data.map((v: any, i: number) => {
          if (typeof v === 'object') return v;
          return { value: v, name: cats[i] || `Item ${i+1}` };
        });

        series = [{
          type: 'pie',
          radius: ['40%', '65%'],
          center: ['50%', '50%'],
          itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
          label: { show: false },
          data: pieData
        }];
      } else if (type === 'radar') {
        // 雷达图配置
        const indicator = baseOption.xAxis?.data?.map((name: string) => ({
          name,
          max: Math.max(...(baseOption.series?.[0]?.data || [100]))
        })) || [{ name: '指标1', max: 100 }, { name: '指标2', max: 100 }];

        series = [{
          type: 'radar',
          data: (baseOption.series || []).map((s: any, idx: number) => ({
            value: s.data || s.data,
            name: s.name || `系列${idx + 1}`,
            itemStyle: { color: appleColors[idx % appleColors.length] }
          })),
          areaStyle: { opacity: 0.2 }
        }];

        specialConfig = {
          radar: {
            indicator,
            splitArea: { show: false },
            axisLine: { lineStyle: { color: '#E5E5E7' } },
            splitLine: { lineStyle: { color: '#F2F2F7', type: 'dashed' } }
          },
          xAxis: { show: false },
          yAxis: { show: false }
        };
      } else if (type === 'scatter' || type === 'effectScatter') {
        series = (baseOption.series || []).map((s: any, idx: number) => ({
          ...s,
          type,
          symbolSize: type === 'effectScatter' ? 20 : 10,
          rippleEffect: type === 'effectScatter' ? {
            brushType: 'stroke',
            scale: 3
          } : undefined,
          itemStyle: {
            color: appleColors[idx % appleColors.length],
            shadowBlur: 10,
            shadowColor: appleColors[idx % appleColors.length]
          }
        }));
      } else if (type === 'funnel') {
        series = [{
          type: 'funnel',
          left: '10%',
          top: 60,
          bottom: 60,
          width: '80%',
          min: 0,
          max: 100,
          minSize: '0%',
          maxSize: '100%',
          sort: 'descending',
          gap: 2,
          label: {
            show: true,
            position: 'inside',
            fontSize: 12,
            color: '#fff'
          },
          labelLine: {
            length: 10,
            lineStyle: { width: 1, type: 'solid' }
          },
          itemStyle: {
            borderColor: '#fff',
            borderWidth: 0
          },
          emphasis: {
            label: { fontSize: 14 }
          },
          data: (baseOption.series?.[0]?.data || []).map((v: any, i: number) => {
            if (typeof v === 'object') return v;
            const cats = baseOption.xAxis?.data || [];
            return { value: v, name: cats[i] || `Item ${i+1}` };
          })
        }];
        specialConfig = { xAxis: { show: false }, yAxis: { show: false } };
      } else if (type === 'gauge') {
        const value = baseOption.series?.[0]?.data?.[0] || 50;
        series = [{
          type: 'gauge',
          startAngle: 180,
          endAngle: 0,
          min: 0,
          max: 100,
          splitNumber: 10,
          itemStyle: { color: appleColors[0] },
          progress: {
            show: true,
            width: 18
          },
          pointer: {
            icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
            length: '12%',
            width: 20,
            offsetCenter: [0, '-60%'],
            itemStyle: { color: 'auto' }
          },
          axisLine: {
            lineStyle: {
              width: 18
            }
          },
          axisTick: { distance: -45, splitNumber: 5, lineStyle: { width: 1, color: '#999' } },
          splitLine: { distance: -52, length: 14, lineStyle: { width: 2, color: '#999' } },
          axisLabel: { distance: -20, color: '#999', fontSize: 12 },
          detail: {
            valueAnimation: true,
            formatter: '{value}%',
            color: 'auto',
            fontSize: 30,
            offsetCenter: [0, '20%']
          },
          data: [{ value, name: baseOption.title?.text || '指标' }]
        }];
        specialConfig = { xAxis: { show: false }, yAxis: { show: false } };
      } else if (type === 'heatmap') {
        series = [{
          type: 'heatmap',
          data: baseOption.series?.[0]?.data || [[0, 0, 10]],
          label: { show: true },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }];
        specialConfig = {
          visualMap: {
            min: 0,
            max: 100,
            calculable: true,
            orient: 'horizontal',
            left: 'center',
            bottom: '15%',
            inRange: { color: ['#50a3ba', '#eac736', '#d94e5d'] }
          }
        };
      } else {
        // line, bar, tree, treemap, sunburst, graph, sankey, parallel 等其他类型
        series = (baseOption.series || []).map((s: any, idx: number) => ({
          ...s,
          type,
          barMaxWidth: 40,
          smooth: type === 'line',
          symbol: 'circle',
          symbolSize: 6,
          itemStyle: {
            borderRadius: type === 'bar' ? [6, 6, 0, 0] : 0,
            color: appleColors[idx % appleColors.length]
          },
          lineStyle: { width: 3 },
          areaStyle: type === 'line' ? {
             opacity: 0.1,
             color: appleColors[idx % appleColors.length]
          } : null
        }));
      }

      chartInstance.current.setOption({
        ...baseOption,
        ...specialConfig,
        title, grid, legend,
        xAxis: (type === 'pie' || type === 'radar' || type === 'funnel' || type === 'gauge') ? { show: false } : xAxis,
        yAxis: (type === 'pie' || type === 'radar' || type === 'funnel' || type === 'gauge') ? { show: false } : yAxis,
        color: appleColors,
        backgroundColor: 'transparent',
        tooltip: { 
          trigger: type === 'pie' ? 'item' : 'axis',
          backgroundColor: 'rgba(255,255,255,0.9)',
          borderRadius: 12,
          borderWidth: 0,
          padding: 12,
          textStyle: { color: '#1d1d1f', fontSize: 12 },
          shadowBlur: 20,
          shadowColor: 'rgba(0,0,0,0.1)'
        },
        series: series, 
        animationDuration: 800
      }, true); // true = not merge, replace
      console.log('[AppleECharts] Chart option set successfully');
    } catch (err) {
      console.error('[AppleECharts] Error setting chart option:', err);
    }
  }, [option]);

  // 图表初始化 - 只运行一次
  useEffect(() => {
    console.log('[AppleECharts] Initialization useEffect running, chartRef.current:', chartRef.current);
    if (chartRef.current) {
      console.log('[AppleECharts] Initializing ECharts instance');
      chartInstance.current = echarts.init(chartRef.current);
      console.log('[AppleECharts] ECharts instance initialized:', chartInstance.current);

      return () => {
        console.log('[AppleECharts] Cleaning up ECharts instance');
        chartInstance.current?.dispose();
      };
    } else {
      console.error('[AppleECharts] chartRef.current is null during initialization!');
    }
  }, []); // 空依赖数组，只在挂载时运行

  // 图表更新 - 当 option 或 chartType 变化时运行
  useEffect(() => {
    console.log('[AppleECharts] Update useEffect running, chartInstance:', !!chartInstance.current, 'option:', !!option);
    if (chartInstance.current && option) {
      console.log('[AppleECharts] Calling updateChart with chartType:', chartType);
      updateChart(chartType);
    } else {
      console.error('[AppleECharts] Cannot update chart - instance or option missing', {
        hasInstance: !!chartInstance.current,
        hasOption: !!option
      });
    }
  }, [chartType, option, updateChart]);

  return (
    <div className="relative group/chart w-full animate-apple-slide">
      <div ref={chartRef} className="w-full h-[400px] rounded-[32px] border border-black/[0.04] bg-[#FBFBFD] p-4 shadow-sm" />
    </div>
  );
};

// --- 图表块组件 ---
export const ChartBlock: React.FC<{ chartOption: any; blockIdx: number }> = ({ chartOption, blockIdx }) => {
  const [chartType, setChartType] = useState<ChartType>('line');

  console.log(`[ChartBlock] blockIdx=${blockIdx}, chartOption=`, chartOption);
  console.log(`[ChartBlock] chartOption has title=`, !!chartOption?.title);
  console.log(`[ChartBlock] chartOption has series=`, !!chartOption?.series);

  return (
    <div className="my-8 animate-apple-fade">
      <div className="rounded-[24px] border border-gray-200/60 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] overflow-hidden">
        {/* Data Visualization 标题 */}
        <div className="px-5 py-3 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100 flex items-center space-x-2">
          <Activity size={14} className="text-blue-500" />
          <span className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Data Visualization</span>
        </div>
        {/* 图表类型切换按钮 */}
        <div className="px-5 py-3 border-b border-gray-100 flex flex-wrap gap-1.5 bg-white">
          {(Object.keys(CHART_CONFIGS) as ChartType[]).filter(t => t !== 'radar').slice(0, 6).map(t => {
            const config = CHART_CONFIGS[t];
            const IconComponent = config.icon;
            return (
              <button
                key={t}
                onClick={() => setChartType(t)}
                className={`p-2 rounded-lg transition-all flex items-center space-x-1.5 ${chartType === t ? 'bg-black text-white shadow-sm' : 'text-gray-400 hover:text-gray-900 hover:bg-gray-100'}`}
                title={`${config.label} - ${config.description}`}
              >
                <IconComponent size={12} />
                <span className="text-[9px] font-bold">{config.label}</span>
              </button>
            );
          })}
        </div>
        {/* 图表容器 */}
        <div className="p-6">
          <AppleECharts option={chartOption} chartType={chartType} />
        </div>
      </div>
    </div>
  );
};
