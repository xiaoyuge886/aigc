
import React, { useState, useEffect } from 'react';
import { Copy, Check, X, Terminal, Maximize2, Minimize2 } from 'lucide-react';
import { GlassCard } from './GlassCard';

interface CodeViewerProps {
  code: string;
  language?: string;
  onClose: () => void;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({ code, language = 'text', onClose }) => {
  const [copied, setCopied] = useState(false);
  const [lines, setLines] = useState<string[]>([]);

  useEffect(() => {
    if (code) {
      setLines(code.split('\n'));
    }
  }, [code]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <GlassCard className="h-full flex flex-col overflow-hidden border-blue-200/50 shadow-2xl ring-1 ring-black/5 animate-fade-in" padding="p-0">
      {/* Window Header */}
      <div className="flex items-center justify-between px-3 md:px-4 py-2 md:py-3 bg-gray-50/90 backdrop-blur-xl border-b border-gray-200/80 select-none">
        <div className="flex items-center space-x-3 md:space-x-4">
          <div className="flex space-x-1 md:space-x-1.5 group">
            <button 
                onClick={onClose} 
                className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-[#FF5F57] border border-[#E0443E] flex items-center justify-center text-black/0 hover:text-black/50 transition-all"
            >
                {/* Fixed: Removed non-existent md:size prop */}
                <X size={8} strokeWidth={3} />
            </button>
            <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-[#FEBC2E] border border-[#D89E24]" />
            <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-[#28C840] border border-[#1AAB29]" />
          </div>
          <div className="h-3 md:h-4 w-px bg-gray-300 mx-1 md:mx-2"></div>
          <div className="flex items-center space-x-1.5 text-gray-600 overflow-hidden">
            {/* Fixed: Removed non-existent md:size prop */}
            <Terminal size={14} className="text-blue-500 flex-shrink-0" />
            <span className="text-[10px] md:text-xs font-semibold tracking-wide uppercase text-gray-500 font-mono truncate">
              {language || 'Untitled'}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-1 md:space-x-2">
            <button 
            onClick={handleCopy}
            className="p-1 md:p-1.5 hover:bg-white rounded-md transition-all text-gray-500 hover:text-blue-600"
            title="复制代码"
            >
            {/* Fixed: Removed non-existent md:size prop */}
            {copied ? <Check size={16} className="text-green-600" /> : <Copy size={16} />}
            </button>
        </div>
      </div>
      
      {/* Code Content */}
      <div className="flex-1 overflow-auto bg-[#1e1e1e] text-[11px] md:text-[13px] leading-5 md:leading-6 font-mono custom-scrollbar group relative">
        <div className="flex min-h-full">
            {/* Line Numbers */}
            <div className="flex flex-col items-end px-2 md:px-3 py-3 md:py-4 text-gray-600 bg-[#1e1e1e] select-none border-r border-gray-800/50 min-w-[2rem] md:min-w-[3rem]">
                {lines.map((_, i) => (
                    <span key={i} className="leading-5 md:leading-6 opacity-50">{i + 1}</span>
                ))}
            </div>
            
            {/* Code Text */}
            <div className="flex-1 p-3 md:p-4 pt-3 md:pt-4 overflow-x-auto">
                <pre className="font-mono text-gray-300 whitespace-pre tab-[2] md:tab-[4]">
                    <code>{code}</code>
                </pre>
            </div>
        </div>
      </div>
      
      {/* Footer Status */}
      <div className="px-3 md:px-4 py-1 bg-[#0071E3] text-white text-[9px] md:text-[10px] flex justify-between items-center">
        <span className="hidden sm:inline">UTF-8</span>
        <div className="flex items-center space-x-2 md:space-x-3">
            <span>Ln {lines.length}</span>
            <span className="opacity-70 uppercase">{language}</span>
        </div>
      </div>
    </GlassCard>
  );
};
