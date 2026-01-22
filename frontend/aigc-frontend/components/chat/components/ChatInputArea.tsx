import React, { useRef } from 'react';
import { Send, Paperclip, FileIcon, X, Mic, Video, Loader2, FileText } from 'lucide-react';
import { SessionFile } from '../../../services/agentService';

interface ChatInputAreaProps {
  input: string;
  setInput: (value: string) => void;
  onSend: () => void;
  isLoading: boolean;
  
  // 文件相关
  pendingFiles: Array<{ name: string; type: string; data: string }>;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRemovePendingFile: (index: number) => void;
  fileInputRef: React.RefObject<HTMLInputElement>;
  
  // 摄像头相关
  isCameraActive: boolean;
  onToggleCamera: () => void;
  
  // 录音相关
  isRecording: boolean;
  recordingTime: number;
  onToggleRecording: () => void;
  
  // @ 提及相关
  mentionFiles: SessionFile[];
  showMentionDropdown: boolean;
  mentionQuery: string;
  mentionPosition: { top: number; left: number };
  selectedMentionIndex: number;
  inputRef: React.RefObject<HTMLInputElement>;
  mentionDropdownRef: React.RefObject<HTMLDivElement>;
  onMentionInputChange: (value: string, cursorPos: number, inputElement: HTMLInputElement | null) => void;
  onMentionKeyDown: (
    e: React.KeyboardEvent<HTMLInputElement>,
    input: string,
    setInput: (value: string) => void,
    onEnter?: () => void
  ) => boolean;
  onSelectMentionFile: (file: SessionFile, input: string, setInput: (value: string) => void) => void;
}

/**
 * 聊天输入区域组件
 * 包含输入框、文件上传、摄像头、录音等功能
 */
export const ChatInputArea: React.FC<ChatInputAreaProps> = ({
  input,
  setInput,
  onSend,
  isLoading,
  pendingFiles,
  onFileChange,
  onRemovePendingFile,
  fileInputRef,
  isCameraActive,
  onToggleCamera,
  isRecording,
  recordingTime,
  onToggleRecording,
  mentionFiles,
  showMentionDropdown,
  mentionQuery,
  mentionPosition,
  selectedMentionIndex,
  inputRef,
  mentionDropdownRef,
  onMentionInputChange,
  onMentionKeyDown,
  onSelectMentionFile,
}) => {
  return (
    <div className="border-t border-black/[0.04] bg-white relative p-5">
      {/* 待发送文件列表 */}
      {pendingFiles.length > 0 && (
        <div className="absolute bottom-full left-5 right-5 mb-4 flex flex-wrap gap-2 animate-apple-slide z-50">
          {pendingFiles.map((file, idx) => (
            <div key={idx} className="flex items-center space-x-2 px-3 py-1.5 bg-white/95 backdrop-blur-md border border-black/5 rounded-xl shadow-lg ring-1 ring-black/5">
              <FileIcon size={12} className="text-blue-600" />
              <span className="text-[10px] font-black text-apple-gray truncate max-w-[100px]">{file.name}</span>
              <button onClick={() => onRemovePendingFile(idx)} className="text-gray-300 hover:text-red-500"><X size={12}/></button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 bg-[#F2F2F7] rounded-[24px] px-3 py-2.5 border border-black/[0.02] shadow-inner">
        <input type="file" ref={fileInputRef} onChange={onFileChange} className="hidden" multiple />
        <button onClick={() => fileInputRef.current?.click()} className="p-2 text-gray-400 hover:text-blue-600 hover:bg-white rounded-xl transition-all">
          <Paperclip size={18}/>
        </button>
        <button onClick={onToggleCamera} className={`p-2 rounded-xl transition-all ${isCameraActive ? 'text-blue-600 bg-white shadow-sm' : 'text-gray-400 hover:text-blue-600 hover:bg-white'}`}>
          <Video size={18}/>
        </button>
        <button 
          onClick={onToggleRecording} 
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
              const cursorPos = e.target.selectionStart || 0;
              onMentionInputChange(value, cursorPos, e.target);
            }}
            onKeyDown={e => {
              const handled = onMentionKeyDown(e, input, setInput, onSend);
              if (!handled && e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onSend();
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
                    onClick={() => onSelectMentionFile(file, input, setInput)}
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
          onClick={onSend} 
          disabled={(!input.trim() && !isCameraActive && pendingFiles.length === 0 && !isRecording) || isLoading} 
          className="w-9 h-9 bg-apple-gray text-white rounded-xl flex items-center justify-center disabled:opacity-30 hover:bg-black transition-all shadow-lg hover:shadow-xl active:scale-95"
        >
          {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </div>
    </div>
  );
};
