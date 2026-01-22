import React from 'react';
import { FileText, ArrowLeft } from 'lucide-react';
import { FilePreview } from '../../FilePreview';
import { CodeViewer } from '../../CodeViewer';
import { getFileContent } from '../../../services/agentService';

interface FileInfo {
  id: string;
  name: string;
  path?: string;
  url?: string;
  size?: number;
  type?: string;
  conversation_turn_id?: string;
  created_at?: Date;
}

interface PreviewFile {
  id: string;
  name: string;
  type: 'code' | 'document';
  content: string;
  lang: string;
}

interface FilesTabProps {
  files: FileInfo[];
  selectedTurnId: string | null;
  previewFile: PreviewFile | null;
  onSetPreviewFile: (file: PreviewFile | null) => void;
  onGetFileContent: (path: string) => Promise<{ content: string }>;
}

/**
 * 文件标签页组件
 * 显示当前会话的文件列表，支持文件预览
 */
export const FilesTab: React.FC<FilesTabProps> = ({
  files,
  selectedTurnId,
  previewFile,
  onSetPreviewFile,
  onGetFileContent,
}) => {
  // 根据 selectedTurnId 过滤文件列表
  const savedTurnId = typeof window !== 'undefined' ? localStorage.getItem('selected_conversation_turn_id') : null;
  const effectiveTurnId = selectedTurnId || savedTurnId;

  const filteredFiles = effectiveTurnId
    ? files.filter(file => {
        const fileTurnId = file.conversation_turn_id || '';
        const effectiveTurnIdStr = String(effectiveTurnId || '');
        return fileTurnId === effectiveTurnIdStr;
      })
    : files;

  console.log('%c📁 [库标签页] 文件过滤:', 'color: #5856D6; font-weight: bold', {
    total_files: files.length,
    filtered_files: filteredFiles.length,
    effectiveTurnId: effectiveTurnId,
    selectedTurnId: selectedTurnId,
    savedTurnId: savedTurnId,
    files_by_turn_id: files.reduce((acc, f) => {
      const tid = f.conversation_turn_id || 'none';
      acc[tid] = (acc[tid] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  });

  if (previewFile) {
    return (
      <div className="flex flex-col h-full animate-apple-slide">
        <button
          onClick={() => onSetPreviewFile(null)}
          className="mb-4 flex items-center space-x-2 text-[11px] font-semibold uppercase tracking-wider text-blue-600 hover:translate-x-[-2px] transition-transform"
        >
          <ArrowLeft size={16} /> <span>返回库目录</span>
        </button>
        <div className="flex-1 rounded-2xl overflow-hidden border border-gray-200 bg-white shadow-lg">
          {previewFile.type === 'code' ? (
            <CodeViewer code={previewFile.content} language={previewFile.lang} onClose={() => onSetPreviewFile(null)} />
          ) : (
            <FilePreview content={previewFile.content} title={previewFile.name} type="document" />
          )}
        </div>
      </div>
    );
  }

  if (filteredFiles.length === 0) {
    return (
      <div className="text-center py-24">
        <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-gray-100 flex items-center justify-center">
          <FileText size={32} className="text-gray-300" />
        </div>
        <p className="text-[15px] text-[#86868B] font-medium tracking-tight">
          {effectiveTurnId ? `当前轮次 (${effectiveTurnId.substring(0, 8)}...) 暂无文件` : '暂无文件'}
        </p>
      </div>
    );
  }

  // 获取文件图标
  const getFileIcon = (fileName: string, fileType?: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    if (fileType?.includes('image')) return '🖼️';
    if (ext === 'pdf') return '📄';
    if (['md', 'txt'].includes(ext || '')) return '📝';
    if (['py', 'js', 'ts', 'tsx', 'jsx', 'java', 'cpp', 'c'].includes(ext || '')) return '💻';
    if (['xlsx', 'xls', 'csv'].includes(ext || '')) return '📊';
    if (['pptx', 'ppt'].includes(ext || '')) return '📽️';
    return '📄';
  };

  // 格式化文件大小
  const formatFileSize = (size?: number) => {
    if (!size) return '未知';
    if (size < 1024) return `${size}B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)}KB`;
    return `${(size / (1024 * 1024)).toFixed(2)}MB`;
  };

  // 格式化日期
  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return '今天';
    if (days === 1) return '昨天';
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="max-w-7xl mx-auto h-full animate-apple-fade">
      <div className="space-y-8">
        <div className="space-y-1">
          {/* 列表头部 */}
          <div className="px-4 py-3 mb-2 border-b border-gray-200/80">
            <div className="flex items-center justify-between">
              <p className="text-[13px] font-semibold text-[#1D1D1F] tracking-tight">文件列表</p>
              <p className="text-[12px] text-[#86868B] font-medium tracking-tight">{filteredFiles.length} 个文件</p>
            </div>
          </div>

          {/* 文件列表 */}
          {filteredFiles.map((file) => (
            <div
              key={file.id}
              onClick={async () => {
                if (file.url) {
                  window.open(file.url, '_blank');
                } else if (file.path) {
                  // 本地文件预览（从后端加载内容）
                  try {
                    onSetPreviewFile({
                      id: file.id,
                      name: file.name,
                      type: 'document',
                      content: '加载中...',
                      lang: 'text',
                    });

                    const fileData = await onGetFileContent(file.path);

                    // 判断文件类型
                    const isCodeFile =
                      file.type?.includes('code') ||
                      file.path.endsWith('.py') ||
                      file.path.endsWith('.js') ||
                      file.path.endsWith('.ts') ||
                      file.path.endsWith('.tsx') ||
                      file.path.endsWith('.jsx') ||
                      file.path.endsWith('.java') ||
                      file.path.endsWith('.cpp') ||
                      file.path.endsWith('.c');

                    onSetPreviewFile({
                      id: file.id,
                      name: file.name,
                      type: isCodeFile ? 'code' : 'document',
                      content: fileData.content,
                      lang: file.path.split('.').pop() || 'text',
                    });
                  } catch (error) {
                    console.error('读取文件失败:', error);
                    onSetPreviewFile({
                      id: file.id,
                      name: file.name,
                      type: 'document',
                      content: `读取文件失败: ${error instanceof Error ? error.message : '未知错误'}`,
                      lang: 'text',
                    });
                  }
                }
              }}
              className="group bg-white border-b border-gray-100 hover:bg-[#F5F5F7] cursor-pointer transition-all duration-200"
            >
              <div className="px-6 py-4 flex items-center space-x-4">
                {/* 文件图标 */}
                <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-sm group-hover:shadow-md transition-all duration-200">
                  <span className="text-2xl">{getFileIcon(file.name, file.type)}</span>
                </div>

                {/* 文件信息 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3 mb-1">
                    <p className="text-[15px] font-semibold text-[#1D1D1F] tracking-tight truncate" title={file.name}>
                      {file.name}
                    </p>
                    {file.url && (
                      <span className="flex-shrink-0 px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-[11px] font-medium tracking-tight">
                        已上传
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-4 text-[12px] text-[#86868B]">
                    <span>{formatFileSize(file.size)}</span>
                    <span>•</span>
                    <span>{formatDate(file.created_at)}</span>
                    {file.type && (
                      <>
                        <span>•</span>
                        <span className="capitalize">{file.type}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
