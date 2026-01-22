
import React, { useState, useRef, useEffect } from 'react';
import { 
  Bot, RefreshCw, Wand2, Download, Save, ChevronDown, ChevronRight, 
  Bold, Italic, Underline, Strikethrough, AlignLeft, AlignCenter, AlignRight, AlignJustify,
  Image as ImageIcon, Link as LinkIcon, List, ListOrdered, Hash, Type, Plus, MoreHorizontal,
  Undo2, Redo2, Palette, Table, Code, Quote, Sparkles, Search, FileText, Loader2
} from 'lucide-react';
import { GoogleGenAI } from "@google/genai";

interface DocSection {
  id: string;
  level: 1 | 2 | 3;
  title: string;
  content: string;
}

export const Editor: React.FC = () => {
  const [activeNode, setActiveNode] = useState('1');
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [sections, setSections] = useState<DocSection[]>([
    { id: '1', level: 1, title: '引言', content: '在当前快速发展的数字化时代，智能助手平台已经成为提高个人和团队工作效率的核心工具。本项目旨在通过融合最先进的AI技术，重塑用户与数字内容的交互方式。' },
    { id: '1.1', level: 2, title: '项目背景', content: '项目开发的动机源于对生产力瓶颈的深度观察。我们发现，传统的数字化工具往往碎片化，缺乏统一的智能调度层。' },
    { id: '1.1.1', level: 3, title: '技术发展现状', content: '当前，生成式人工智能（AIGC）正在深刻改变内容生产的逻辑，从单纯的辅助工具进化为具备深度创作能力的数字合作伙伴。' },
    { id: '1.2', level: 2, title: '项目目标', content: '构建一个集智能对话、文档编辑、知识管理于一体的综合性AI协作平台。' },
    { id: '2', level: 1, title: '技术架构', content: '系统采用分布式架构，确保高可用性与可扩展性。' },
    { id: '2.1', level: 2, title: '前端架构', content: '采用 React 19 + TypeScript 的高规格开发链路，确保界面的高性能与类型安全。' },
    { id: '2.1.1', level: 3, title: '组件化设计', content: '通过原子化组件设计，实现极致的代码复用与灵活的界面扩展性。' },
    { id: '2.2', level: 2, title: 'AI集成', content: '通过高度抽象的中间层，实现对多款领先大语言模型的无缝切换。' },
    { id: '3', level: 1, title: '核心功能', content: '介绍平台最具竞争力的功能模块。' },
    { id: '3.1', level: 2, title: '智能写作辅助', content: 'AI驱动的实时纠错、逻辑优化与自动续写功能。' }
  ]);

  const editorRef = useRef<HTMLDivElement>(null);

  const applyCommand = (command: string, value?: string) => {
    document.execCommand(command, false, value);
  };

  const handleUpdate = (id: string, field: 'title' | 'content', value: string) => {
    setSections(prev => prev.map(s => s.id === id ? { ...s, [field]: value } : s));
  };

  const scrollToSection = (id: string) => {
    setActiveNode(id);
    const element = document.getElementById(`section-${id}`);
    if (element && editorRef.current) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleAiAssistance = async () => {
    const currentSection = sections.find(s => s.id === activeNode);
    if (!currentSection || isAiLoading) return;

    setIsAiLoading(true);
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const prompt = `你是一个专业的文档编辑器助手。请为以下文档章节进行“续写”或“深度扩写”。
      章节标题: ${currentSection.title}
      当前内容: ${currentSection.content}
      请直接提供续写的文字内容，不要包含任何多余的解释。`;

      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: prompt,
      });

      const newText = response.text;
      if (newText) {
        handleUpdate(activeNode, 'content', currentSection.content + '\n' + newText);
      }
    } catch (error) {
      console.error("AI Assistance failed:", error);
    } finally {
      setIsAiLoading(false);
    }
  };

  const renderOutline = () => {
    return sections.map((s) => (
      <div 
        key={s.id}
        onClick={() => scrollToSection(s.id)}
        className={`group flex items-center p-2 rounded-xl cursor-pointer transition-all ${activeNode === s.id ? 'bg-[#F2F6FF] ring-1 ring-[#0066CC]/10' : 'hover:bg-gray-50'}`}
        style={{ paddingLeft: `${(s.level - 1) * 16 + 8}px` }}
      >
        <div className="flex items-center space-x-3 flex-1 overflow-hidden">
          <div className={`w-5 h-5 flex-shrink-0 rounded-md flex items-center justify-center ${s.level === 1 ? 'bg-[#0066CC]' : 'bg-white border border-gray-200'}`}>
            {s.level === 1 ? <Type className="text-white" size={10} /> : <Hash className={s.level === 2 ? 'text-gray-600' : 'text-gray-400'} size={10} />}
          </div>
          <p className={`text-[13px] font-bold truncate ${activeNode === s.id ? 'text-[#0066CC]' : 'text-gray-700'}`}>
            <span className="opacity-40 mr-1 font-mono">{s.id}</span> {s.title}
          </p>
        </div>
      </div>
    ));
  };

  return (
    <div className="flex flex-col h-full bg-[#FBFBFD] animate-fade-in selection:bg-[#007AFF]/20 selection:text-[#007AFF]">
      <header className="h-16 px-6 bg-white border-b border-gray-100 flex items-center justify-between z-20 shadow-sm">
        <div className="flex items-center space-x-4">
           <div className="p-2 bg-gray-50 rounded-xl">
             <FileText className="text-blue-600" size={20} />
           </div>
           <div className="flex flex-col">
              <h2 className="text-lg font-black tracking-tight text-gray-900 leading-none">产品技术方案.docx</h2>
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mt-1">
                {sections.reduce((acc, s) => acc + s.title.length + s.content.length, 0)} 字符 • 自动保存
              </p>
           </div>
        </div>
        
        <div className="flex items-center space-x-3">
           <button className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-white border border-gray-100 hover:border-gray-200 text-xs font-bold text-gray-700 transition-all hover:bg-gray-50">
             <Download size={14} />
             <span>导出</span>
           </button>
           <button className="flex items-center space-x-2 px-6 py-2 rounded-xl bg-[#0066CC] text-white shadow-lg shadow-blue-500/20 text-xs font-bold transition-all hover:scale-105 active:scale-95">
             <Save size={14} />
             <span>立即保存</span>
           </button>
           <div className="h-6 w-px bg-gray-100 mx-2" />
           <button className="p-2 text-gray-400 hover:text-gray-900 transition-colors">
             <MoreHorizontal size={20} />
           </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-[280px] bg-white border-r border-gray-100 flex flex-col p-6 overflow-y-auto custom-scrollbar flex-shrink-0">
           <div className="flex items-center justify-between mb-8">
             <h3 className="text-[11px] font-black text-gray-400 uppercase tracking-[0.2em]">章节导航</h3>
             <div className="flex space-x-1">
                <button className="p-1.5 hover:bg-gray-50 rounded-lg text-gray-400 transition-colors"><Plus size={14} /></button>
             </div>
           </div>
           <div className="space-y-1">
             {renderOutline()}
           </div>
        </aside>

        <div className="flex-1 flex flex-col bg-white overflow-hidden relative">
          {/* Enhanced Rich Text Toolbar with Logic */}
          <div className="sticky top-0 z-10 px-6 py-2.5 bg-white/90 backdrop-blur-xl border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center space-x-0.5">
              <div className="flex items-center pr-2 mr-2 border-r border-gray-100">
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('undo'); }} title="撤销" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 transition-all"><Undo2 size={16}/></button>
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('redo'); }} title="重做" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 transition-all"><Redo2 size={16}/></button>
              </div>

              <div className="flex items-center space-x-0.5 pr-2 mr-2 border-r border-gray-100">
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('bold'); }} title="加粗" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 hover:text-blue-600 transition-all"><Bold size={16}/></button>
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('italic'); }} title="斜体" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 hover:text-blue-600 transition-all"><Italic size={16}/></button>
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('underline'); }} title="下划线" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 hover:text-blue-600 transition-all"><Underline size={16}/></button>
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('strikeThrough'); }} title="删除线" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 hover:text-blue-600 transition-all"><Strikethrough size={16}/></button>
              </div>

              <div className="flex items-center space-x-0.5 pr-2 mr-2 border-r border-gray-100">
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('insertUnorderedList'); }} title="无序列表" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 transition-all"><List size={16}/></button>
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('insertOrderedList'); }} title="有序列表" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 transition-all"><ListOrdered size={16}/></button>
              </div>

              <div className="flex items-center space-x-0.5 pr-2 mr-2 border-r border-gray-100">
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('justifyLeft'); }} title="左对齐" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 transition-all"><AlignLeft size={16}/></button>
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('justifyCenter'); }} title="居中对齐" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 transition-all"><AlignCenter size={16}/></button>
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('justifyRight'); }} title="右对齐" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 transition-all"><AlignRight size={16}/></button>
              </div>

              <div className="flex items-center space-x-0.5">
                <button onMouseDown={(e) => { e.preventDefault(); }} title="插入代码块" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 transition-all"><Code size={16}/></button>
                <button onMouseDown={(e) => { e.preventDefault(); applyCommand('formatBlock', 'blockquote'); }} title="插入引用" className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 transition-all"><Quote size={16}/></button>
              </div>
            </div>

            <button 
              onClick={handleAiAssistance}
              disabled={isAiLoading}
              className={`flex items-center space-x-2 px-4 py-2 ${isAiLoading ? 'bg-blue-100' : 'bg-blue-50'} text-blue-700 rounded-xl text-xs font-bold hover:bg-blue-100 transition-all border border-blue-100 shadow-sm relative overflow-hidden`}
            >
              {isAiLoading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  <span>AI 正在创作...</span>
                </>
              ) : (
                <>
                  <Sparkles size={14} className="animate-pulse" />
                  <span>AI 辅助续写</span>
                </>
              )}
            </button>
          </div>

          <div 
            ref={editorRef}
            className="flex-1 overflow-y-auto p-12 md:p-24 custom-scrollbar bg-[#FBFBFD] scroll-smooth"
          >
             <div className="max-w-4xl mx-auto bg-white min-h-[1200px] shadow-[0_10px_40px_-20px_rgba(0,0,0,0.1)] rounded-2xl border border-gray-100 p-16 md:p-24 space-y-16">
                {sections.map((s) => (
                  <section 
                    key={s.id} 
                    id={`section-${s.id}`} 
                    className={`group relative space-y-6 transition-all duration-300 ${activeNode === s.id ? 'opacity-100' : 'opacity-80'}`}
                    onFocus={() => setActiveNode(s.id)}
                  >
                    <div className="flex items-center space-x-3">
                      <div className="flex-1">
                        <div className="flex items-baseline space-x-4">
                          <span className="font-mono text-gray-200 text-sm select-none tracking-tighter">
                            {'#'.repeat(s.level)}
                          </span>
                          <h2 
                            contentEditable 
                            suppressContentEditableWarning
                            onBlur={(e) => handleUpdate(s.id, 'title', e.currentTarget.innerText || '')}
                            className={`
                              font-black tracking-tight text-[#1D1D1F] focus:outline-none w-full
                              ${s.level === 1 ? 'text-5xl mb-4' : s.level === 2 ? 'text-3xl' : 'text-xl'}
                            `}
                          >
                            {s.title}
                          </h2>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <div className="w-6 flex-shrink-0" />
                      <div 
                        contentEditable 
                        suppressContentEditableWarning
                        onBlur={(e) => handleUpdate(s.id, 'content', e.currentTarget.innerHTML || '')}
                        dangerouslySetInnerHTML={{ __html: s.content }}
                        className="flex-1 text-gray-600 leading-[1.8] text-lg focus:outline-none min-h-[1.5em] font-medium selection:bg-blue-100 outline-none"
                      />
                    </div>

                    {s.level === 1 && <div className="h-px bg-gray-50 w-full mt-12" />}
                  </section>
                ))}
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};
