
import React, { useState, useEffect } from 'react';
import { 
  Search, Star, Users, ArrowUpRight, ShieldCheck, 
  Briefcase, Palette, Code2, GraduationCap, Megaphone, UserCircle,
  Zap, Crown, ChevronRight, Play, Sparkles
} from 'lucide-react';
import { platformService, Skill } from '../services/platformService';

interface Skill {
  id: string;
  title: string;
  description: string;
  category: string;
  isPremium: boolean;
  rating: number;
  users: string;
  icon: React.ReactNode;
  tags: string[];
  author: string;
  color: string;
  gradient: string;
}

export const SkillMarket: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState('全部');
  const [searchQuery, setSearchQuery] = useState('');
  const [isVisible, setIsVisible] = useState(false);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsVisible(true);
    loadSkills();
  }, []);

  const loadSkills = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await platformService.listSkills();
      setSkills(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载技能失败');
      console.error('Failed to load skills:', err);
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    { name: '全部', icon: <Zap size={14} /> },
    { name: '商业助手', icon: <Briefcase size={14} /> },
    { name: '创意辅助', icon: <Palette size={14} /> },
    { name: '技术开发', icon: <Code2 size={14} /> },
    { name: '学术研究', icon: <GraduationCap size={14} /> },
    { name: '数字营销', icon: <Megaphone size={14} /> },
    { name: '私人助理', icon: <UserCircle size={14} /> },
  ];

  // Map API Skill to display format
  const getIconForCategory = (category: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      '商业助手': <Briefcase size={24} strokeWidth={1.5} />,
      '创意辅助': <Palette size={24} strokeWidth={1.5} />,
      '技术开发': <Code2 size={24} strokeWidth={1.5} />,
      '学术研究': <GraduationCap size={24} strokeWidth={1.5} />,
      '数字营销': <Megaphone size={24} strokeWidth={1.5} />,
      '私人助理': <UserCircle size={24} strokeWidth={1.5} />,
    };
    return iconMap[category] || <Sparkles size={24} strokeWidth={1.5} />;
  };

  const getColorForCategory = (category: string) => {
    const colorMap: Record<string, { color: string; gradient: string }> = {
      '商业助手': { color: 'text-blue-600', gradient: 'from-blue-500/20 to-blue-600/5' },
      '创意辅助': { color: 'text-rose-600', gradient: 'from-rose-500/20 to-rose-600/5' },
      '技术开发': { color: 'text-purple-600', gradient: 'from-purple-500/20 to-purple-600/5' },
      '学术研究': { color: 'text-indigo-600', gradient: 'from-indigo-500/20 to-indigo-600/5' },
      '数字营销': { color: 'text-amber-600', gradient: 'from-amber-500/20 to-amber-600/5' },
      '私人助理': { color: 'text-slate-700', gradient: 'from-slate-500/20 to-slate-600/5' },
    };
    return colorMap[category] || { color: 'text-gray-600', gradient: 'from-gray-500/20 to-gray-600/5' };
  };

  // Convert API skills to display format
  const displaySkills: Skill[] = skills.map((apiSkill) => {
    const category = apiSkill.category || '其他';
    const colors = getColorForCategory(category);
    return {
      id: apiSkill.skill_id,
      title: apiSkill.name,
      description: apiSkill.description || '',
      category: category,
      isPremium: apiSkill.is_default || false,
      rating: 4.5, // Default rating
      users: `${apiSkill.usage_count || 0}`,
      icon: getIconForCategory(category),
      tags: [category],
      author: '系统',
      color: colors.color,
      gradient: colors.gradient,
    };
  });

  const filteredSkills = displaySkills.filter(skill => {
    const matchesCategory = activeCategory === '全部' || skill.category === activeCategory;
    const matchesSearch = skill.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                         skill.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="flex-1 overflow-y-auto bg-white custom-scrollbar scroll-smooth selection:bg-blue-100 selection:text-blue-900">
      {/* Featured Hero Banner */}
      <section className="px-6 pt-16 pb-8">
        <div className={`max-w-7xl mx-auto transition-all duration-1000 transform ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
          <div className="relative rounded-[40px] overflow-hidden bg-[#1D1D1F] p-10 md:p-16 text-white group cursor-pointer shadow-2xl">
            {/* Background elements */}
            <div className="absolute top-0 right-0 w-2/3 h-full bg-gradient-to-l from-[#0066CC]/20 to-transparent pointer-events-none" />
            <div className="absolute -bottom-20 -right-20 w-80 h-80 bg-blue-500/10 blur-[100px] rounded-full group-hover:bg-blue-500/20 transition-all duration-700" />
            
            <div className="relative z-10 grid md:grid-cols-2 gap-12 items-center">
              <div className="space-y-8">
                <div className="flex items-center space-x-3 bg-white/10 w-fit px-4 py-1.5 rounded-full border border-white/10 backdrop-blur-md">
                   <Sparkles size={14} className="text-blue-400" />
                   <span className="text-[11px] font-black uppercase tracking-[0.2em] text-blue-100">本月推荐技能</span>
                </div>
                <h2 className="text-4xl md:text-6xl font-black tracking-tight leading-[0.9] text-white">
                  全自动<br />
                  <span className="text-blue-400">战略咨询引擎</span>
                </h2>
                <p className="text-lg text-gray-400 max-w-md font-medium leading-relaxed">
                  深度集成的商业大脑，能够在分钟级内完成传统咨询团队周级的工作量。覆盖 140+ 行业数据库。
                </p>
                <div className="flex items-center space-x-6 pt-4">
                   <button className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-black transition-all shadow-xl active:scale-95 flex items-center group/btn">
                     <span>立即开启</span>
                     <ArrowUpRight size={18} className="ml-2 group-hover/btn:-translate-y-0.5 group-hover/btn:translate-x-0.5 transition-transform" />
                   </button>
                   <button className="flex items-center space-x-3 text-white/60 hover:text-white transition-colors font-bold">
                     <div className="w-10 h-10 rounded-full border border-white/20 flex items-center justify-center">
                       <Play size={14} className="fill-current" />
                     </div>
                     <span>查看演示</span>
                   </button>
                </div>
              </div>
              
              <div className="hidden md:flex justify-end">
                <div className="relative w-80 h-80 flex items-center justify-center">
                  <div className="absolute inset-0 border-2 border-dashed border-white/5 rounded-full animate-[spin_30s_linear_infinite]" />
                  <div className="w-48 h-48 bg-white/5 backdrop-blur-3xl rounded-[40px] border border-white/10 flex items-center justify-center shadow-2xl transform rotate-12 group-hover:rotate-6 transition-all duration-700">
                    <ShieldCheck size={80} strokeWidth={1} className="text-blue-400" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Market Grid */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Navigation & Search Bar */}
        <div className={`flex flex-col md:flex-row md:items-center justify-between gap-8 mb-16 transition-all duration-1000 delay-300 transform ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
          <div className="space-y-2">
            <h3 className="text-2xl font-black text-[#1D1D1F] tracking-tight">探索技能库</h3>
            <p className="text-[#86868B] font-medium text-sm">X 全球技能生态系统，助力无限生产力。</p>
          </div>
          
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <nav className="flex items-center p-1.5 bg-[#F5F5F7] rounded-2xl border border-[#D2D2D7]/20">
              {categories.slice(0, 4).map((cat) => (
                <button
                  key={cat.name}
                  onClick={() => setActiveCategory(cat.name)}
                  className={`px-6 py-2 rounded-xl text-xs font-black transition-all whitespace-nowrap uppercase tracking-wider ${
                    activeCategory === cat.name
                      ? 'bg-white text-[#0066CC] shadow-md shadow-black/5'
                      : 'text-[#86868B] hover:text-[#1D1D1F]'
                  }`}
                >
                  {cat.name}
                </button>
              ))}
              <button className="p-2 text-[#86868B] hover:text-[#1D1D1F]">
                <ChevronRight size={16} />
              </button>
            </nav>

            <div className="relative w-full sm:w-64 group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[#D2D2D7] group-focus-within:text-[#0066CC] transition-colors" size={16} />
              <input 
                type="text" 
                placeholder="搜索技能..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-11 pr-4 py-3 bg-[#F5F5F7] border border-transparent rounded-2xl text-[13px] font-bold focus:outline-none focus:bg-white focus:border-[#D2D2D7]/50 focus:shadow-xl transition-all placeholder-[#D2D2D7]"
              />
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-32">
            <div className="w-12 h-12 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <p className="text-red-600 font-bold">{error}</p>
          </div>
        )}

        {/* Skill Cards Grid */}
        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {filteredSkills.map((skill, index) => (
            <div 
              key={skill.id}
              className={`group bg-white rounded-[40px] p-8 border border-[#D2D2D7]/30 hover:border-[#0066CC]/20 hover:shadow-[0_40px_100px_-20px_rgba(0,0,0,0.06)] transition-all duration-700 transform ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}
              style={{ transitionDelay: `${index * 100 + 400}ms` }}
            >
              <div className="flex justify-between items-start mb-10">
                <div className={`w-16 h-16 bg-gradient-to-br ${skill.gradient} rounded-[24px] flex items-center justify-center ${skill.color} shadow-sm group-hover:scale-110 group-hover:shadow-lg transition-all duration-500`}>
                  {skill.icon}
                </div>
                {skill.isPremium && (
                  <div className="bg-[#FFF8E1] border border-[#FFE082]/30 px-3 py-1 rounded-full flex items-center space-x-1.5 shadow-sm">
                    <Crown size={12} className="text-[#FFA000]" />
                    <span className="text-[10px] font-black text-[#FFA000] uppercase tracking-widest">PRO</span>
                  </div>
                )}
              </div>

              <div className="space-y-4 mb-10">
                <div className="flex items-center justify-between">
                  <h4 className="text-xl font-black text-[#1D1D1F] tracking-tight group-hover:text-[#0066CC] transition-colors">
                    {skill.title}
                  </h4>
                  <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="text-[10px] font-black text-[#0066CC] uppercase tracking-wider">查看详情</span>
                    <ArrowUpRight size={12} className="text-[#0066CC]" />
                  </div>
                </div>
                
                <p className="text-[14px] text-[#86868B] font-medium leading-relaxed h-12 line-clamp-2">
                  {skill.description}
                </p>

                <div className="flex flex-wrap gap-2 pt-2">
                  {skill.tags.map(tag => (
                    <span key={tag} className="text-[10px] font-bold text-[#86868B] bg-[#F5F5F7] px-2.5 py-1 rounded-lg uppercase tracking-wider border border-transparent group-hover:border-[#D2D2D7]/30 transition-all">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-auto pt-6 border-t border-[#D2D2D7]/10 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-1">
                    <Star size={12} className="text-[#FF9500] fill-[#FF9500]" />
                    <span className="text-xs font-black text-[#1D1D1F]">{skill.rating}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Users size={12} className="text-[#86868B]" />
                    <span className="text-xs font-bold text-[#86868B]">{skill.users}</span>
                  </div>
                </div>
                
                <button className="px-5 py-2.5 bg-[#1D1D1F] text-white rounded-xl text-xs font-black hover:bg-[#0066CC] transition-all transform active:scale-95 shadow-md hover:shadow-blue-500/20">
                  启用技能
                </button>
              </div>
            </div>
          ))}
          </div>
        )}

        {!loading && !error && filteredSkills.length === 0 && (
          <div className="py-32 text-center animate-fade-in">
             <div className="w-20 h-20 bg-[#F5F5F7] rounded-[40px] flex items-center justify-center mx-auto mb-8">
               <Search size={32} className="text-[#D2D2D7]" />
             </div>
             <p className="text-xl text-[#1D1D1F] font-black mb-2">未找到匹配技能</p>
             <p className="text-[#86868B] font-medium mb-8">尝试更改搜索词或选择不同的分类。</p>
             <button 
               onClick={() => {setActiveCategory('全部'); setSearchQuery('');}}
               className="px-8 py-3 bg-[#1D1D1F] text-white rounded-2xl font-black text-sm transition-all hover:bg-black active:scale-95"
             >
               重置筛选器
             </button>
          </div>
        )}
      </div>

      {/* Promotional Bottom Section */}
      <section className="py-32 bg-[#FBFBFD] px-6">
        <div className="max-w-5xl mx-auto rounded-[60px] bg-gradient-to-br from-[#0066CC] to-[#004499] p-12 md:p-24 text-center space-y-12 shadow-2xl relative overflow-hidden group">
           {/* Visual Flourish */}
           <div className="absolute top-0 right-0 w-80 h-80 bg-white/10 blur-[80px] rounded-full -translate-y-1/2 translate-x-1/2 group-hover:scale-150 transition-transform duration-1000" />
           
           <h2 className="text-4xl md:text-6xl font-black text-white leading-[0.9] tracking-tight relative z-10">
             开发者？<br />
             <span className="opacity-60">发布您的专属技能。</span>
           </h2>
           
           <p className="text-xl text-blue-100 max-w-xl mx-auto font-medium relative z-10 opacity-80">
             加入 X 全球开发者生态，将您的 AI 创意转化为触手可及的企业级生产力工具。
           </p>
           
           <div className="flex flex-col sm:flex-row items-center justify-center gap-6 relative z-10">
             <button className="px-10 py-5 bg-white text-[#0066CC] rounded-2xl font-black text-lg transition-all hover:shadow-xl hover:scale-105 active:scale-95">
               开始构建
             </button>
             <button className="text-white font-bold text-lg hover:underline underline-offset-8 transition-all">
               查看开发者文档
             </button>
           </div>
        </div>
      </section>

      {/* Minimalist Tech Footer */}
      <footer className="py-24 px-6 bg-white border-t border-[#D2D2D7]/20">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center text-[#86868B] text-[10px] font-black uppercase tracking-[0.3em]">
          <div className="flex items-center space-x-3 mb-12 md:mb-0 transition-opacity hover:opacity-100 opacity-60">
            <div className="w-8 h-8 bg-[#1D1D1F] rounded-lg flex items-center justify-center text-white text-xs">AI</div>
            <span className="text-sm font-black text-[#1D1D1F] tracking-tight">X SKILL MARKET</span>
          </div>
          <div className="flex flex-wrap justify-center gap-12 mb-12 md:mb-0">
            <a href="#" className="hover:text-[#1D1D1F] transition-colors">技能提报</a>
            <a href="#" className="hover:text-[#1D1D1F] transition-colors">API 支持</a>
            <a href="#" className="hover:text-[#1D1D1F] transition-colors">企业准入</a>
            <a href="#" className="hover:text-[#1D1D1F] transition-colors">服务条款</a>
          </div>
          <p className="opacity-30 tracking-normal font-medium italic">Powered by X Intelligent Core © 2025</p>
        </div>
      </footer>
    </div>
  );
};
