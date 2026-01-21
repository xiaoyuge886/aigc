
import React from 'react';
import { FileText, Download, Eye, FileJson, FileCode } from 'lucide-react';
import { GlassCard } from './GlassCard';

interface FilePreviewProps {
  content: string;
  title: string;
  type: 'document' | 'file-list';
  files?: any[];
}

export const FilePreview: React.FC<FilePreviewProps> = ({ content, title, type, files }) => {
  if (type === 'file-list') {
    return (
      <div className="space-y-2 md:space-y-3">
        {files?.map((f, i) => (
          <div key={i} className="flex items-center justify-between p-3 md:p-4 bg-white rounded-xl md:rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-all">
            <div className="flex items-center space-x-2 md:space-x-3">
              <div className="p-1.5 md:p-2 bg-blue-50 text-blue-600 rounded-lg md:rounded-xl">
                {/* Fixed: Removed non-existent md:size prop which caused TS errors */}
                {f.type.includes('image') ? <Eye size={18}/> : <FileText size={18}/>}
              </div>
              <div className="overflow-hidden">
                <p className="text-[12px] md:text-sm font-semibold text-gray-800 truncate max-w-[150px] md:max-w-none">{f.name}</p>
                <p className="text-[8px] md:text-[10px] text-gray-400 uppercase">{f.type}</p>
              </div>
            </div>
            {/* Fixed: Removed non-existent md:size prop */}
            <button className="p-1.5 text-gray-400 hover:text-blue-600 transition-colors">
              <Download size={16} />
            </button>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-white">
      <div className="max-w-5xl mx-auto p-6 md:p-8">
        <header className="mb-4 pb-3 border-b border-gray-200">
           <h1 className="text-lg md:text-xl font-semibold text-gray-900 tracking-tight mb-1">{title}</h1>
        </header>
        <div className="prose prose-slate max-w-none text-gray-700 leading-relaxed space-y-2">
           {content.split('\n').map((line, i) => {
             const trimmed = line.trim();
             if (trimmed.startsWith('# ')) return <h1 key={i} className="text-base md:text-lg font-semibold text-gray-900 mt-4 mb-2">{trimmed.replace('# ', '')}</h1>;
             if (trimmed.startsWith('## ')) return <h2 key={i} className="text-sm md:text-base font-semibold text-gray-800 mt-3 mb-1.5">{trimmed.replace('## ', '')}</h2>;
             if (trimmed.startsWith('### ')) return <h3 key={i} className="text-xs md:text-sm font-semibold text-gray-800 mt-2 mb-1">{trimmed.replace('### ', '')}</h3>;
             if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) return <li key={i} className="ml-4 list-disc text-xs md:text-sm">{trimmed.replace(/^[*\-] /, '')}</li>;
             if (trimmed.startsWith('```')) return null; // 跳过代码块标记，由 markdown 处理
             if (!trimmed) return <div key={i} className="h-1" />;
             return <p key={i} className="whitespace-pre-wrap text-xs md:text-sm leading-relaxed">{trimmed}</p>;
           })}
        </div>
      </div>
    </div>
  );
};
