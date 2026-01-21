import React from 'react';
import { Sparkles as SparklesIcon } from 'lucide-react';
import { Message, Sender } from '../../../types';
import { FormattedResponse } from '../../markdown/MarkdownComponents';

interface RealtimeTabProps {
  messages: Message[];
  isLoading: boolean;
  currentResponse: string;
  selectedTurnId: string | null;
  workspaceMessageId: string | null;
  getMessageDisplay: (text: string) => { fullContent: string };
  wsEnd?: React.RefObject<HTMLDivElement>;
}

/**
 * 实时标签页组件
 * 显示实时分析流和响应内容
 */
export const RealtimeTab: React.FC<RealtimeTabProps> = ({
  messages,
  isLoading,
  currentResponse,
  selectedTurnId,
  workspaceMessageId,
  getMessageDisplay,
  wsEnd,
}) => {
  return (
    <div className="w-full max-w-[1800px] mx-auto space-y-8 animate-apple-fade">
      <div className="flex items-center justify-between border-b border-black/[0.05] pb-6">
        <div className="flex flex-col">
          <div className="flex items-center space-x-3">
            <SparklesIcon size={20} className="text-blue-600 animate-pulse" />
            <h2 className="text-[20px] font-black tracking-tight text-apple-gray uppercase">Analysis Stream</h2>
          </div>
          <span className="text-[11px] text-apple-secondary font-black uppercase tracking-[0.35em] mt-3">
            {isLoading ? 'Real-time Processing' : 'System Operational'}
          </span>
        </div>
        <div className={`w-3.5 h-3.5 rounded-full ${isLoading ? 'bg-blue-500 shadow-[0_0_20px_rgba(37,99,235,0.5)] animate-pulse' : 'bg-green-500'}`} />
      </div>

      {/* 格式化响应组件 - 显示完整内容 */}
      <FormattedResponse
        text={
          isLoading
            ? currentResponse || '处理中...'
            : (() => {
                // ⚠️ 重要：根据 selectedTurnId (conversation_turn_id) 显示对应轮次的内容
                // 确保左侧和右侧工作区统一显示同一个 conversation_turn_id 的内容
                const effectiveTurnId = selectedTurnId || (typeof window !== 'undefined' ? localStorage.getItem('selected_conversation_turn_id') : null);
                
                if (effectiveTurnId) {
                  // 找到该 conversation_turn_id 对应的 AI 消息
                  const turnAIMessage = messages
                    .filter(m => m.sender === Sender.AI && m.conversation_turn_id === effectiveTurnId)
                    .sort((a, b) => {
                      const timeA = a.timestamp instanceof Date ? a.timestamp.getTime() : new Date(a.timestamp).getTime();
                      const timeB = b.timestamp instanceof Date ? b.timestamp.getTime() : new Date(b.timestamp).getTime();
                      return timeB - timeA; // 最新的在前
                    })[0];
                  
                  if (turnAIMessage) {
                    console.log('%c📋 [realtime] 显示 conversation_turn_id 对应的消息:', 'color: #007AFF', {
                      conversation_turn_id: effectiveTurnId,
                      message_id: turnAIMessage.id,
                      message_text_length: turnAIMessage.text?.length || 0
                    });
                    return getMessageDisplay(turnAIMessage.text).fullContent;
                  }
                }
                
                // 如果指定了 workspaceMessageId，显示该消息的完整内容（向后兼容）
                if (workspaceMessageId) {
                  const targetMessage = messages.find(m => m.id === workspaceMessageId);
                  if (targetMessage && targetMessage.sender === Sender.AI) {
                    return getMessageDisplay(targetMessage.text).fullContent;
                  }
                }
                
                // 否则显示最后一个 AI 消息的完整内容
                const lastAIMessage = [...messages].reverse().find(m => m.sender === Sender.AI);
                return lastAIMessage ? getMessageDisplay(lastAIMessage.text).fullContent : 'X 核心就绪，等待数据输入解析。';
              })()
        }
        isStreaming={isLoading}
      />

      {wsEnd && <div ref={wsEnd} />}
    </div>
  );
};
