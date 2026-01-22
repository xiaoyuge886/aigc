import React, { useRef } from 'react';
import {
  Activity, Globe, FileIcon, Wrench, GitGraph, X, ArrowLeft,
  Sparkles as SparklesIcon, FileText, ChevronRight, Loader2
} from 'lucide-react';
import { Message, Sender } from '../../types';
import { FormattedResponse } from '../markdown/MarkdownComponents';
import { MarkdownRendererWithCharts } from '../markdown/MarkdownComponents';
import { FilePreview } from '../FilePreview';
import { CodeViewer } from '../CodeViewer';
import { DataFlowTimeline } from '../DataFlowTimeline';
import { getFileContent } from '../../services/agentService';
import { FilesTab } from '../chat/tabs/FilesTab';
import { ToolsTab } from '../chat/tabs/ToolsTab';
import { DataFlowTab } from '../chat/tabs/DataFlowTab';
import { RealtimeTab } from '../chat/tabs/RealtimeTab';

// 工具调用类型
interface ToolCall {
  tool_use_id: string;
  tool_name: string;
  input: any;
  output: any;
  timestamp: string;
  duration?: number;
  status: 'success' | 'error' | 'running';
  conversation_turn_id?: string | null;
  message_id?: string;
}

// 文件信息类型
interface FileInfo {
  id: string;
  name: string;
  path?: string;
  url?: string;
  type?: string;
  size?: number;
  created_at?: Date;
  conversation_turn_id?: string;
}

// 预览文件类型
interface PreviewFile {
  id: string;
  name: string;
  type: 'code' | 'document';
  content: string;
  lang: string;
}

// 工作区组件 Props
export interface WorkspacePanelProps {
  activeTab: 'realtime' | 'browser' | 'files' | 'tools' | 'dataflow';
  setActiveTab: (tab: 'realtime' | 'browser' | 'files' | 'tools' | 'dataflow') => void;
  setIsWorkspaceOpen: (open: boolean) => void;
  messages: Message[];
  files: FileInfo[];
  toolCalls: ToolCall[];
  selectedTurnId: string | null;
  selectedToolCall: string | null;
  setSelectedToolCall: (id: string | null) => void;
  previewFile: PreviewFile | null;
  setPreviewFile: (file: PreviewFile | null) => void;
  isLoading: boolean;
  currentResponse: string;
  workspaceMessageId: string | null;
  getMessageDisplay: (text: string) => { fullContent: string };
  wsEnd?: React.RefObject<HTMLDivElement>;
  sessionId?: string | null;
}

export const WorkspacePanel: React.FC<WorkspacePanelProps> = ({
  activeTab,
  setActiveTab,
  setIsWorkspaceOpen,
  messages,
  files,
  toolCalls,
  selectedTurnId,
  selectedToolCall,
  setSelectedToolCall,
  previewFile,
  setPreviewFile,
  isLoading,
  currentResponse,
  workspaceMessageId,
  getMessageDisplay,
  wsEnd,
  sessionId
}) => {
  return (
    <div className="flex-1 flex flex-col bg-white animate-apple-fade border-l border-black/[0.05]">
          <header className="h-16 px-6 md:px-10 border-b border-black/[0.04] flex items-center justify-between bg-white/95 backdrop-blur-3xl z-40 shadow-sm sticky top-0">
            <div className="flex bg-[#F2F2F7] p-1 rounded-2xl border border-black/[0.01]">
              {[
                {id: 'realtime', icon: <Activity size={12}/>, label: '追踪'},
                {id: 'browser', icon: <Globe size={12}/>, label: '浏览器'},
                {id: 'files', icon: <FileIcon size={12}/>, label: '资源'},
                {id: 'tools', icon: <Wrench size={12}/>, label: '工具'},
                {id: 'dataflow', icon: <GitGraph size={12}/>, label: '链路'}
              ].map(t => (
                <button key={t.id} onClick={() => {setActiveTab(t.id as any); setPreviewFile(null); setSelectedToolCall(null); /* ⚠️ 不删除 selectedTurnId，保持 conversation_turn_id */}} className={`flex items-center space-x-2 px-6 py-2 text-[10px] font-black rounded-xl transition-all ${activeTab === t.id ? 'bg-white shadow-xl text-blue-600' : 'text-gray-400 hover:text-gray-600'}`}>
                  {t.icon} <span className="uppercase tracking-widest">{t.label}</span>
                </button>
              ))}
            </div>
            <button onClick={() => setIsWorkspaceOpen(false)} className="p-2.5 text-gray-300 hover:text-black hover:bg-gray-50 rounded-full transition-all"><X size={20}/></button>
          </header>

          <div className="flex-1 overflow-y-auto bg-white custom-scrollbar p-6 md:p-10 lg:p-14">
            {activeTab === 'realtime' && (
              <RealtimeTab
                messages={messages}
                isLoading={isLoading}
                currentResponse={currentResponse}
                selectedTurnId={selectedTurnId}
                workspaceMessageId={workspaceMessageId}
                getMessageDisplay={getMessageDisplay}
                wsEnd={wsEnd}
              />
            )}

            {activeTab === 'browser' && (
              <div className="max-w-2xl mx-auto h-full flex flex-col items-center justify-center space-y-10 py-32 text-center animate-apple-fade">
                <div className="w-28 h-28 bg-blue-50 text-blue-500 rounded-[48px] flex items-center justify-center shadow-inner ring-1 ring-blue-100">
                  <Globe size={48} strokeWidth={1.5} />
                </div>
                <div className="space-y-3">
                  <h3 className="text-3xl font-black text-apple-gray">全域解析引擎</h3>
                  <p className="text-gray-400 font-medium max-w-sm leading-relaxed text-[15px]">预览模块已就绪。正在同步全球实时信息链。结果将通过 X 核心进行多维验证。</p>
                </div>
              </div>
            )}

            {activeTab === 'files' && (
              <FilesTab
                files={files}
                selectedTurnId={selectedTurnId}
                previewFile={previewFile}
                onSetPreviewFile={setPreviewFile}
                onGetFileContent={getFileContent}
              />
            )}

            {/* 工具调用历史 */}
            {activeTab === 'tools' && (
              <ToolsTab
                toolCalls={toolCalls}
                selectedToolCall={selectedToolCall}
                setSelectedToolCall={setSelectedToolCall}
                selectedTurnId={selectedTurnId}
                sessionId={sessionId}
              />
            )}

            {activeTab === 'dataflow' && (
              <DataFlowTab
                selectedTurnId={selectedTurnId}
              />
            )}
          </div>
        </div>
  );
};
