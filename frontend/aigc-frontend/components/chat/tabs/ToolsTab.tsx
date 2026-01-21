import React from 'react';
import { Wrench, ArrowLeft, ChevronRight, Loader2 } from 'lucide-react';
import { MarkdownRendererWithCharts } from '../../markdown/MarkdownComponents';

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

interface ToolsTabProps {
  toolCalls: ToolCall[];
  selectedToolCall: string | null;
  setSelectedToolCall: (id: string | null) => void;
  selectedTurnId: string | null;
  sessionId?: string | null;
}

/**
 * 工具标签页组件
 * 显示工具调用列表和详情
 */
export const ToolsTab: React.FC<ToolsTabProps> = ({
  toolCalls,
  selectedToolCall,
  setSelectedToolCall,
  selectedTurnId,
  sessionId,
}) => {
  // 调试日志
  React.useEffect(() => {
    console.log('🔧 工具标签页已激活', {
      session_id: sessionId,
      totalCalls: toolCalls.length,
      selectedCall: selectedToolCall,
      turns: [...new Set(toolCalls.map(t => t.conversation_turn_id))].length,
      calls: toolCalls.map(t => ({
        id: t.tool_use_id,
        name: t.tool_name,
        status: t.status,
        turn_id: t.conversation_turn_id
      }))
    });
  }, [toolCalls, selectedToolCall, sessionId]);

  return (
    <div className="w-full max-w-[1800px] mx-auto animate-apple-fade">
      <div className="flex items-center justify-between border-b border-black/[0.05] pb-6">
        <div className="flex flex-col">
          <div className="flex items-center space-x-3">
            <Wrench size={20} className="text-blue-600" />
            <h2 className="text-[20px] font-black tracking-tight text-apple-gray uppercase">Tool Calls</h2>
          </div>
          <span className="text-[11px] text-apple-secondary font-black uppercase tracking-[0.35em] mt-3">
            {toolCalls.length} 个工具调用 · {selectedTurnId ? '已选轮次' : '当前轮次'}
          </span>
        </div>
      </div>

      {selectedToolCall ? (
        // 工具调用详情
        <div className="space-y-6 animate-apple-slide">
          <button
            onClick={() => {
              setSelectedToolCall(null);
              // ⚠️ 不删除 selectedTurnId，保持 conversation_turn_id（只有点击"数据已经同步到工作区"按钮才能更新）
            }}
            className="flex items-center space-x-2 text-[11px] font-black uppercase tracking-widest text-blue-600 hover:translate-x-[-4px] transition-transform"
          >
            <ArrowLeft size={16} /> <span>返回列表</span>
          </button>

          {(() => {
            const tool = toolCalls.find(t => t.tool_use_id === selectedToolCall);
            if (!tool) return null;

            return (
              <div className="space-y-6">
                {/* 工具名称和状态 */}
                <div className="bg-white rounded-2xl border border-black/[0.04] p-6 shadow-sm">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-3">
                        <Wrench size={18} className="text-blue-600" />
                        <h3 className="text-[16px] font-black text-apple-gray">{tool.tool_name}</h3>
                        <span className={`px-2 py-1 rounded-full text-[10px] font-black uppercase ${
                          tool.status === 'success' ? 'bg-green-100 text-green-700' :
                          tool.status === 'error' ? 'bg-red-100 text-red-700' :
                          'bg-blue-100 text-blue-700'
                        }`}>
                          {tool.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-gray-400 font-mono">{tool.tool_use_id}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[12px] text-gray-400">{tool.timestamp}</p>
                      {tool.duration && (
                        <p className="text-[11px] text-gray-500 mt-1">{tool.duration}ms</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* 输入 */}
                <div className="bg-white rounded-2xl border border-black/[0.04] overflow-hidden shadow-sm">
                  <div className="px-6 py-3 bg-gray-50 border-b border-gray-100">
                    <p className="text-[11px] font-black uppercase tracking-widest text-gray-500">Input</p>
                  </div>
                  <div className="p-6">
                    <pre className="text-[13px] font-mono text-gray-700 whitespace-pre-wrap overflow-x-auto bg-[#F5F5F7] rounded-xl p-4">
                      {typeof tool.input === 'string' ? tool.input : JSON.stringify(tool.input, null, 2)}
                    </pre>
                  </div>
                </div>

                {/* 输出 */}
                <div className="bg-white rounded-2xl border border-black/[0.04] overflow-hidden shadow-sm">
                  <div className="px-6 py-3 bg-gray-50 border-b border-gray-100">
                    <p className="text-[11px] font-black uppercase tracking-widest text-gray-500">Output</p>
                  </div>
                  <div className="p-6 max-h-[400px] overflow-y-auto">
                    {tool.status === 'running' ? (
                      <div className="flex items-center space-x-3 text-gray-400">
                        <Loader2 size={16} className="animate-spin" />
                        <span className="text-[13px]">Running...</span>
                      </div>
                    ) : (
                      <div className="text-[13px]">
                        {typeof tool.output === 'string' && tool.output.includes('```') ? (
                          <MarkdownRendererWithCharts content={tool.output} isStreaming={false} />
                        ) : (
                          <pre className="font-mono text-gray-700 whitespace-pre-wrap overflow-x-auto bg-[#F5F5F7] rounded-xl p-4">
                            {typeof tool.output === 'string' ? tool.output : JSON.stringify(tool.output, null, 2)}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      ) : (
        // 工具调用列表 - 只显示当前轮次的工具（不再显示轮次列表）
        <div className="space-y-3">
          {toolCalls.length === 0 ? (
            <div className="text-center py-20">
              <Wrench size={48} className="text-gray-300 mx-auto mb-4" />
              <p className="text-[14px] text-gray-400">当前轮次暂无工具调用</p>
              <p className="text-[11px] text-gray-300 mt-2">发送消息后，工具调用将显示在这里</p>
            </div>
          ) : (
            <div className="space-y-3">
              {toolCalls.map((tool) => (
                <div
                  key={tool.tool_use_id}
                  onClick={() => setSelectedToolCall(tool.tool_use_id)}
                  className="bg-white rounded-xl border border-black/[0.04] p-5 hover:border-blue-200 hover:shadow-lg cursor-pointer transition-all duration-300 group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className={`p-2.5 rounded-xl ${
                        tool.status === 'success' ? 'bg-green-50 text-green-600' :
                        tool.status === 'error' ? 'bg-red-50 text-red-600' :
                        'bg-blue-50 text-blue-600'
                      }`}>
                        <Wrench size={16} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h4 className="text-[14px] font-bold text-apple-gray truncate">{tool.tool_name}</h4>
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase ${
                            tool.status === 'success' ? 'bg-green-100 text-green-600' :
                            tool.status === 'error' ? 'bg-red-100 text-red-600' :
                            'bg-blue-100 text-blue-600'
                          }`}>
                            {tool.status}
                          </span>
                        </div>
                        <p className="text-[11px] text-gray-400 font-mono truncate">{tool.tool_use_id}</p>
                        <div className="flex items-center space-x-3 mt-2">
                          <span className="text-[11px] text-gray-400">{tool.timestamp}</span>
                          {tool.duration && (
                            <span className="text-[11px] text-gray-400">{tool.duration}ms</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <ChevronRight size={16} className="text-gray-300 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
