import React, { useRef } from 'react';
import { Send, Paperclip, FileIcon, X, Loader2, Mic, Video, FileText } from 'lucide-react';
import { SessionFile } from '../../services/agentService';

export interface ChatInputProps {
  input: string;
  setInput: (value: string) => void;
  pendingFiles: { name: string; type: string; data: string }[];
  isCameraActive: boolean;
  isRecording: boolean;
  recordingTime: number;
  isLoading: boolean;
  mentionFiles: SessionFile[];
  showMentionDropdown: boolean;
  mentionQuery: string;
  mentionPosition: { top: number; left: number };
  selectedMentionIndex: number;
  fileInputRef: React.RefObject<HTMLInputElement>;
  mentionDropdownRef: React.RefObject<HTMLDivElement>;
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  removePendingFile: (index: number) => void;
  toggleCamera: () => void;
  toggleRecording: () => void;
  handleSend: () => void;
  setShowMentionDropdown: (show: boolean) => void;
  setMentionQuery: (query: string) => void;
  setSelectedMentionIndex: (index: number) => void;
  setMentionPosition: (position: { top: number; left: number }) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  input,
  setInput,
  pendingFiles,
  isCameraActive,
  isRecording,
  recordingTime,
  isLoading,
  mentionFiles,
  showMentionDropdown,
  mentionQuery,
  mentionPosition,
  selectedMentionIndex,
  fileInputRef,
  mentionDropdownRef,
  handleFileChange,
  removePendingFile,
  toggleCamera,
  toggleRecording,
  handleSend,
  setShowMentionDropdown,
  setMentionQuery,
  setSelectedMentionIndex,
  setMentionPosition,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="border-t border-black/[0.04] bg-white relative p-5">
      {pendingFiles.length > 0 && (
        <div className="absolute bottom-full left-5 right-5 mb-4 flex flex-wrap gap-2 animate-apple-slide z-50">
          {pendingFiles.map((file, idx) => (
            <div key={idx} className="flex items-center space-x-2 px-3 py-1.5 bg-white/95 backdrop-blur-md border border-black/5 rounded-xl shadow-lg ring-1 ring-black/5">
              <FileIcon size={12} className="text-blue-600" />
              <span className="text-[10px] font-black text-apple-gray truncate max-w-[100px]">{file.name}</span>
              <button onClick={() => removePendingFile(idx)} className="text-gray-300 hover:text-red-500"><X size={12}/></button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 bg-[#F2F2F7] rounded-[24px] px-3 py-2.5 border border-black/[0.02] shadow-inner">
        <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" multiple />
        <button onClick={() => fileInputRef.current?.click()} className="p-2 text-gray-400 hover:text-blue-600 hover:bg-white rounded-xl transition-all">
          <Paperclip size={18}/>
        </button>
        <button onClick={toggleCamera} className={`p-2 rounded-xl transition-all ${isCameraActive ? 'text-blue-600 bg-white shadow-sm' : 'text-gray-400 hover:text-blue-600 hover:bg-white'}`}>
          <Video size={18}/>
        </button>
        <button 
          onClick={toggleRecording} 
          className={`p-2 rounded-xl transition-all relative ${isRecording ? 'text-red-600 bg-red-50 shadow-sm animate-pulse' : 'text-gray-400 hover:text-blue-600 hover:bg-white'}`}
          title={isRecording ? '点击停止录制' : '点击开始录制'}
        >
          <Mic size={18}/>
          {isRecording && (
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-ping" />
          )}
        </button>
        {isRecording && (
          <div className="flex items-center space-x-2 px-3 py-1 bg-red-50 rounded-xl border border-red-200">
            <div className="flex space-x-1">
              <div className="w-1 h-4 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
              <div className="w-1 h-6 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
              <div className="w-1 h-5 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
              <div className="w-1 h-4 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '450ms' }} />
            </div>
            <span className="text-[12px] font-bold text-red-600 min-w-[45px] tabular-nums" title={`录制时长: ${recordingTime} 秒`}>
              {Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}
            </span>
          </div>
        )}
        <div className="flex-1 relative">
          <input
            ref={inputRef}
            value={input} 
            onChange={e => {
              const value = e.target.value;
              setInput(value);
              
              // 检测 @ 符号
              const cursorPos = e.target.selectionStart || 0;
              const textBeforeCursor = value.substring(0, cursorPos);
              const lastAtIndex = textBeforeCursor.lastIndexOf('@');
              
              if (lastAtIndex !== -1) {
                // 检查 @ 后是否有空格或换行（如果有，说明不是提及）
                const afterAt = textBeforeCursor.substring(lastAtIndex + 1);
                if (!afterAt.includes(' ') && !afterAt.includes('\n')) {
                  const query = afterAt.toLowerCase();
                  setMentionQuery(query);
                  
                  // 检查是否有可提及的文件
                  if (mentionFiles.length > 0) {
                    setShowMentionDropdown(true);
                    setSelectedMentionIndex(0);
                    
                    // 计算下拉菜单位置
                    if (inputRef.current) {
                      const rect = inputRef.current.getBoundingClientRect();
                      setMentionPosition({
                        top: rect.bottom + 4,
                        left: rect.left
                      });
                    }
                  } else {
                    // 没有可提及的文件，隐藏下拉菜单
                    setShowMentionDropdown(false);
                  }
                  
                  return;
                }
              }
              
              // 如果没有 @ 或 @ 后有空格，隐藏下拉菜单
              setShowMentionDropdown(false);
            }}
            onKeyDown={e => {
              if (showMentionDropdown && mentionFiles.length > 0) {
                if (e.key === 'ArrowDown') {
                  e.preventDefault();
                  setSelectedMentionIndex(prev => 
                    prev < mentionFiles.length - 1 ? prev + 1 : prev
                  );
                } else if (e.key === 'ArrowUp') {
                  e.preventDefault();
                  setSelectedMentionIndex(prev => prev > 0 ? prev - 1 : 0);
                } else if (e.key === 'Enter' || e.key === 'Tab') {
                  e.preventDefault();
                  const selectedFile = mentionFiles[selectedMentionIndex];
                  if (selectedFile) {
                    // 替换 @ 后的文本为文件引用
                    const cursorPos = inputRef.current?.selectionStart || 0;
                    const textBeforeCursor = input.substring(0, cursorPos);
                    const lastAtIndex = textBeforeCursor.lastIndexOf('@');
                    const textAfterCursor = input.substring(cursorPos);
                    
                    const newText = 
                      input.substring(0, lastAtIndex) + 
                      `@${selectedFile.file_name}` + 
                      textAfterCursor;
                    
                    setInput(newText);
                    setShowMentionDropdown(false);
                    
                    // 设置光标位置
                    setTimeout(() => {
                      if (inputRef.current) {
                        const newPos = lastAtIndex + selectedFile.file_name.length + 1;
                        inputRef.current.setSelectionRange(newPos, newPos);
                      }
                    }, 0);
                  }
                } else if (e.key === 'Escape') {
                  e.preventDefault();
                  setShowMentionDropdown(false);
                } else {
                  // 其他按键，继续正常处理
                  if (e.key === 'Enter' && !e.shiftKey) {
                    handleSend();
                  }
                }
              } else {
                // 没有下拉菜单时，正常处理 Enter
                if (e.key === 'Enter' && !e.shiftKey) {
                  handleSend();
                }
              }
            }}
            placeholder="发送指令... (输入 @ 提及文件)" 
            className="w-full bg-transparent border-none text-[14px] px-2 outline-none font-medium text-apple-gray placeholder:text-gray-400"
          />
          
          {/* @ 提及文件下拉菜单 */}
          {showMentionDropdown && mentionFiles.length > 0 && (
            <div
              ref={mentionDropdownRef}
              className="absolute z-50 mt-1 w-64 bg-white rounded-xl shadow-xl border border-gray-200 max-h-60 overflow-y-auto"
              style={{
                top: `${mentionPosition.top}px`,
                left: `${mentionPosition.left}px`
              }}
            >
              {mentionFiles
                .filter(file => 
                  !mentionQuery || 
                  file.file_name.toLowerCase().includes(mentionQuery)
                )
                .map((file, index) => (
                  <div
                    key={file.doc_id}
                    onClick={() => {
                      // 替换 @ 后的文本为文件引用
                      const cursorPos = inputRef.current?.selectionStart || 0;
                      const textBeforeCursor = input.substring(0, cursorPos);
                      const lastAtIndex = textBeforeCursor.lastIndexOf('@');
                      const textAfterCursor = input.substring(cursorPos);
                      
                      const newText = 
                        input.substring(0, lastAtIndex) + 
                        `@${file.file_name}` + 
                        textAfterCursor;
                      
                      setInput(newText);
                      setShowMentionDropdown(false);
                      
                      // 设置光标位置
                      setTimeout(() => {
                        if (inputRef.current) {
                          const newPos = lastAtIndex + file.file_name.length + 1;
                          inputRef.current.setSelectionRange(newPos, newPos);
                          inputRef.current.focus();
                        }
                      }, 0);
                    }}
                    className={`px-4 py-2 cursor-pointer transition-colors ${
                      index === selectedMentionIndex
                        ? 'bg-blue-50 text-blue-600'
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <FileText size={16} className="text-gray-400" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{file.file_name}</p>
                        {file.file_size && (
                          <p className="text-xs text-gray-400">
                            {(file.file_size / 1024).toFixed(1)} KB
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
        <button 
          onClick={() => handleSend()} 
          disabled={(!input.trim() && !isCameraActive && pendingFiles.length === 0 && !isRecording) || isLoading} 
          className="w-9 h-9 bg-apple-gray text-white rounded-xl flex items-center justify-center disabled:opacity-30 hover:bg-black transition-all shadow-lg hover:shadow-xl active:scale-95"
        >
          {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </div>
    </div>
  );
};
