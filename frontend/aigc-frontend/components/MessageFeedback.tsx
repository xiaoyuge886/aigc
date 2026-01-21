/**
 * 消息反馈组件
 * 
 * 功能：
 * 1. 点赞/点踩/纠正/重新生成按钮
 * 2. 简单的反馈原因选择（不要求自由输入）
 */
import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Edit, RefreshCw, X } from 'lucide-react';
import { submitFeedback, submitImplicitFeedback } from '../services/api';

export interface MessageFeedbackProps {
  messageId: string;
  sessionId?: string;
  conversationTurnId?: string;
  userPrompt?: string;
  assistantResponse?: string;
  scenarioIds?: number[];  // 改为整数ID数组
  onFeedbackSubmitted?: (type: string) => void;
  onCorrectClick?: () => void;  // 交给父组件弹出全局纠正弹框
}

const DISLIKE_REASONS = [
  '回答不准确',
  '回答不完整',
  '回答太详细',
  '回答太简洁',
  '回答不相关',
  '其他'
];

export const MessageFeedback: React.FC<MessageFeedbackProps> = ({
  messageId,
  sessionId,
  conversationTurnId,
  userPrompt,
  assistantResponse,
  scenarioIds,
  onFeedbackSubmitted,
  onCorrectClick
}) => {
  const [feedbackType, setFeedbackType] = useState<string | null>(null);
  const [showDislikeReasons, setShowDislikeReasons] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLike = async () => {
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      await submitFeedback({
        message_id: parseInt(messageId),
        session_id: sessionId,
        conversation_turn_id: conversationTurnId,
        feedback_type: 'like',
        user_prompt: userPrompt,
        assistant_response: assistantResponse,
        scenario_ids: scenarioIds
      });
      
      setFeedbackType('like');
      onFeedbackSubmitted?.('like');
    } catch (error) {
      console.error('提交点赞反馈失败:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDislike = () => {
    setShowDislikeReasons(true);
  };

  const handleDislikeReason = async (reason: string) => {
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      await submitFeedback({
        message_id: parseInt(messageId),
        session_id: sessionId,
        conversation_turn_id: conversationTurnId,
        feedback_type: 'dislike',
        feedback_data: { reason },
        user_prompt: userPrompt,
        assistant_response: assistantResponse,
        scenario_ids: scenarioIds
      });
      
      setFeedbackType('dislike');
      setShowDislikeReasons(false);
      onFeedbackSubmitted?.('dislike');
    } catch (error) {
      console.error('提交点踩反馈失败:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCorrect = () => {
    // 交给父组件统一弹出纠正弹框，避免在消息列表内部嵌套复杂蒙层导致抖动
    onCorrectClick?.();
  };

  const handleRegenerate = async () => {
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      await submitFeedback({
        message_id: parseInt(messageId),
        session_id: sessionId,
        conversation_turn_id: conversationTurnId,
        feedback_type: 'regenerate',
        user_prompt: userPrompt,
        assistant_response: assistantResponse,
        scenario_ids: scenarioIds
      });
      
      setFeedbackType('regenerate');
      onFeedbackSubmitted?.('regenerate');
    } catch (error) {
      console.error('提交重新生成反馈失败:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative">
      <div className="flex items-center space-x-2">
        <button
          onClick={handleLike}
          disabled={isSubmitting}
          className={`p-1.5 rounded transition-colors ${
            feedbackType === 'like'
              ? 'text-green-600 bg-green-50'
              : 'text-gray-300 hover:text-green-600 hover:bg-green-50'
          } ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}`}
          title="有帮助"
        >
          <ThumbsUp size={14} />
        </button>
        
        <button
          onClick={handleDislike}
          disabled={isSubmitting}
          className={`p-1.5 rounded transition-colors ${
            feedbackType === 'dislike'
              ? 'text-red-500 bg-red-50'
              : 'text-gray-300 hover:text-red-500 hover:bg-red-50'
          } ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}`}
          title="无帮助"
        >
          <ThumbsDown size={14} />
        </button>
        
        <button
          onClick={handleCorrect}
          disabled={isSubmitting}
          className={`p-1.5 rounded transition-colors ${
            feedbackType === 'correct'
              ? 'text-blue-600 bg-blue-50'
              : 'text-gray-300 hover:text-blue-600 hover:bg-blue-50'
          } ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}`}
          title="纠正"
        >
          <Edit size={14} />
        </button>
        
        <button
          onClick={handleRegenerate}
          disabled={isSubmitting}
          className={`p-1.5 rounded transition-colors ${
            feedbackType === 'regenerate'
              ? 'text-purple-600 bg-purple-50'
              : 'text-gray-300 hover:text-purple-600 hover:bg-purple-50'
          } ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}`}
          title="重新生成"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {/* 点踩原因选择 */}
      {showDislikeReasons && (
        <div className="absolute top-full left-0 mt-2 bg-white rounded-lg shadow-lg border border-gray-200 p-3 z-50 min-w-[200px]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">选择原因</span>
            <button
              onClick={() => setShowDislikeReasons(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X size={16} />
            </button>
          </div>
          <div className="space-y-1">
            {DISLIKE_REASONS.map((reason) => (
              <button
                key={reason}
                onClick={() => handleDislikeReason(reason)}
                disabled={isSubmitting}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
              >
                {reason}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
