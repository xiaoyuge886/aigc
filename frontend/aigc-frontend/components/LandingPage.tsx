
import React from 'react';
import { Sparkles, MessageSquare, Zap, BarChart3, ChevronRight, Play, Globe, Shield, Cpu, ArrowUpRight } from 'lucide-react';
import { GlassCard } from './GlassCard';

interface LandingPageProps {
  onStartChat: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onStartChat }) => {
  return (
    <div className="flex-1 overflow-y-auto bg-white custom-scrollbar scroll-smooth">
      {/* Hero Section */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden pt-12 md:pt-0">
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-[-10%] right-[10%] w-[800px] h-[800px] bg-blue-50/50 rounded-full blur-[140px] mix-blend-multiply animate-pulse" />
          <div className="absolute bottom-[-10%] left-[-5%] w-[600px] h-[600px] bg-purple-50/40 rounded-full blur-[120px] mix-blend-multiply" />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:64px_64px]" />
        </div>

        <div className="max-w-7xl w-full grid lg:grid-cols-2 gap-16 items-center z-10 relative">
          <div className="flex flex-col space-y-10 animate-slide-up">
            <div className="inline-flex items-center space-x-2 bg-gray-900 px-4 py-1.5 rounded-full w-fit group cursor-default transition-all hover:bg-black">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
              </span>
              <span className="text-[11px] font-extrabold text-white tracking-[0.1em] uppercase">X v1.1 已发布</span>
              <ArrowUpRight size={14} className="text-gray-400 group-hover:text-white transition-colors" />
            </div>

            <h1 className="text-6xl md:text-8xl font-black text-gray-900 leading-[0.95] tracking-[-0.04em]">
              重塑智能<br />
              <span className="relative inline-block mt-2">
                工作范式
                <div className="absolute -bottom-2 left-0 w-full h-2 bg-blue-600/10 rounded-full" />
              </span>
            </h1>

            <p className="text-xl md:text-2xl text-gray-500 leading-relaxed max-w-lg font-medium tracking-tight">
              X AI 融合顶尖 AIGC 技术，为专业人士提供超越极限的创作生产力。每一个像素、每一行代码，皆由智慧驱动。
            </p>

            <div className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-8">
              <button 
                onClick={onStartChat}
                className="w-full sm:w-auto px-10 py-5 bg-gray-900 text-white rounded-2xl font-bold text-lg hover:bg-black transition-all shadow-2xl hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center group"
              >
                <span>立即开启</span>
                <ChevronRight size={22} className="ml-2 group-hover:translate-x-1 transition-transform" />
              </button>
              
              <button className="flex items-center space-x-3 text-gray-900 font-bold hover:text-blue-600 transition-colors py-4 px-2 group">
                <span className="w-12 h-12 rounded-full border border-gray-200 flex items-center justify-center group-hover:border-blue-200 group-hover:bg-blue-50 transition-all shadow-sm">
                  <Play size={18} className="fill-current ml-1" />
                </span>
                <span className="text-lg">观摩演示视频</span>
              </button>
            </div>

            <div className="pt-8 flex flex-col space-y-4">
              <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">赋能全球顶尖团队</span>
              <div className="flex items-center space-x-8 opacity-40 grayscale hover:grayscale-0 transition-all duration-500 cursor-default">
                 <div className="flex items-center space-x-1 font-bold text-gray-900 text-lg italic"><Globe size={20}/> <span>GLOBAL</span></div>
                 <div className="font-black text-gray-900 text-xl tracking-tighter">TECH_CORP</div>
                 <div className="font-serif text-gray-900 text-xl font-bold">Lumina</div>
              </div>
            </div>
          </div>

          <div className="relative hidden lg:block h-[600px] perspective-1000">
            <div className="relative h-full flex items-center justify-center">
               <div className="absolute w-[500px] h-[500px] border border-dashed border-gray-200 rounded-full animate-[spin_60s_linear_infinite]" />
               <div className="absolute w-[350px] h-[350px] border border-gray-100 rounded-full" />
               
               <div className="relative z-10 w-[420px] h-[540px] bg-white border border-gray-200 rounded-[48px] shadow-[0_40px_100px_-20px_rgba(0,0,0,0.12)] p-10 flex flex-col space-y-8 transform hover:rotate-y-12 transition-transform duration-1000 ease-out group">
                  <div className="flex items-center justify-between">
                    <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                      <Cpu size={24} className="text-white" />
                    </div>
                    <div className="flex -space-x-2">
                       {[1,2,3].map(i => (
                         <div key={i} className={`w-8 h-8 rounded-full border-2 border-white bg-gray-${i*100} shadow-sm`} />
                       ))}
                    </div>
                  </div>
                  
                  <div className="flex-1 space-y-6">
                    <div className="space-y-3">
                      <div className="h-2.5 bg-gray-100 rounded-full w-2/3 group-hover:w-full transition-all duration-700" />
                      <div className="h-2.5 bg-gray-50 rounded-full w-full" />
                    </div>

                    <div className="p-6 bg-[#F9F9FB] rounded-3xl border border-gray-100 space-y-4 shadow-sm group-hover:border-blue-100 transition-colors">
                      <div className="flex items-center justify-between">
                         <div className="h-3 bg-blue-200 rounded-full w-1/4" />
                         <span className="text-[10px] font-bold text-blue-500">REALTIME</span>
                      </div>
                      <div className="flex items-end space-x-1 h-12">
                         {[40, 70, 45, 90, 65, 80, 50].map((h, i) => (
                           <div key={i} style={{height: `${h}%`}} className="flex-1 bg-blue-500/20 rounded-t-sm group-hover:bg-blue-500/40 transition-all" />
                         ))}
                      </div>
                    </div>
                    
                    <div className="space-y-4 pt-4">
                       <div className="flex items-center space-x-3">
                          <div className="w-2 h-2 rounded-full bg-green-500" />
                          <span className="text-[12px] font-bold text-gray-500">核心引擎就绪</span>
                       </div>
                       <div className="flex items-center space-x-3">
                          <div className="w-2 h-2 rounded-full bg-blue-500" />
                          <span className="text-[12px] font-bold text-gray-500">多模态链路解析中...</span>
                       </div>
                    </div>
                  </div>

                  <div className="h-14 bg-gray-50 border border-gray-100 rounded-2xl flex items-center px-5 group-hover:bg-white group-hover:shadow-inner transition-all">
                    <div className="h-2 bg-gray-200 rounded-full w-full" />
                    <Sparkles size={16} className="text-blue-500 ml-3" />
                  </div>
               </div>

               <div className="absolute -right-12 top-[20%] animate-[bounce_6s_ease-in-out_infinite]">
                 <GlassCard className="px-6 py-4 flex items-center space-x-3 shadow-2xl border-white/90">
                    <BarChart3 size={20} className="text-blue-600" />
                    <span className="text-sm font-black text-gray-900 italic">PRO_ANALYTICS</span>
                 </GlassCard>
               </div>
               
               <div className="absolute -left-16 bottom-[15%] animate-[bounce_8s_ease-in-out_infinite_1s]">
                 <GlassCard className="px-6 py-4 flex items-center space-x-3 shadow-2xl border-white/90">
                    <Shield size={20} className="text-green-600" />
                    <span className="text-sm font-black text-gray-900 tracking-tighter">ENTERPRISE_READY</span>
                 </GlassCard>
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* Value Proposition Bento Grid */}
      <section className="py-32 px-6 bg-white border-y border-gray-100">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 bg-[#F9F9FB] rounded-[48px] p-12 flex flex-col justify-between group hover:shadow-xl transition-all duration-500">
               <div className="max-w-md">
                 <h2 className="text-4xl font-black text-gray-900 mb-6 tracking-tight">不仅仅是 AI，更是您的数字大脑。</h2>
                 <p className="text-lg text-gray-500 font-medium">深度集成上下文记忆与多维知识库，X为您提供具备深度思考能力的专属助手。</p>
               </div>
               <div className="mt-12 flex items-center space-x-6">
                  <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-600 w-3/4 group-hover:w-full transition-all duration-1000" />
                  </div>
                  <span className="text-sm font-bold text-gray-400">效率提升 300%</span>
               </div>
            </div>
            
            <div className="lg:col-span-4 bg-gray-900 rounded-[48px] p-12 text-white flex flex-col justify-between hover:bg-black transition-all">
               <Zap size={40} className="text-blue-400 fill-blue-400" />
               <div className="space-y-4">
                 <h3 className="text-2xl font-bold">极速响应</h3>
                 <p className="text-gray-400 text-sm leading-relaxed">毫秒级推理速度，即刻捕捉每一个闪现的灵感。再也不用等待，创作随心而动。</p>
               </div>
            </div>

            <div className="lg:col-span-4 bg-white border border-gray-200 rounded-[48px] p-10 flex flex-col justify-between hover:border-blue-500/30 transition-all">
               <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600">
                 <MessageSquare size={28} />
               </div>
               <div className="mt-8 space-y-2">
                 <h3 className="text-xl font-bold text-gray-900">自然交互</h3>
                 <p className="text-gray-500 text-sm leading-relaxed">理解幽微语境，像与人类专家交谈一样自然、准确、高效。</p>
               </div>
            </div>

            <div className="lg:col-span-8 bg-[#F5F7FA] rounded-[48px] p-10 flex items-center justify-between group overflow-hidden">
               <div className="max-w-xs z-10">
                 <h3 className="text-2xl font-bold text-gray-900 mb-2">全球化视野</h3>
                 <p className="text-gray-500 text-sm">实时检索全球咨询，为您提供跨地域、跨语言的战略洞察。</p>
               </div>
               <div className="relative w-48 h-48 flex-shrink-0">
                  <Globe size={180} className="text-blue-100 absolute -right-10 group-hover:rotate-12 transition-transform duration-1000" />
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* Detailed Features Marquee / Showcase */}
      <section className="py-24 overflow-hidden bg-gray-50">
        <div className="max-w-7xl mx-auto px-6 mb-12 flex justify-between items-end">
          <div className="space-y-4">
            <h2 className="text-3xl md:text-5xl font-black text-gray-900 tracking-tight">专业工具，极致打磨</h2>
            <p className="text-lg text-gray-400 font-medium">适配各种复杂商业场景，助力企业实现数智化转型。</p>
          </div>
          <button className="hidden md:flex items-center space-x-2 text-blue-600 font-bold hover:underline">
            <span>探索所有功能</span>
            <ChevronRight size={18} />
          </button>
        </div>
        
        <div className="flex space-x-6 px-6 animate-[scroll_40s_linear_infinite] w-max">
           {[
             {t: '精准文案', d: '品牌级公关稿与营销文案'},
             {t: '智能代码', d: '高效重构与跨语言开发'},
             {t: '商业分析', d: '自动生成 PPT 与数据图表'},
             {t: '创意视觉', d: '高质量海报与设计灵感生成'},
             {t: '即时翻译', d: '专业级别的多语言同传支持'},
             {t: '精准文案', d: '品牌级公关稿与营销文案'},
             {t: '智能代码', d: '高效重构与跨语言开发'},
           ].map((item, i) => (
             <div key={i} className="w-80 bg-white p-8 rounded-[32px] border border-gray-100 shadow-sm hover:shadow-lg transition-all flex flex-shrink-0 flex-col">
               <h4 className="text-lg font-bold text-gray-900 mb-2">{item.t}</h4>
               <p className="text-sm text-gray-500 leading-relaxed">{item.d}</p>
             </div>
           ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-6">
        <div className="max-w-5xl mx-auto bg-gray-900 rounded-[64px] p-12 md:p-24 text-center space-y-12 relative overflow-hidden group">
           <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-blue-600/20 to-transparent pointer-events-none" />
           
           <h2 className="text-4xl md:text-6xl font-black text-white leading-tight z-10 relative">
             现在就让智能<br />提升您的商业价值。
           </h2>
           
           <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-8 z-10 relative">
             <button 
              onClick={onStartChat}
              className="px-12 py-5 bg-white text-gray-900 rounded-2xl font-black text-xl hover:bg-gray-100 transition-all hover:scale-105 active:scale-95"
             >
               立即免费试用
             </button>
             <button className="text-white font-bold text-lg hover:underline underline-offset-8">
               咨询企业定制方案
             </button>
           </div>
           
           <div className="pt-12 border-t border-white/10 flex flex-wrap justify-center gap-8 text-white/40 text-xs font-bold uppercase tracking-[0.2em]">
              <span>ISO 27001 认证</span>
              <span>数据加密保护</span>
              <span>24/7 专属支持</span>
           </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-20 px-6 border-t border-gray-100 bg-white">
        <div className="max-w-7xl mx-auto grid md:grid-cols-4 gap-12 mb-16">
          <div className="col-span-2 space-y-6">
             <div className="flex items-center space-x-2">
                <div className="text-2xl">✍️</div>
                <span className="text-2xl font-black text-gray-900 tracking-tighter">X AI</span>
             </div>
             <p className="text-gray-400 text-sm max-w-xs leading-relaxed">
               X AI 致力于通过前沿的人工智能技术，构建人类与机器协作的最佳形态。赋能每一份创造力。
             </p>
          </div>
          <div className="space-y-6">
            <h5 className="font-bold text-gray-900 uppercase tracking-widest text-[11px]">产品</h5>
            <ul className="space-y-3 text-sm text-gray-500 font-medium">
               <li><a href="#" className="hover:text-blue-600 transition-colors">核心助手</a></li>
               <li><a href="#" className="hover:text-blue-600 transition-colors">企业版</a></li>
               <li><a href="#" className="hover:text-blue-600 transition-colors">API 接口</a></li>
               <li><a href="#" className="hover:text-blue-600 transition-colors">最新动态</a></li>
            </ul>
          </div>
          <div className="space-y-6">
            <h5 className="font-bold text-gray-900 uppercase tracking-widest text-[11px]">关于</h5>
            <ul className="space-y-3 text-sm text-gray-500 font-medium">
               <li><a href="#" className="hover:text-blue-600 transition-colors">隐私政策</a></li>
               <li><a href="#" className="hover:text-blue-600 transition-colors">服务条款</a></li>
               <li><a href="#" className="hover:text-blue-600 transition-colors">联系团队</a></li>
               <li><a href="#" className="hover:text-blue-600 transition-colors">加入我们</a></li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center text-gray-400 text-xs font-bold uppercase tracking-widest">
          <div className="flex items-center space-x-2">
            <span>© 2025 X Intelligent Technology.</span>
                    </div>
          <div className="flex space-x-6 mt-4 md:mt-0">
             <a href="#" className="hover:text-gray-900 transition-colors">Twitter</a>
             <a href="#" className="hover:text-gray-900 transition-colors">LinkedIn</a>
             <a href="#" className="hover:text-gray-900 transition-colors">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
};
