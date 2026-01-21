import React from 'react';
import { ChevronRight } from 'lucide-react';

// 推荐问题数据类型
export interface RecommendedQuestion {
  id: string;
  icon: string;
  title: string;
  question: string;
  gradient: string;
}

// 推荐问题数据
export const RECOMMENDED_QUESTIONS: RecommendedQuestion[] = [
  {
    id: 'q1',
    icon: '📊',
    title: '数据分析',
    question: '帮我分析当前项目的关键指标趋势',
    gradient: 'from-blue-500 to-cyan-500'
  },
  {
    id: 'q2',
    icon: '🎯',
    title: '策略优化',
    question: '基于现有数据提供优化建议',
    gradient: 'from-purple-500 to-pink-500'
  },
  {
    id: 'q3',
    icon: '💡',
    title: '创意生成',
    question: '为我的产品生成 5 个创新点子',
    gradient: 'from-orange-500 to-red-500'
  },
  {
    id: 'q4',
    icon: '🔍',
    title: '深度研究',
    question: '研究并总结最新的 AI 技术趋势',
    gradient: 'from-green-500 to-emerald-500'
  }
];

// 推荐问题悬浮卡片组件
export const RecommendationCard: React.FC<{
  item: RecommendedQuestion;
  index: number;
  onClick: () => void;
  isDisappearing: boolean;
}> = ({ item, index, onClick, isDisappearing }) => {
  return (
    <button
      onClick={onClick}
      disabled={isDisappearing}
      className={`group relative w-full bg-white/90 backdrop-blur-xl rounded-[20px] p-4 border border-black/[0.04] hover:border-blue-200 transition-all duration-500 hover:shadow-2xl hover:shadow-blue-500/10 hover:-translate-y-2 active:scale-[0.98] text-left overflow-hidden ${
        isDisappearing ? 'pointer-events-none' : ''
      }`}
      style={{
        animation: `${isDisappearing ? 'cardDisappear' : 'floatAnimation'} 0.6s cubic-bezier(0.16, 1, 0.3, 1) ${isDisappearing ? 0 : index * 0.08}s forwards, ${isDisappearing ? '' : 'float 3s ease-in-out infinite'}`,
        opacity: isDisappearing ? 1 : 0,
        transform: isDisappearing ? 'scale(1)' : 'translateY(15px)'
      }}
    >
      {/* 渐变背景装饰 */}
      <div className={`absolute inset-0 bg-gradient-to-br ${item.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-500`} />
      <div className={`absolute top-0 right-0 w-20 h-20 bg-gradient-to-br ${item.gradient} opacity-0 group-hover:opacity-10 blur-3xl transition-opacity duration-500`} />

      {/* 内容 */}
      <div className="relative">
        <div className="flex items-center space-x-3 mb-2">
          <div className={`inline-flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br ${item.gradient} text-white text-lg shadow-lg group-hover:scale-110 transition-transform duration-300`}>
            {item.icon}
          </div>
          <div className="flex-1">
            <h3 className="text-[13px] font-bold text-apple-gray group-hover:text-blue-600 transition-colors">
              {item.title}
            </h3>
          </div>
        </div>
        <p className="text-[11px] text-gray-500 leading-relaxed group-hover:text-gray-700 transition-colors pl-1">
          {item.question}
        </p>
        <div className="mt-2 flex items-center text-[9px] font-black uppercase tracking-widest text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300 transform translate-y-1 group-hover:translate-y-0">
          点击开始 <ChevronRight size={10} className="ml-1" />
        </div>
      </div>

      {/* 光效边框 */}
      <div className="absolute inset-0 rounded-[20px] bg-gradient-to-r from-transparent via-blue-400/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" style={{
        backgroundSize: '200% 100%',
        animation: 'shimmer 2s infinite'
      }} />
    </button>
  );
};
