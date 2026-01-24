
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
  Send, Paperclip, FileIcon, X, Search, Loader2,
  Activity, ArrowLeft, Cpu, ChevronRight, Zap,
  Maximize2, FileText, BarChart3, LineChart, PieChart, GitGraph,
  Expand, Shrink, Share2, Globe, Mic, Video, StopCircle, Camera, Trash2,
  Sparkles as SparklesIcon, ThumbsUp, ThumbsDown, RefreshCw, Copy, Check
} from 'lucide-react';
import { Message, Sender, ResultInfo } from '../types';
import { streamGeminiResponse } from '../services/geminiService';
import { streamAgentQuery, deleteSession, getLocalSessionId, getConversationHistory, getFileContent, getSessionFiles, SessionFile } from '../services/agentService';
import { FilePreview } from './FilePreview';
import { CodeViewer } from './CodeViewer';
import { TodoList, TodoItem } from './TodoList';
import { DataFlowTimeline } from './DataFlowTimeline';
import { ChartType, CHART_CONFIGS, AppleECharts, ChartBlock } from './charts/ChartComponents';
import { MarkdownRenderer, MarkdownRendererWithCharts, FormattedResponse } from './markdown/MarkdownComponents';
import { MarkmapContainer } from './mindmap/MarkmapContainer';
import { RecommendationCard, RECOMMENDED_QUESTIONS } from './recommendations/RecommendationCard';
import { getMessageDisplay, extractTodosFromToolCalls } from './chat/utils/messageUtils';
import { parseToolCalls, ToolCall } from './chat/utils/toolCallUtils';
import { ChatInputArea } from './chat/components/ChatInputArea';
import { FilesTab } from './chat/tabs/FilesTab';
import { WorkspacePanel } from './workspace/WorkspacePanel';
import { useMentions } from './chat/hooks/useMentions';
import * as echarts from 'echarts';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Wrench, ChevronDown, ChevronUp } from 'lucide-react';
import { MessageFeedback } from './MessageFeedback';
import { submitFeedback } from '../services/api';

/**
 * 检查工具调用是否是 TodoWrite 或 enhanced_todo_write
 */
const isTodoTool = (toolName: string): boolean => {
  return toolName === 'TodoWrite' || toolName === 'enhanced_todo_write' || toolName === 'mcp__custom_tools__enhanced_todo_write';
};

/**
 * 解析任务层级（从 content 中提取）
 * 返回 { level: string | null, parentLevel: string | null }
 */
const parseTaskLevel = (content: string): { level: string | null; parentLevel: string | null } => {
  if (!content) return { level: null, parentLevel: null };

  const trimmed = content.trim();
  // 匹配 "1", "1.1", "1.2.3" 这样的层级编号
  const match = trimmed.match(/^(\d+(?:\.\d+)*)(?:\.\s|\s)/);

  if (match) {
    const level = match[1];
    const parts = level.split('.');
    const parentLevel = parts.length > 1 ? parts.slice(0, -1).join('.') : null;
    return { level, parentLevel };
  }

  return { level: null, parentLevel: null };
};

/**
 * 解析 todos 数据（可能是数组或 JSON 字符串）
 * 同时为每个 todo 添加 level 和 parentLevel 字段
 */
const parseTodosData = (todos: any): any[] => {
  if (!todos) return [];
  if (Array.isArray(todos)) {
    // 为每个 todo 解析 level
    return todos.map((todo: any) => {
      const content = todo.content || '';
      const level = parseTaskLevel(content);
      return {
        ...todo,
        level: level.level,
        parentLevel: level.parentLevel
      };
    });
  }
  if (typeof todos === 'string') {
    try {
      const parsed = JSON.parse(todos);
      if (Array.isArray(parsed)) {
        return parsed.map((todo: any) => {
          const content = todo.content || '';
          const level = parseTaskLevel(content);
          return {
            ...todo,
            level: level.level,
            parentLevel: level.parentLevel
          };
        });
      }
      return parsed;
    } catch (e) {
      console.warn('Failed to parse todos JSON string:', e);
      return [];
    }
  }
  return [];
};

interface ChatInterfaceProps {
  isWorkspaceOpen: boolean;
  setIsWorkspaceOpen: (open: boolean) => void;
  backendProvider?: 'gemini' | 'claude';
  onSessionChange?: (sessionId: string | null) => void;
}


/**
 * Mock 历史记录数据（模拟后端返回的格式）
 * 
 * 评估说明：
 * 1. ✅ 前端已支持渲染 Message[] 格式的历史记录
 * 2. ✅ 前端已支持 resultInfo 字段（subtype, duration_ms, num_turns, total_cost_usd, usage 等）
 * 3. ✅ 前端已支持长消息（>100字符）显示"数据已经同步到工作区"
 * 4. ✅ 前端已支持 markdown 渲染（表格、代码块、图表等）
 * 
 * 后端接口建议返回格式：
 * {
 *   "session_id": "657009a6-f757-4614-b21f-25044b9d688f",
 *   "messages": [
 *     {
 *       "id": "user-1",
 *       "text": "用户消息内容",
 *       "sender": "user",
 *       "timestamp": "2024-01-01T12:00:00Z"
 *     },
 *     {
 *       "id": "ai-1",
 *       "text": "AI 响应内容",
 *       "sender": "ai",
 *       "timestamp": "2024-01-01T12:00:01Z",
 *       "resultInfo": {
 *         "subtype": "success",
 *         "duration_ms": 6356,
 *         "duration_api_ms": 10071,
 *         "is_error": false,
 *         "num_turns": 4,
 *         "session_id": "657009a6-f757-4614-b21f-25044b9d688f",
 *         "total_cost_usd": 0.0500592,
 *         "usage": { ... }
 *       }
 *     }
 *   ]
 * }
 */
const MOCK_HISTORY_MESSAGES: Message[] = [
  {
    id: 'user-1',
    text: '用你的技能把问题优化输出完整报告',
    sender: Sender.User,
    timestamp: new Date(Date.now() - 2 * 60 * 1000), // 2分钟前
  },
  {
    id: 'ai-1',
    text: '我已深度研究专家技能来为您分析温榆河。这个技能将基于专业知识库进行智能提示增强和深度研究分析。\n\n请您提供更具体的需求，以便我为您生成更精准的分析报告：\n\n1. **分析维度**：您希望重点分析哪些方面？\n   - 水文特征与水资源状况\n   - 水环境质量与生态状况\n   - 河道治理与工程设施\n   - 流域管理与保护措施\n   - 综合性分析报告\n\n2. **地理范围**：\n   - 全流域分析\n   - 特定河段（如上游、中游、下游）\n   - 特定区域（如北京市域范围内）\n\n3. **报告用途**：\n   - 学术研究\n   - 工程规划\n   - 环境评估\n   - 管理决策\n\n4. **时间范围**：\n   - 现状分析\n   - 历史变化趋势\n   - 未来发展预测\n\n请告诉我您的具体需求，我将为您生成专业的温榆河分析报告。',
    sender: Sender.AI,
    timestamp: new Date(Date.now() - 2 * 60 * 1000 + 1000),
    resultInfo: {
      subtype: 'success',
      duration_ms: 6356,
      duration_api_ms: 10071,
      is_error: false,
      num_turns: 4,
      session_id: '657009a6-f757-4614-b21f-25044b9d688f',
      total_cost_usd: 0.0500592,
      usage: {
        input_tokens: 12067,
        cache_creation_input_tokens: 0,
        cache_read_input_tokens: 12288,
        output_tokens: 267,
        server_tool_use: { web_search_requests: 0 },
        service_tier: 'standard',
        cache_creation: {
          ephemeral_1h_input_tokens: 0,
          ephemeral_5m_input_tokens: 0
        }
      }
    }
  },
  {
    id: 'user-2',
    text: '你好生成不错',
    sender: Sender.User,
    timestamp: new Date(Date.now() - 1 * 60 * 1000), // 1分钟前
  },
  {
    id: 'ai-2',
    text: '谢谢您的肯定! 😊 很高兴这份温榆河综合分析报告符合您的期望。如果您后续还有其他需求,比如: ● 针对某个具体章节进行更深入的分析',
    sender: Sender.AI,
    timestamp: new Date(Date.now() - 1 * 60 * 1000 + 500),
    resultInfo: {
      subtype: 'success',
      duration_ms: 1234,
      duration_api_ms: 2000,
      is_error: false,
      num_turns: 1,
      session_id: '657009a6-f757-4614-b21f-25044b9d688f',
      total_cost_usd: 0.002345,
      usage: {
        input_tokens: 500,
        output_tokens: 150,
        service_tier: 'standard'
      }
    }
  }
];

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  isWorkspaceOpen, 
  setIsWorkspaceOpen, 
  backendProvider = 'claude',
  onSessionChange 
}) => {
  // 初始化消息为空数组，将从后端加载
  const [messages, setMessages] = useState<Message[]>([]);
  
  // 对话历史分页状态
  const [historyTotal, setHistoryTotal] = useState<number | null>(null);
  const [historyHasMore, setHistoryHasMore] = useState(false);
  const [historyOffset, setHistoryOffset] = useState(0);
  const [loadingMoreHistory, setLoadingMoreHistory] = useState(false);
  const MESSAGES_PER_PAGE = 50; // 每页加载的消息数
  
  // 调试：监控 messages 变化
  useEffect(() => {
    console.log('[ChatInterface] Messages state changed:', {
      count: messages.length,
      total: historyTotal,
      has_more: historyHasMore,
      messages: messages.map(m => ({ id: m.id, sender: m.sender, text_length: m.text?.length || 0 }))
    });
  }, [messages, historyTotal, historyHasMore]);

  const [sessionId, setSessionId] = useState<string | null>(null);

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'realtime' | 'browser' | 'files' | 'tools' | 'dataflow'>('realtime');
  const [currentResponse, setCurrentResponse] = useState<string>('');
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  // 全局纠正反馈弹框状态（避免在消息列表内部嵌套蒙层导致抖动）
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);
  const [feedbackCorrectText, setFeedbackCorrectText] = useState('');
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [feedbackTarget, setFeedbackTarget] = useState<{
    messageId: string;
    sessionId?: string;
    conversationTurnId?: string;
    userPrompt?: string;
    assistantResponse?: string;
  } | null>(null);

  const handleSubmitCorrectFeedback = async () => {
    if (!feedbackTarget || !feedbackCorrectText.trim() || isSubmittingFeedback) return;
    setIsSubmittingFeedback(true);
    try {
      await submitFeedback({
        message_id: parseInt(feedbackTarget.messageId),
        session_id: feedbackTarget.sessionId,
        conversation_turn_id: feedbackTarget.conversationTurnId,
        feedback_type: 'correct',
        feedback_data: { correct_text: feedbackCorrectText.trim() },
        user_prompt: feedbackTarget.userPrompt,
        assistant_response: feedbackTarget.assistantResponse,
        scenario_ids: undefined,
      });
      setIsFeedbackModalOpen(false);
      setFeedbackCorrectText('');
      setFeedbackTarget(null);
    } catch (error) {
      console.error('提交纠正反馈失败:', error);
    } finally {
      setIsSubmittingFeedback(false);
    }
  };
  const [selectedToolCall, setSelectedToolCall] = useState<string | null>(null);
  
  // ⚠️ 重要：从 localStorage 初始化 selectedTurnId
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(() => {
    const saved = localStorage.getItem('selected_conversation_turn_id');
    console.log('%c📥 从 localStorage 恢复 selectedTurnId:', 'color: #FF9500; font-weight: bold', {
      saved: saved,
      saved_type: typeof saved
    });
    return saved || null;
  });
  
  const [workspaceMessageId, setWorkspaceMessageId] = useState<string | null>(null); // 当前在工作区显示的消息ID
  
  // 文件列表状态
  interface FileInfo {
    id: string;
    name: string;
    path?: string;
    url?: string;
    size?: number;
    type?: string;
    conversation_turn_id: string;
    created_at: Date;
    file_content?: string; // 🔧 新增：文件内容（如果已在 event 中推送）
  }
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [expandedStats, setExpandedStats] = useState<Set<string>>(new Set()); // 存储已展开统计信息的消息ID
  
  // @ 提及功能状态
  const [mentionFiles, setMentionFiles] = useState<SessionFile[]>([]); // 可提及的文件列表
  const [showMentionDropdown, setShowMentionDropdown] = useState(false); // 是否显示文件下拉菜单
  const [mentionQuery, setMentionQuery] = useState(''); // @ 后的查询文本
  const [mentionPosition, setMentionPosition] = useState({ top: 0, left: 0 }); // 下拉菜单位置
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0); // 选中的文件索引
  const inputRef = useRef<HTMLInputElement>(null); // 输入框引用
  
  /**
   * 从消息中提取 TodoWrite 的待办事项列表
   * 返回最新的待办事项列表（如果有多个 TodoWrite 调用，使用最新的）
   * 
   * 🔧 关键修复：使用 useEffect 替代 useMemo，确保每次 messages 变化时都重新计算
   * 直接从 messages 中提取，不依赖 toolCalls 状态（因为 toolCalls 只在 tools 标签页激活时提取）
   */
  const [todos, setTodos] = useState<TodoItem[]>([]);
  const realtimeTodosRef = useRef<TodoItem[]>([]); // 🔧 跟踪实时更新的 todos
  
  // 🔧 简化方案：实时更新优先使用 tool_input_delta 中的 todos
  // extractTodosFromToolCalls 仅用于历史记录加载（当没有实时更新时）
  useEffect(() => {
    // 如果已经有实时更新的 todos，优先使用实时更新的
    if (realtimeTodosRef.current.length > 0) {
      console.log('%c⏭️ [useEffect] 跳过 extractTodosFromToolCalls，使用实时更新的 todos', 'color: #86868B; font-weight: bold', {
        realtime_todos_count: realtimeTodosRef.current.length,
        note: '实时更新优先'
      });
      return;
    }
    
    // 只在没有实时更新时，从 messages 中提取（用于历史记录加载）
    const extractedTodos = extractTodosFromToolCalls(messages);
    if (extractedTodos.length > 0) {
      console.log('%c🔄 [useEffect] 从历史记录提取 todos', 'color: #007AFF; font-weight: bold', {
        messages_count: messages.length,
        extracted_todos_count: extractedTodos.length,
        extracted_todos_statuses: extractedTodos.map(t => `${t.content?.substring(0, 15)}:${t.status}`),
        note: '历史记录加载时使用'
      });
      setTodos(extractedTodos);
    }
  }, [messages]);

  // 🔍 监听 sessionId 变化，处理文件列表
  useEffect(() => {
    if (sessionId) {
      // sessionId 存在时，文件列表会在加载历史对话时设置
      console.log('%c📁 [sessionId变化] sessionId存在，等待加载历史对话中的文件列表', 'color: #5856D6', sessionId);
    } else {
      // sessionId 为空时，不清空文件列表（新对话时可能正在上传文件）
      // 文件列表会在新对话开始时通过文件事件更新
      console.log('%c📁 [sessionId变化] sessionId为空，保留文件列表（新对话可能正在上传文件）', 'color: #5856D6');
    }
  }, [sessionId]);

  // 🐛 调试：监控 selectedTurnId 变化，并同步到 localStorage
  useEffect(() => {
    console.log('%c🎯 selectedTurnId 状态变化:', 'color: #34C759; font-weight: bold', {
      selectedTurnId: selectedTurnId,
      type: typeof selectedTurnId,
      conversation_turn_id: selectedTurnId
    });
    
    // ⚠️ 重要：同步到 localStorage（只保存，不删除）
    // 只有点击"数据已经同步到工作区"按钮时才能更新 conversation_turn_id
    // 其他地方（如切换标签页、返回列表等）都不应该删除 conversation_turn_id
    if (selectedTurnId) {
      localStorage.setItem('selected_conversation_turn_id', selectedTurnId);
      console.log('%c💾 已保存 selectedTurnId 到 localStorage:', 'color: #34C759; font-weight: bold', {
        conversation_turn_id: selectedTurnId
      });
    }
    // ⚠️ 注意：不删除 localStorage，保持 conversation_turn_id 持久化
  }, [selectedTurnId]);

  // 🐛 调试：监控工具调用状态
  useEffect(() => {
    if (toolCalls.length > 0) {
      console.log('%c🔧 工具调用状态更新:', 'color: #FF9500; font-weight: bold', {
        total: toolCalls.length,
        selectedTurnId: selectedTurnId,
        calls: toolCalls.map(t => ({
          id: t.tool_use_id.substring(0, 20) + '...',
          name: t.tool_name,
          status: t.status,
          turn_id: t.conversation_turn_id,
          timestamp: t.timestamp
        }))
      });
    }
  }, [toolCalls, selectedTurnId]);

  // 📁 加载文件列表（用于 @ 提及功能）
  useEffect(() => {
    const loadFiles = async () => {
      if (sessionId) {
        try {
          console.log('%c📁 [loadFiles] 开始加载文件列表，sessionId:', 'color: #5856D6; font-weight: bold', sessionId);
          const sessionFiles = await getSessionFiles(sessionId);
          console.log('%c📁 [loadFiles] 获取到的文件列表:', 'color: #5856D6; font-weight: bold', {
            count: sessionFiles.length,
            files: sessionFiles.map(f => ({ name: f.file_name, doc_id: f.doc_id }))
          });
          // 合并现有文件和从服务器获取的文件（避免覆盖通过文件事件添加的文件）
          setMentionFiles(prev => {
            const existingDocIds = new Set(prev.map(f => f.doc_id));
            const newFiles = sessionFiles.filter(f => !existingDocIds.has(f.doc_id));
            if (newFiles.length > 0) {
              const merged = [...prev, ...newFiles];
              console.log('%c📁 [loadFiles] ✅ 合并文件列表到 mentionFiles:', 'color: #34C759; font-weight: bold', {
                before_count: prev.length,
                new_files: newFiles.length,
                after_count: merged.length,
                files: merged.map(f => f.file_name)
              });
              return merged;
            }
            return prev;
          });
        } catch (error) {
          // 404 错误是正常的（session 可能还没创建），不影响已有的 mentionFiles
          console.warn('⚠️ 加载文件列表失败（可能 session 还未创建）:', error);
        }
      } else {
        console.log('%c📁 [loadFiles] sessionId 为空，跳过加载', 'color: #FF9500');
      }
      // 注意：即使 sessionId 为空，也不清空 mentionFiles，因为可能使用 files 状态中的文件
    };
    loadFiles();
  }, [sessionId]);
  
  // 📁 同步 files 状态到 mentionFiles（用于新对话时文件上传后立即可用）
  useEffect(() => {
    // 如果 files 状态有文件，且 mentionFiles 为空或文件数量不匹配，同步文件
    if (files.length > 0) {
      // 将 FileInfo 转换为 SessionFile 格式
      const sessionFilesFromState: SessionFile[] = files.map(file => ({
        doc_id: file.id, // 使用 file.id 作为临时 doc_id
        file_name: file.name,
        file_type: file.type || 'application/octet-stream',
        file_size: file.size || null,
        uploaded_at: file.created_at.toISOString(),
      }));
      
      // 合并 mentionFiles 和 files 中的文件（去重）
      const existingFileNames = new Set(mentionFiles.map(f => f.file_name));
      const newFiles = sessionFilesFromState.filter(f => !existingFileNames.has(f.file_name));
      
      if (newFiles.length > 0) {
        setMentionFiles(prev => [...prev, ...newFiles]);
        console.log('%c📁 同步文件到 @ 提及列表:', 'color: #5856D6; font-weight: bold', {
          new_files: newFiles.map(f => f.file_name),
          total: mentionFiles.length + newFiles.length
        });
      }
    }
  }, [files]); // 监听 files 状态变化

  // 🔑 初始化时从 localStorage 恢复 session_id 并加载历史记录
  useEffect(() => {
    const loadHistory = async () => {
      const savedSessionId = getLocalSessionId();
      if (savedSessionId) {
        setSessionId(savedSessionId);
        if (onSessionChange) {
          onSessionChange(savedSessionId);
        }
        console.log('%c📥 从 localStorage 恢复会话:', 'color: #FF9500; font-weight: bold', savedSessionId);
        
        // 加载历史记录
        try {
          console.log('%c📚 开始加载对话历史...', 'color: #007AFF; font-weight: bold');
          const history = await getConversationHistory(savedSessionId, MESSAGES_PER_PAGE, 0);
          if (history && history.messages.length > 0) {
            console.log('%c📋 准备设置消息:', 'color: #007AFF; font-weight: bold', {
              message_count: history.messages.length,
              total: history.total,
              has_more: history.has_more,
              messages: history.messages.map(m => ({
                id: m.id,
                sender: m.sender,
                text_length: m.text?.length || 0,
                text_preview: m.text?.substring(0, 50) || '(空)'
              }))
            });
            setMessages(history.messages);
            setHistoryTotal(history.total || null);
            setHistoryHasMore(history.has_more || false);
            setHistoryOffset(history.messages.length);
            
            // 🔧 检查最新的一条 AI 消息是否有任务进度，如果有则标记需要展开
            const latestAIMessageWithTodos = [...history.messages]
              .reverse() // 反转数组，从最新到最旧
              .find(msg => {
                if (msg.sender !== Sender.AI) return false;
                if (msg.tool_calls && msg.tool_calls.length > 0) {
                  return msg.tool_calls.some(tc => isTodoTool(tc.tool_name));
                }
                return false;
              });
            
            if (latestAIMessageWithTodos) {
              setLatestHistoryMessageIdWithTodos(latestAIMessageWithTodos.id);
              console.log('%c📋 [加载历史] 找到最新一条有任务进度的消息，将自动展开', 'color: #34C759; font-weight: bold', {
                message_id: latestAIMessageWithTodos.id,
                conversation_turn_id: latestAIMessageWithTodos.conversation_turn_id,
                tool_calls_count: latestAIMessageWithTodos.tool_calls?.length || 0
              });
            } else {
              setLatestHistoryMessageIdWithTodos(null);
              console.log('%c📋 [加载历史] 没有找到有任务进度的消息', 'color: #007AFF');
            }
            
            // 🔧 修复问题1：加载文件事件列表，确保文件链接不丢失
            if (history.file_events && history.file_events.length > 0) {
              console.log('%c📁 [修复问题1] 加载文件事件列表:', 'color: #5856D6; font-weight: bold', {
                file_events_count: history.file_events.length,
                raw_file_events: history.file_events.map((fe: any) => ({
                  file_name: fe.file_name,
                  file_path: fe.file_path,
                  file_url: fe.file_url || '(缺失)',
                  conversation_turn_id: fe.conversation_turn_id
                }))
              });
              
              const fileInfos = history.file_events.map((fe: any, index: number) => {
                // 🔧 确保所有字段都正确设置，特别是 file_url
                const fileInfo = {
                  id: `file-history-${index}-${Date.now()}`,
                  name: fe.file_name || '未知文件',
                  path: fe.file_path || '',
                  url: fe.file_url || '', // 确保 file_url 被正确设置，即使为空也要设置
                  size: fe.file_size || 0,
                  type: fe.file_type || '文件',
                  conversation_turn_id: fe.conversation_turn_id || '',
                  created_at: new Date(fe.created_at),
                };
                
                // 🔧 如果 file_url 缺失但 file_path 存在，记录警告（可能是上传失败或未上传）
                if (!fileInfo.url && fileInfo.path) {
                  console.warn('⚠️ [修复问题1] 文件事件缺少 file_url（可能是本地文件未上传）:', {
                    file_name: fileInfo.name,
                    file_path: fileInfo.path,
                    conversation_turn_id: fileInfo.conversation_turn_id
                  });
                }
                
                return fileInfo;
              });
              
              console.log('%c📁 [修复问题1] 文件事件处理完成:', 'color: #5856D6; font-weight: bold', {
                total_files: fileInfos.length,
                files_with_url: fileInfos.filter(f => f.url).length,
                files_without_url: fileInfos.filter(f => !f.url).length,
                files_detail: fileInfos.map(f => ({
                  name: f.name,
                  conversation_turn_id: f.conversation_turn_id,
                  path: f.path,
                  url: f.url || '(无链接)'
                }))
              });
              
              setFiles(fileInfos);
            } else {
              // 如果没有文件事件，确保清空文件列表（避免显示上一个会话的文件）
              console.log('%c📁 [加载历史] 没有文件事件，清空文件列表', 'color: #5856D6');
              setFiles([]);
            }
            console.log('%c✅ 对话历史加载成功:', 'color: #34C759; font-weight: bold', {
              session_id: history.session_id,
              message_count: history.messages.length
            });
          } else {
            // 如果没有历史记录，显示欢迎消息
            setMessages([
              { id: 'm1', text: 'X 智能核心已就绪。所有分析请求将实时同步至多维工作区。', sender: Sender.AI, timestamp: new Date() }
            ]);
            console.log('%cℹ️ 没有历史记录，显示欢迎消息', 'color: #007AFF');
          }
        } catch (error) {
          console.error('❌ 加载对话历史失败:', error);
          // 加载失败时显示欢迎消息
          setMessages([
            { id: 'm1', text: 'X 智能核心已就绪。所有分析请求将实时同步至多维工作区。', sender: Sender.AI, timestamp: new Date() }
          ]);
        }
      } else {
        // 没有 session_id，显示欢迎消息
        setMessages([
          { id: 'm1', text: 'X 智能核心已就绪。所有分析请求将实时同步至多维工作区。', sender: Sender.AI, timestamp: new Date() }
        ]);
        if (onSessionChange) {
          onSessionChange(null);
        }
      }
    };

    loadHistory();
  }, [onSessionChange]);

  // 🔄 切换标签页时重置工具相关状态
  const prevActiveTabRef = useRef<'realtime' | 'browser' | 'files' | 'tools' | 'dataflow'>(activeTab);
  useEffect(() => {
    // 切换到工具标签页或库标签页时，从 localStorage 恢复 selectedTurnId（统一逻辑）
    if ((activeTab === 'tools' || activeTab === 'files') && prevActiveTabRef.current !== activeTab) {
      // ⚠️ 重要：切换到工具标签页或库标签页时，强制从 localStorage 恢复 selectedTurnId
      const savedTurnId = localStorage.getItem('selected_conversation_turn_id');
      console.log(`%c🔄 切换到${activeTab === 'tools' ? '工具' : '库'}标签页:`, 'color: #007AFF; font-weight: bold', {
        saved_conversation_turn_id_from_localStorage: savedTurnId,
        current_selectedTurnId: selectedTurnId,
        will_restore: !!savedTurnId
      });
      
      // 强制从 localStorage 恢复（即使状态中有值，也确保同步）
      if (savedTurnId) {
        console.log('%c📥 从 localStorage 恢复 selectedTurnId:', 'color: #FF9500; font-weight: bold', {
          conversation_turn_id: savedTurnId,
          conversation_turn_id_type: typeof savedTurnId,
          conversation_turn_id_value: String(savedTurnId)
        });
        setSelectedTurnId(savedTurnId);
      } else {
        console.warn('%c⚠️ localStorage 中没有 selected_conversation_turn_id', 'color: #FF9500; font-weight: bold');
      }
      
      // 只在工具标签页时重置工具详情选择
      if (activeTab === 'tools') {
      setSelectedToolCall(null);
      console.log('%c✅ 工具标签页切换完成，等待 useEffect 提取工具调用', 'color: #34C759; font-weight: bold', {
        selectedTurnId: savedTurnId || selectedTurnId,
        conversation_turn_id: savedTurnId || selectedTurnId
      });
      } else if (activeTab === 'files') {
        console.log('%c✅ 库标签页切换完成，将根据 selectedTurnId 过滤文件', 'color: #34C759; font-weight: bold', {
          selectedTurnId: savedTurnId || selectedTurnId,
          conversation_turn_id: savedTurnId || selectedTurnId
        });
      } else if (activeTab === 'dataflow') {
        console.log('%c✅ 数据链路标签页切换完成，将显示 selectedTurnId 的数据链路', 'color: #34C759; font-weight: bold', {
          selectedTurnId: savedTurnId || selectedTurnId,
          conversation_turn_id: savedTurnId || selectedTurnId
        });
      }
    } else if (activeTab !== 'tools' && activeTab !== 'files' && activeTab !== 'dataflow') {
      // 切换到其他标签页时，重置工具相关状态（但不重置轮次选择，因为用户可能在其他地方使用）
      setSelectedToolCall(null);
      // 注意：不重置 selectedTurnId，因为用户可能在其他地方选择了轮次
    }
    prevActiveTabRef.current = activeTab;
  }, [activeTab, selectedTurnId]);

  // 🔧 从消息中提取工具调用并设置到 toolCalls 状态
  // 优先显示 selectedTurnId 对应的轮次，如果没有则显示当前轮次（最新轮次）
  useEffect(() => {
    // ⚠️ 重要：只在工具标签页激活时才提取工具调用
    if (activeTab !== 'tools') {
      console.log('%c⏭️ 跳过工具调用提取（当前不在工具标签页）', 'color: #FF9500', {
        activeTab: activeTab
      });
      return;
    }
    
    // ⚠️ 重要：优先从 localStorage 读取 selectedTurnId（确保不丢失）
    const savedTurnId = localStorage.getItem('selected_conversation_turn_id');
    const effectiveTurnId = selectedTurnId || savedTurnId;
    
    console.log('%c🔧 [useEffect] 开始提取工具调用（工具标签页激活）', 'color: #007AFF; font-weight: bold', {
      session_id: sessionId,
      messages_count: messages.length,
      messages_with_tool_calls: messages.filter(m => m.tool_calls && m.tool_calls.length > 0).length,
      activeTab: activeTab,
      selectedTurnId: selectedTurnId,
      selectedTurnId_type: typeof selectedTurnId,
      savedTurnId_from_localStorage: savedTurnId,
      savedTurnId_type: typeof savedTurnId,
      effectiveTurnId: effectiveTurnId,
      effectiveTurnId_type: typeof effectiveTurnId,
      effectiveTurnId_value: String(effectiveTurnId || '')
    });
    
    // 确定目标轮次：
    // 1. 优先使用 selectedTurnId（状态中的值）
    // 2. 如果 selectedTurnId 为空，使用 localStorage 中的值
    // 3. 如果都没有，使用当前轮次（最新的 AI 消息的 conversation_turn_id）
    let targetTurnId: string | null = null;
    
    if (effectiveTurnId) {
      // 用户选择了特定轮次（从状态或 localStorage）
      targetTurnId = effectiveTurnId;
      // 如果状态中没有但 localStorage 有，同步到状态
      if (!selectedTurnId && savedTurnId) {
        setSelectedTurnId(savedTurnId);
      }
      console.log('%c🎯 使用用户选择的轮次ID:', 'color: #34C759; font-weight: bold', {
        conversation_turn_id: targetTurnId,
        conversation_turn_id_type: typeof targetTurnId,
        conversation_turn_id_value: String(targetTurnId),
        source: selectedTurnId ? 'state' : 'localStorage'
      });
    } else {
      // 使用当前轮次（最新轮次）
      const latestAIMessage = [...messages]
        .filter(m => m.sender === Sender.AI)
        .sort((a, b) => {
          const timeA = a.timestamp instanceof Date ? a.timestamp.getTime() : new Date(a.timestamp).getTime();
          const timeB = b.timestamp instanceof Date ? b.timestamp.getTime() : new Date(b.timestamp).getTime();
          return timeB - timeA;
        })[0];
      
      targetTurnId = latestAIMessage?.conversation_turn_id || null;
      console.log('%c🎯 使用当前轮次ID（最新轮次）:', 'color: #34C759; font-weight: bold', {
        conversation_turn_id: targetTurnId,
        conversation_turn_id_type: typeof targetTurnId,
        conversation_turn_id_value: String(targetTurnId || ''),
        latestAIMessage_id: latestAIMessage?.id,
        latestAIMessage_timestamp: latestAIMessage?.timestamp
      });
    }
    
    // 当消息变化时，重新提取工具调用（只提取目标轮次的工具调用）
    const extractedToolCalls: ToolCall[] = [];
    
    // 遍历当前会话的消息，只提取目标轮次的工具调用
    messages.forEach((msg) => {
      if (msg.tool_calls && msg.tool_calls.length > 0) {
        console.log('%c📋 处理消息的工具调用:', 'color: #34C759', {
          message_id: msg.id,
          message_turn_id: msg.conversation_turn_id,
          tool_calls_count: msg.tool_calls.length,
          tool_calls: msg.tool_calls.map(tc => ({
            tool_use_id: tc.tool_use_id.substring(0, 20),
            tool_name: tc.tool_name,
            conversation_turn_id: (tc as any).conversation_turn_id
          }))
        });
        
        msg.tool_calls.forEach((toolCall) => {
          // 转换为 ToolCall 格式，包含对话轮次信息
          const toolCallTurnId = (toolCall as any).conversation_turn_id || msg.conversation_turn_id || null;
          
          // ⚠️ 只提取目标轮次的工具调用
          const toolTurnIdStr = String(toolCallTurnId || '');
          const targetTurnIdStr = String(targetTurnId || '');
          const isMatch = toolTurnIdStr === targetTurnIdStr;
          
          console.log('%c🔍 工具调用轮次匹配检查:', 'color: #007AFF', {
            tool_name: toolCall.tool_name,
            tool_conversation_turn_id: toolCallTurnId,
            tool_conversation_turn_id_type: typeof toolCallTurnId,
            tool_conversation_turn_id_value: toolTurnIdStr,
            target_conversation_turn_id: targetTurnId,
            target_conversation_turn_id_type: typeof targetTurnId,
            target_conversation_turn_id_value: targetTurnIdStr,
            selectedTurnId: selectedTurnId,
            selectedTurnId_type: typeof selectedTurnId,
            isMatch: isMatch
          });
          
          if (!isMatch) {
            console.log('%c⏭️ 跳过非目标轮次的工具调用:', 'color: #FF9500', {
              tool_name: toolCall.tool_name,
              tool_turn_id: toolCallTurnId,
              target_turn_id: targetTurnId
            });
            return; // 跳过非目标轮次的工具调用
          }
          
          // 🔍 判断工具状态：如果 tool_output 存在（不为 null/undefined），即使为空字符串也视为成功
          // 因为工具已经执行完成，只是输出为空
          const hasToolOutput = toolCall.tool_output !== null && toolCall.tool_output !== undefined;
          const toolStatus: 'success' | 'error' | 'running' = hasToolOutput ? 'success' : 'running';
          
          const toolCallData: ToolCall = {
            tool_use_id: toolCall.tool_use_id,
            tool_name: toolCall.tool_name,
            input: toolCall.tool_input || {},
            output: toolCall.tool_output || null,
            timestamp: msg.timestamp instanceof Date 
              ? msg.timestamp.toLocaleTimeString('zh-CN')
              : new Date(msg.timestamp).toLocaleTimeString('zh-CN'),
            status: toolStatus,
            // 优先使用 toolCall 自己的 conversation_turn_id，如果没有则使用消息的
            conversation_turn_id: toolCallTurnId,
            message_id: msg.id
          };
          extractedToolCalls.push(toolCallData);
          
          console.log('%c✅ 提取工具调用:', 'color: #FF9500', {
            tool_use_id: toolCall.tool_use_id.substring(0, 20),
            tool_name: toolCall.tool_name,
            conversation_turn_id: toolCallTurnId,
            conversation_turn_id_type: typeof toolCallTurnId,
            conversation_turn_id_value: String(toolCallTurnId || ''),
            from_toolCall: (toolCall as any).conversation_turn_id,
            from_message: msg.conversation_turn_id,
            target_turn_id: targetTurnId
          });
        });
      }
    });

    // 无论是否有工具调用，都更新状态（切换会话时清空旧数据）
    console.log('%c📊 工具调用提取完成:', 'color: #007AFF; font-weight: bold', {
      total_extracted: extractedToolCalls.length,
      unique_turn_ids: [...new Set(extractedToolCalls.map(t => t.conversation_turn_id))],
      turn_ids_count: [...new Set(extractedToolCalls.map(t => t.conversation_turn_id))].length
    });
    
    if (extractedToolCalls.length > 0) {
      // 详细检查每个工具调用的 conversation_turn_id
      const turnIds = extractedToolCalls.map(t => t.conversation_turn_id);
      const uniqueTurnIds = [...new Set(turnIds)];
      const toolsByTurn = new Map<string | null, ToolCall[]>();
      extractedToolCalls.forEach(tool => {
        const turnId = tool.conversation_turn_id || 'null';
        if (!toolsByTurn.has(turnId)) {
          toolsByTurn.set(turnId, []);
        }
        toolsByTurn.get(turnId)!.push(tool);
      });
      
      console.log('%c🔧 从目标轮次消息中提取工具调用:', 'color: #FF9500; font-weight: bold', {
        session_id: sessionId,
        target_turn_id: targetTurnId,
        target_turn_id_type: typeof targetTurnId,
        selectedTurnId: selectedTurnId,
        selectedTurnId_type: typeof selectedTurnId,
        total: extractedToolCalls.length,
        unique_turn_ids: uniqueTurnIds,
        turn_ids_count: uniqueTurnIds.length,
        tools_by_turn: Array.from(toolsByTurn.entries()).map(([turnId, tools]) => ({
          turn_id: turnId,
          turn_id_type: typeof turnId,
          tool_count: tools.length,
          tool_names: tools.map(t => t.tool_name)
        })),
        all_calls_detail: extractedToolCalls.map(t => ({
          id: t.tool_use_id.substring(0, 20) + '...',
          name: t.tool_name,
          status: t.status,
          conversation_turn_id: t.conversation_turn_id,
          conversation_turn_id_type: typeof t.conversation_turn_id,
          has_output: !!t.output
        }))
      });
      
      // 直接设置提取的工具调用（不合并，因为我们要显示特定轮次的工具调用）
      console.log('%c💾 准备设置 toolCalls 状态:', 'color: #34C759; font-weight: bold', {
        target_turn_id: targetTurnId,
        selectedTurnId: selectedTurnId,
        extracted_count: extractedToolCalls.length,
        extracted_tool_calls: extractedToolCalls.map(t => ({
          tool_name: t.tool_name,
          conversation_turn_id: t.conversation_turn_id,
          conversation_turn_id_value: String(t.conversation_turn_id || '')
        }))
      });
      setToolCalls(extractedToolCalls);
    } else {
      // 如果没有工具调用，清空 toolCalls（切换会话时清空旧数据）
      console.log('%c🔧 清空工具调用列表（当前会话无工具调用）', 'color: #FF9500; font-weight: bold', {
        session_id: sessionId,
        message_count: messages.length
      });
      setToolCalls([]);
    }
  }, [messages, sessionId, selectedTurnId, activeTab]); // 添加 activeTab 依赖，切换标签页时也重新提取

  // 监听外部会话切换（从 SessionHistory 组件触发）
  useEffect(() => {
    const handleStorageChange = async (e: StorageEvent) => {
      if (e.key === 'chat_session_id') {
        const newSessionId = e.newValue; // 可能是 null（新建对话时）
        
        if (newSessionId === null || newSessionId === '') {
          // 新建对话：清除所有状态
          console.log('%c➕ 检测到新建对话请求，清除所有状态', 'color: #34C759; font-weight: bold');
          setSessionId(null);
          setMessages([
            { id: 'm1', text: 'X 智能核心已就绪。所有分析请求将实时同步至多维工作区。', sender: Sender.AI, timestamp: new Date() }
          ]);
          setToolCalls([]);
          setFiles([]); // 🔍 清空文件列表（与工具标签页保持一致）
          // ⚠️ 不清空 mentionFiles，因为新对话时用户可能正在上传文件，需要保留 @ 功能
          // setMentionFiles([]); // 不清空，保留文件以便 @ 功能可用
          setSelectedTurnId(null);
          setSelectedToolCall(null);
          setWorkspaceMessageId(null);
          setLatestHistoryMessageIdWithTodos(null); // 🔧 清空历史消息的任务进度展开标记
          setTodos([]); // 🔧 清空 todos
          realtimeTodosRef.current = []; // 🔧 清空实时更新标记
          if (onSessionChange) {
            onSessionChange(null);
          }
          return;
        }
        
        if (newSessionId && newSessionId !== sessionId) {
          console.log('%c🔄 检测到会话切换:', 'color: #FF9500; font-weight: bold', newSessionId);
          setSessionId(newSessionId);
          if (onSessionChange) {
            onSessionChange(newSessionId);
          }
          
          // 加载新会话的历史记录
          // 先清空旧数据，避免显示上一个会话的工具调用和文件
          setMessages([]);
          setToolCalls([]);
          setTodos([]); // 🔧 清空 todos
          realtimeTodosRef.current = []; // 🔧 清空实时更新标记
          setFiles([]); // 🔍 清空文件列表（与工具标签页保持一致）
          setSelectedTurnId(null);
          setSelectedToolCall(null);
          setLatestHistoryMessageIdWithTodos(null); // 🔧 清空历史消息的任务进度展开标记
          
          try {
            const history = await getConversationHistory(newSessionId, MESSAGES_PER_PAGE, 0);
            if (history && history.messages.length > 0) {
              setHistoryTotal(history.total || null);
              setHistoryHasMore(history.has_more || false);
              setHistoryOffset(history.messages.length);
              setMessages(history.messages);
              
              // 🔧 检查最新的一条 AI 消息是否有任务进度，如果有则标记需要展开（切换会话时）
              const latestAIMessageWithTodos = [...history.messages]
                .reverse() // 反转数组，从最新到最旧
                .find(msg => {
                  if (msg.sender !== Sender.AI) return false;
                  if (msg.tool_calls && msg.tool_calls.length > 0) {
                    return msg.tool_calls.some(tc => isTodoTool(tc.tool_name));
                  }
                  return false;
                });
              
              if (latestAIMessageWithTodos) {
                setLatestHistoryMessageIdWithTodos(latestAIMessageWithTodos.id);
                console.log('%c📋 [切换会话] 找到最新一条有任务进度的消息，将自动展开', 'color: #34C759; font-weight: bold', {
                  message_id: latestAIMessageWithTodos.id,
                  conversation_turn_id: latestAIMessageWithTodos.conversation_turn_id,
                  tool_calls_count: latestAIMessageWithTodos.tool_calls?.length || 0
                });
              } else {
                setLatestHistoryMessageIdWithTodos(null);
                console.log('%c📋 [切换会话] 没有找到有任务进度的消息', 'color: #007AFF');
              }
              
              // 🔧 修复问题1：加载文件事件列表，确保文件链接不丢失（切换会话时）
              if (history.file_events && history.file_events.length > 0) {
                console.log('%c📁 [修复问题1-切换会话] 加载文件事件列表:', 'color: #5856D6; font-weight: bold', {
                  file_events_count: history.file_events.length,
                  raw_file_events: history.file_events.map((fe: any) => ({
                    file_name: fe.file_name,
                    file_path: fe.file_path,
                    file_url: fe.file_url || '(缺失)',
                    conversation_turn_id: fe.conversation_turn_id
                  }))
                });
                
                const fileInfos = history.file_events.map((fe: any, index: number) => {
                  // 🔧 确保所有字段都正确设置，特别是 file_url
                  const fileInfo = {
                    id: `file-history-${index}-${Date.now()}`,
                    name: fe.file_name || '未知文件',
                    path: fe.file_path || '',
                    url: fe.file_url || '', // 确保 file_url 被正确设置
                    size: fe.file_size || 0,
                    type: fe.file_type || '文件',
                    conversation_turn_id: fe.conversation_turn_id || '',
                    created_at: new Date(fe.created_at),
                  };
                  
                  // 🔧 如果 file_url 缺失但 file_path 存在，记录警告
                  if (!fileInfo.url && fileInfo.path) {
                    console.warn('⚠️ [修复问题1-切换会话] 文件事件缺少 file_url:', {
                      file_name: fileInfo.name,
                      file_path: fileInfo.path,
                      conversation_turn_id: fileInfo.conversation_turn_id
                    });
                  }
                  
                  return fileInfo;
                });
                
                console.log('%c📁 [修复问题1-切换会话] 文件事件处理完成:', 'color: #5856D6; font-weight: bold', {
                  total_files: fileInfos.length,
                  files_with_url: fileInfos.filter(f => f.url).length,
                  files_without_url: fileInfos.filter(f => !f.url).length
                });
                
                setFiles(fileInfos);
              } else {
                // 如果没有文件事件，确保清空文件列表
                setFiles([]);
              }
              
              console.log('%c✅ 新会话历史加载成功:', 'color: #34C759; font-weight: bold', {
                message_count: history.messages.length,
                file_events_count: history.file_events?.length || 0
              });
            } else {
              setMessages([
                { id: 'm1', text: 'X 智能核心已就绪。所有分析请求将实时同步至多维工作区。', sender: Sender.AI, timestamp: new Date() }
              ]);
              setToolCalls([]);
              setFiles([]); // 确保清空文件列表
            }
          } catch (error) {
            console.error('❌ 加载新会话历史失败:', error);
            setMessages([
              { id: 'm1', text: 'X 智能核心已就绪。所有分析请求将实时同步至多维工作区。', sender: Sender.AI, timestamp: new Date() }
            ]);
            setToolCalls([]);
            setFiles([]); // 确保清空文件列表
          }
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [sessionId, onSessionChange]);
  const [previewFile, setPreviewFile] = useState<any | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showRecommendations, setShowRecommendations] = useState(true);
  const [disappearingCardId, setDisappearingCardId] = useState<string | null>(null);
  const [shouldAutoExpandTodos, setShouldAutoExpandTodos] = useState(false); // 🔧 用于自动展开 TodoList（实时消息）
  const [latestHistoryMessageIdWithTodos, setLatestHistoryMessageIdWithTodos] = useState<string | null>(null); // 🔧 历史消息中最新一条有任务进度的消息 ID
  
  const [isCameraActive, setIsCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  
  // 语音录制相关状态
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<number | null>(null);
  // 视频框位置：使用 fixed 定位，相对于视口
  const [videoPosition, setVideoPosition] = useState(() => {
    // 从 localStorage 恢复位置，如果没有则默认在右下角
    const saved = localStorage.getItem('videoCameraPosition');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return { x: window.innerWidth - 168, y: window.innerHeight - 168 };
      }
    }
    return { x: window.innerWidth - 168, y: window.innerHeight - 168 };
  });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const videoContainerRef = useRef<HTMLDivElement>(null);
  const [pendingFiles, setPendingFiles] = useState<{name: string, type: string, data: string}[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const msgEnd = useRef<HTMLDivElement>(null);
  const wsEnd = useRef<HTMLDivElement>(null);
  const mentionDropdownRef = useRef<HTMLDivElement>(null); // 下拉菜单引用

  // 🛠️ 完整的工具调用解析（配对追踪）
  // 使用工具函数 parseToolCalls
  // 注意：parseToolCalls 函数已提取到 chat/utils/toolCallUtils.ts

  // 🔤 消息长度判断和摘要生成
  // 使用工具函数 getMessageDisplay
  // 注意：getMessageDisplay 函数已提取到 chat/utils/messageUtils.ts

  // 清理会话（组件卸载时）
  useEffect(() => {
    return () => {
      if (sessionId && backendProvider === 'claude') {
        deleteSession(sessionId);
      }
    };
  }, [sessionId, backendProvider]);

  useEffect(() => msgEnd.current?.scrollIntoView({ behavior: 'smooth' }), [messages]);
  // 流式响应时滚动到底部（使用 msgEnd 而不是 wsEnd，因为 wsEnd 在当前组件 DOM 中不存在）
  useEffect(() => { if (isLoading) msgEnd.current?.scrollIntoView({ behavior: 'smooth' }); }, [currentResponse, isLoading]);

  const toggleCamera = async () => {
    if (isCameraActive) {
      streamRef.current?.getTracks().forEach(track => track.stop());
      streamRef.current = null;
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      setIsCameraActive(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 480, height: 480 }, audio: false });
        streamRef.current = stream;
        setIsCameraActive(true);
        // 使用 setTimeout 确保 DOM 更新后再设置视频流
        setTimeout(() => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.play().catch(err => {
              console.error("视频播放失败:", err);
            });
          }
        }, 100);
      } catch (err) {
        console.error("无法开启摄像头:", err);
        alert("无法访问摄像头，请检查权限设置");
      }
    }
  };

  // 确保视频流正确加载
  useEffect(() => {
    if (isCameraActive && streamRef.current && videoRef.current) {
      if (videoRef.current.srcObject !== streamRef.current) {
        videoRef.current.srcObject = streamRef.current;
        videoRef.current.play().catch(err => {
          console.error("视频播放失败:", err);
        });
      }
    }
  }, [isCameraActive]);

  // 视频框拖拽功能 - 全页面拖拽
  const handleVideoMouseDown = (e: React.MouseEvent) => {
    if (!videoContainerRef.current) return;
    e.preventDefault(); // 防止文本选择
    const rect = videoContainerRef.current.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
    setIsDragging(true);
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      
      if (!videoContainerRef.current) return;
      
      const videoWidth = 128; // 视频框宽度
      const videoHeight = 128; // 视频框高度
      
      // 计算相对于视口的位置（fixed 定位）
      let newX = e.clientX - dragOffset.x;
      let newY = e.clientY - dragOffset.y;
      
      // 限制在视口范围内（防止拖出屏幕）
      const maxX = window.innerWidth - videoWidth;
      const maxY = window.innerHeight - videoHeight;
      
      newX = Math.max(0, Math.min(maxX, newX));
      newY = Math.max(0, Math.min(maxY, newY));
      
      const newPosition = { x: newX, y: newY };
      setVideoPosition(newPosition);
      // 实时保存位置到 localStorage
      localStorage.setItem('videoCameraPosition', JSON.stringify(newPosition));
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'grabbing';
    document.body.style.userSelect = 'none';
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging, dragOffset, videoPosition]);

  // 窗口大小改变时，调整视频框位置（防止超出视口）
  useEffect(() => {
    const handleResize = () => {
      const videoWidth = 128;
      const videoHeight = 128;
      setVideoPosition(prev => ({
        x: Math.min(prev.x, window.innerWidth - videoWidth),
        y: Math.min(prev.y, window.innerHeight - videoHeight)
      }));
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 语音录制功能
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        // 停止所有音频轨道
        stream.getTracks().forEach(track => track.stop());
        
        // 将录制的音频转换为 base64
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64Audio = (reader.result as string).split(',')[1];
          // 将音频添加到待发送文件列表
          setPendingFiles(prev => [...prev, {
            name: `语音_${new Date().toLocaleTimeString()}.webm`,
            type: 'audio/webm',
            data: base64Audio
          }]);
        };
        reader.readAsDataURL(audioBlob);
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      // 注意：计时器由 useEffect 管理，这里不需要手动启动
      
    } catch (err) {
      console.error("无法访问麦克风:", err);
      alert("无法访问麦克风，请检查权限设置");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (recordingTimerRef.current) {
        window.clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
      setRecordingTime(0);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // 使用 useEffect 管理计时器，确保状态同步
  useEffect(() => {
    if (isRecording) {
      // 如果正在录制，启动计时器
      if (!recordingTimerRef.current) {
        setRecordingTime(0);
        recordingTimerRef.current = window.setInterval(() => {
          setRecordingTime(prev => {
            const newTime = prev + 1;
            console.log('录制时长更新:', newTime); // 调试日志
            return newTime;
          });
        }, 1000);
        console.log('useEffect: 计时器已启动');
      }
    } else {
      // 如果停止录制，清除计时器
      if (recordingTimerRef.current) {
        window.clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
        console.log('useEffect: 计时器已清除');
      }
    }
    
    return () => {
      if (recordingTimerRef.current) {
        window.clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
    };
  }, [isRecording]);

  const captureFrame = useCallback(() => {
    if (!videoRef.current || !isCameraActive) return null;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.drawImage(videoRef.current, 0, 0);
    return canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
  }, [isCameraActive]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    for (const file of Array.from(files)) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const base64 = (event.target?.result as string).split(',')[1];
        setPendingFiles(prev => [...prev, { name: file.name, type: file.type, data: base64 }]);
      };
      reader.readAsDataURL(file);
    }
  };

  const removePendingFile = (index: number) => {
    setPendingFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleRegenerate = async (aiMessageId: string) => {
    // 找到要重新生成的 AI 消息的索引
    const aiIndex = messages.findIndex(m => m.id === aiMessageId);
    if (aiIndex === -1) return;

    // 找到该 AI 消息之前的最后一条用户消息
    const previousUserMessage = messages
      .slice(0, aiIndex)
      .reverse()
      .find(m => m.sender === Sender.User);

    if (!previousUserMessage) return;

    // 删除该 AI 消息及之后的所有消息
    setMessages(p => p.slice(0, aiIndex));

    // 重新发送用户消息
    await handleSend(previousUserMessage.text);
  };

  const handleSend = async (overrideText?: string) => {
    // 🔒 严格确保 overrideText 和 input 是字符串类型
    // 防止对象被转换为 [object Object]
    let safeOverride = '';
    if (overrideText !== undefined && overrideText !== null) {
      if (typeof overrideText === 'string') {
        safeOverride = overrideText;
      } else {
        // 如果传入的不是字符串，记录错误并尝试转换
        console.error('❌ handleSend 收到非字符串类型的 overrideText:', {
          type: typeof overrideText,
          value: overrideText,
          stringified: String(overrideText)
        });
        // 尝试安全转换，但如果结果是 [object Object] 则拒绝
        const converted = String(overrideText);
        if (converted === '[object Object]') {
          console.error('❌ 无法转换对象为有效文本，跳过发送');
          return;
        }
        safeOverride = converted;
      }
    }
    
    // 确保 input 是字符串，并检查是否为 [object Object]
    let safeInput = '';
    if (typeof input === 'string') {
      safeInput = input;
    } else if (input) {
      const converted = String(input);
      if (converted === '[object Object]') {
        console.error('❌ input 状态包含对象，已重置为空字符串');
        setInput('');
        safeInput = '';
      } else {
        safeInput = converted;
      }
    }
    
    const txt = safeOverride || safeInput.trim();
    
    // 最终验证：确保文本有效且不是 [object Object]
    if (!txt || txt === '[object Object]') {
      if (!isCameraActive && pendingFiles.length === 0) {
        console.warn('⚠️ 发送的文本为空或无效（对象）');
        return;
      }
    }
    
    if ((!txt && !isCameraActive && pendingFiles.length === 0) || isLoading) return;
    setInput('');
    setIsLoading(true);
    setCurrentResponse('');
    // 点击推荐问题或发送消息时自动展开工作区
    setIsWorkspaceOpen(true);
    setActiveTab('realtime');
    setShowRecommendations(false);

    console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #007AFF');
    console.log('%c💬 用户发送消息', 'color: #007AFF; font-weight: bold; font-size: 14px');
    console.log('  文本内容:', txt);
    console.log('  后端提供者:', backendProvider);
    console.log('  会话 ID:', sessionId);
    console.log('  摄像头状态:', isCameraActive ? '开启' : '关闭');
    console.log('  附件数量:', pendingFiles.length);
    console.log('  历史消息数:', messages.length);
    console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #007AFF');

    const multimodalParts: any[] = [];
    if (isCameraActive) {
      const frame = captureFrame();
      if (frame) multimodalParts.push({ inlineData: { data: frame, mimeType: 'image/jpeg' } });
    }
    pendingFiles.forEach(file => {
      multimodalParts.push({ inlineData: { data: file.data, mimeType: file.type || 'application/octet-stream' } });
    });

    setPendingFiles([]);
    const userMessageId = Date.now().toString();
    setMessages(p => [...p, { id: userMessageId, text: txt || "多模态数据分析请求", sender: Sender.User, timestamp: new Date() }]);

    try {
      let full = '';
      let chunkCount = 0;
      const collectedToolCalls: any[] = []; // 收集所有工具调用
      let collectedResultInfo: ResultInfo | undefined = undefined; // 收集 ResultMessage 信息
      const aiMessageId = `ai-${Date.now()}`; // 提前生成 AI 消息 ID，用于实时更新

      if (backendProvider === 'claude') {
        // 使用后端 Claude Agent 接口
        // 注意：第一次对话时 sessionId 为 null，接口会自动创建新会话
        console.log('%c📥 开始接收 Claude 流式响应', 'color: #34C759; font-weight: bold');
        console.log('  会话 ID:', sessionId || '(首次对话，将自动创建)');

        // 🔒 最终验证：确保 txt 是有效的字符串（不是 [object Object]）
        if (txt === '[object Object]' || typeof txt !== 'string') {
          console.error('❌ 最终验证失败：prompt 无效', { txt, type: typeof txt });
          setIsLoading(false);
          setCurrentResponse('错误：无法发送无效的文本内容');
          return;
        }

        // 创建临时 AI 消息，用于实时显示
        setMessages(p => [...p, {
          id: aiMessageId,
          text: '',
          sender: Sender.AI,
          timestamp: new Date(),
          tool_calls: []
        }]);

        // 准备文件附件（如果有）
        const attachments = pendingFiles.length > 0 ? pendingFiles.map(file => ({
          name: file.name,
          type: file.type || 'application/octet-stream',
          data: file.data, // Base64 data (already encoded)
        })) : undefined;

        for await (const chunk of streamAgentQuery(txt, sessionId, undefined, attachments)) {
          if (chunk.error) {
            console.error('❌ 流式响应错误:', chunk.error);
            setCurrentResponse(`错误: ${chunk.error}`);
            break;
          }

          // 保存 session_id（如果返回了新的）
          if (chunk.sessionId && chunk.sessionId !== sessionId) {
            setSessionId(chunk.sessionId);
            console.log('%c✅ 会话 ID 已保存到 state:', 'color: #FF9500; font-weight: bold', chunk.sessionId);
            console.log('  下次对话将使用此 session_id');
          }

          // 收集 ResultMessage 信息
          if (chunk.resultInfo) {
            collectedResultInfo = chunk.resultInfo;
            console.log('%c📊 收集到 Result 信息:', 'color: #007AFF; font-weight: bold', collectedResultInfo);
          }

          // 🔧 检测到 max_turns 错误时，也视为对话完成
          // 当达到最大轮次限制时，backend 会发送 resultInfo.subtype='error_max_turns'
          // 但不发送 isComplete=true，所以前端需要主动检测并触发完成流程
          const isMaxTurnsError = chunk.resultInfo?.subtype === 'error_max_turns';

          // 🔧 检测后端发送的 type='end' 事件（流结束标记）
          // 后端在会话完成时发送 StreamChunk(type="end", data={"status": "completed"})
          // 前端需要识别这个事件并触发完成流程
          const isStreamEnd = (chunk as any).type === 'end' || (chunk as any).data?.status === 'completed';

          // 处理文件事件
          if (chunk.fileEvent) {
            const fileEvent = chunk.fileEvent;
            
            const fileInfo: FileInfo = {
              id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              name: fileEvent.file_name || '未知文件',
              path: fileEvent.file_path,
              url: fileEvent.file_url,
              size: fileEvent.file_size,
              type: fileEvent.file_type,
              conversation_turn_id: fileEvent.conversation_turn_id || '',
              created_at: new Date(),
              file_content: fileEvent.file_content, // 🔧 新增：如果 event 中包含文件内容，直接保存
            };
            
            setFiles(prev => [...prev, fileInfo]);
            
            // 立即更新 mentionFiles，使 @ 功能立即可用
            // 优先使用 fileEvent 中的 doc_id（如果存在），否则从 file_path 提取
            let docId = fileInfo.id; // 默认使用临时 ID
            
            // 优先使用 fileEvent.doc_id（后端直接提供）
            if (fileEvent.doc_id) {
              docId = fileEvent.doc_id;
            } else if (fileEvent.file_path && fileEvent.file_path.includes('user-upload-')) {
              // 从 file_path 提取 doc_id
              const pathParts = fileEvent.file_path.split('/');
              const fileName = pathParts[pathParts.length - 1];
              // 提取 doc_id（去掉扩展名）
              const nameWithoutExt = fileName.replace(/\.[^.]+$/, '');
              if (nameWithoutExt && nameWithoutExt.startsWith('user-upload-')) {
                docId = nameWithoutExt;
              }
            }
            
            const newMentionFile: SessionFile = {
              doc_id: docId,
              file_name: fileInfo.name,
              file_type: fileInfo.type || 'application/octet-stream',
              file_size: fileInfo.size || null,
              uploaded_at: fileInfo.created_at.toISOString(),
            };
            
            setMentionFiles(prev => {
              // 检查是否已存在（避免重复）- 使用 doc_id 检查
              const exists = prev.some(f => f.doc_id === newMentionFile.doc_id);
              if (!exists) {
                return [...prev, newMentionFile];
              }
              return prev;
            });
          }

          // 处理 toolStart 事件（工具调用开始）
          if (chunk.toolStart) {
            console.log('%c🚀 检测到工具开始事件:', 'color: #FF9500; font-weight: bold', {
              tool_name: chunk.toolStart.tool_name,
              tool_use_id: chunk.toolStart.tool_use_id?.substring(0, 20),
              tool_input_keys: chunk.toolStart.tool_input ? Object.keys(chunk.toolStart.tool_input) : [],
              tool_input_todos: chunk.toolStart.tool_input?.todos ? (typeof chunk.toolStart.tool_input.todos === 'string' ? 'string' : Array.isArray(chunk.toolStart.tool_input.todos) ? `array[${chunk.toolStart.tool_input.todos.length}]` : typeof chunk.toolStart.tool_input.todos) : 'none',
              collectedToolCalls_count: collectedToolCalls.length,
              collectedToolCalls_ids: collectedToolCalls.map(tc => tc.tool_use_id?.substring(0, 20)),
              full_chunk: chunk
            });
            
            // 🔧 如果检测到 TodoWrite 工具调用，设置自动展开标志
            if (isTodoTool(chunk.toolStart.tool_name)) {
              setShouldAutoExpandTodos(true);
              console.log('%c📋 [实时对话] 检测到 TodoWrite，将自动展开 TodoList', 'color: #34C759; font-weight: bold');
            }
            
            // 🔧 修复：去重处理，只保留每个 tool_use_id 的最新版本
            // 🔧 移除 tool_input 中的临时 _index 字段（后端用于建立映射，前端不需要）
            const toolInput = { ...chunk.toolStart.tool_input };
            if ('_index' in toolInput) {
              delete toolInput._index;
            }
            
            // 🔧 关键修复：如果 todos 是字符串（JSON字符串），需要解析为数组
            if (toolInput.todos && typeof toolInput.todos === 'string') {
              try {
                toolInput.todos = JSON.parse(toolInput.todos);
                console.log('%c✅ [toolStart] 成功解析 todos JSON字符串', 'color: #34C759; font-weight: bold', {
                  tool_use_id: chunk.toolStart.tool_use_id?.substring(0, 20),
                  todos_count: Array.isArray(toolInput.todos) ? toolInput.todos.length : 0
                });
              } catch (e) {
                console.warn('%c⚠️ [toolStart] 解析 todos JSON字符串失败:', 'color: #FF9500; font-weight: bold', e, {
                  todos_string: toolInput.todos.substring(0, 100)
                });
              }
            }
            
            const newToolCall = {
              tool_use_id: chunk.toolStart.tool_use_id,
              tool_name: chunk.toolStart.tool_name,
              input: toolInput,
              tool_input: toolInput,
              status: 'running',
              timestamp: chunk.toolStart.timestamp || new Date().toLocaleTimeString('zh-CN')
            };
            
            const existingIndex = collectedToolCalls.findIndex(
              (existing: any) => existing.tool_use_id === newToolCall.tool_use_id
            );
            if (existingIndex >= 0) {
              // 🔧 替换已存在的条目（可能是临时工具调用，现在用真实数据替换）
              const wasTemporary = collectedToolCalls[existingIndex].tool_name === 'enhanced_todo_write' && 
                                   Object.keys(collectedToolCalls[existingIndex].input || {}).length === 0;
              if (wasTemporary) {
                console.log('%c✅ toolStart: 替换临时工具调用为真实工具调用', 'color: #34C759; font-weight: bold', {
                  tool_use_id: newToolCall.tool_use_id?.substring(0, 20),
                  tool_name: newToolCall.tool_name
                });
              }
              // 保留已有的 input 数据（如果临时工具调用已经接收了 toolInputDelta 数据）
              if (collectedToolCalls[existingIndex].input && Object.keys(collectedToolCalls[existingIndex].input).length > 0) {
                newToolCall.input = { ...collectedToolCalls[existingIndex].input, ...newToolCall.input };
                newToolCall.tool_input = { ...collectedToolCalls[existingIndex].tool_input, ...newToolCall.tool_input };
              }
              collectedToolCalls[existingIndex] = newToolCall;
            } else {
              // 添加新条目
              collectedToolCalls.push(newToolCall);
              console.log('%c✅ toolStart: 添加新工具调用', 'color: #34C759; font-weight: bold', {
                tool_use_id: newToolCall.tool_use_id?.substring(0, 20),
                tool_name: newToolCall.tool_name
              });
            }
            
            // 实时更新 AI 消息的 tool_calls
            const toolCallsInfo = collectedToolCalls.map(tc => {
              const toolInput = tc.input || tc.tool_input || {};
              // 🔧 确保 tool_input 中的 todos 是数组而不是字符串
              const processedToolInput = { ...toolInput };
              if (processedToolInput.todos && typeof processedToolInput.todos === 'string') {
                try {
                  processedToolInput.todos = JSON.parse(processedToolInput.todos);
                  console.log('%c✅ [toolStart] 在 toolCallsInfo 中解析 todos JSON字符串', 'color: #34C759; font-weight: bold', {
                    tool_use_id: tc.tool_use_id?.substring(0, 20),
                    todos_count: Array.isArray(processedToolInput.todos) ? processedToolInput.todos.length : 0
                  });
                } catch (e) {
                  console.warn('[toolStart] 解析 tool_input.todos 失败:', e);
                }
              }
              return {
                tool_use_id: tc.tool_use_id || '',
                tool_name: tc.tool_name || 'Unknown',
                tool_input: processedToolInput,
                tool_output: tc.output || null,
                conversation_turn_id: null,
              };
            });
            
            // 特别检查 TodoWrite 工具调用
            const todoWriteCalls = toolCallsInfo.filter(tc => isTodoTool(tc.tool_name));
            if (todoWriteCalls.length > 0) {
              const latestTodoWrite = todoWriteCalls[todoWriteCalls.length - 1];
              const todosData = parseTodosData(latestTodoWrite?.tool_input?.todos);
              console.log('%c📋 [toolStart] TodoWrite 工具调用:', 'color: #34C759; font-weight: bold', {
                todoWrite_count: todoWriteCalls.length,
                total_tool_calls: toolCallsInfo.length,
                latest_todos_count: todosData?.length || 0,
                latest_todos_statuses: todosData?.map((t: any) => t.status) || []
              });
            }
            
            // 🔧 修复：确保React检测到变化，通过创建新对象和深拷贝tool_calls
            setMessages(p => p.map(msg => {
              if (msg.id === aiMessageId) {
                // 🔧 创建新的tool_calls数组，确保React检测到变化
                const newToolCalls = toolCallsInfo.map(tc => ({
                  ...tc,
                  tool_input: tc.tool_input ? { ...tc.tool_input } : null
                }));
                
                console.log('%c✅ [toolStart] 更新消息，触发重新渲染', 'color: #34C759; font-weight: bold', {
                  message_id: aiMessageId,
                  tool_calls_count: newToolCalls.length,
                  todoWrite_count: todoWriteCalls.length
                });
                
                return {
                  ...msg,
                  text: full || msg.text,
                  tool_calls: newToolCalls,
                  // 🔧 添加一个时间戳字段，确保React检测到变化
                  _updatedAt: Date.now()
                };
              }
              return msg;
            }));
          }

          // 🔧 处理工具调用的流式输入更新（tool_input_delta）
          // ⚠️ 重要：toolInputDelta 必须在 toolStart 之后处理，确保工具调用已建立
          if (chunk.toolInputDelta) {
            const { tool_use_id, partial_json } = chunk.toolInputDelta;
            console.log('%c🔄 [实时更新] 工具输入增量:', 'color: #FF9500; font-weight: bold', {
              tool_use_id: tool_use_id?.substring(0, 20),
              partial_json_length: partial_json?.length || 0,
              partial_json_preview: partial_json?.substring(0, 200),
              collectedToolCalls_count: collectedToolCalls.length,
              collectedToolCalls_ids: collectedToolCalls.map(tc => tc.tool_use_id?.substring(0, 20)),
              full_chunk: chunk
            });
            
            // 找到对应的工具调用并更新 input
            let existingIndex = collectedToolCalls.findIndex(
              (tc: any) => tc.tool_use_id === tool_use_id
            );
            
            // 🔧 如果找不到对应的工具调用，创建一个临时工具调用（toolInputDelta 可能先于 toolStart 到达）
            // 注意：这应该很少发生，因为后端已经确保 tool_start 先发送
            if (existingIndex < 0) {
              console.warn('%c⚠️ toolInputDelta: 找不到对应的工具调用，创建临时工具调用（toolStart 可能尚未到达）', 'color: #FF9500; font-weight: bold', {
                tool_use_id: tool_use_id?.substring(0, 20),
                collectedToolCalls_ids: collectedToolCalls.map(tc => tc.tool_use_id?.substring(0, 20)),
                collectedToolCalls_count: collectedToolCalls.length
              });
              // 创建临时工具调用，稍后会被 toolStart 事件更新
              collectedToolCalls.push({
                tool_use_id: tool_use_id,
                tool_name: 'enhanced_todo_write', // 临时名称，假设是 enhanced_todo_write（因为这是最常见的场景）
                input: {},
                tool_input: {},
                status: 'running',
                timestamp: new Date().toLocaleTimeString('zh-CN')
              });
              existingIndex = collectedToolCalls.length - 1;
              console.log('%c✅ 已创建临时工具调用，等待 toolStart 事件更新', 'color: #34C759; font-weight: bold', {
                tool_use_id: tool_use_id?.substring(0, 20),
                index: existingIndex
              });
            }
            
            if (existingIndex >= 0) {
              try {
                // 解析 partial_json（可能是完整的 JSON 字符串）
                // 注意：partial_json 可能是部分 JSON，需要尝试解析
                let parsedInput: any = {};
                if (partial_json) {
                  try {
                    // 尝试解析完整的 JSON
                    parsedInput = JSON.parse(partial_json);
                    
                    // 🔧 关键修复：如果 todos 是字符串（JSON字符串），需要再次解析
                    if (parsedInput.todos && typeof parsedInput.todos === 'string') {
                      try {
                        parsedInput.todos = JSON.parse(parsedInput.todos);
                        console.log('%c✅ [toolInputDelta] 成功解析嵌套的 todos JSON字符串', 'color: #34C759; font-weight: bold', {
                          todos_count: Array.isArray(parsedInput.todos) ? parsedInput.todos.length : 0,
                          todos_preview: Array.isArray(parsedInput.todos) ? parsedInput.todos.slice(0, 2).map((t: any) => ({
                            content: t.content,
                            status: t.status
                          })) : 'not an array'
                        });
                      } catch (e3) {
                        console.warn('%c⚠️ [toolInputDelta] 解析嵌套的 todos JSON字符串失败:', 'color: #FF9500; font-weight: bold', e3, {
                          todos_string: parsedInput.todos.substring(0, 100)
                        });
                      }
                    }
                  } catch (e) {
                    // 如果解析失败，可能是部分 JSON，尝试提取 todos 字段
                    const todosMatch = partial_json.match(/"todos"\s*:\s*"([^"]+)"/);
                    if (todosMatch) {
                      try {
                        const todosJson = JSON.parse(todosMatch[1]);
                        parsedInput = { todos: todosJson };
                      } catch (e2) {
                        console.warn('Failed to parse todos from partial_json:', e2);
                      }
                    }
                  }
                }
                
                // 更新工具调用的 input
                if (parsedInput.todos) {
                  // 🔧 确保 todos 是数组
                  const todosArray = Array.isArray(parsedInput.todos) ? parsedInput.todos : [];
                  collectedToolCalls[existingIndex] = {
                    ...collectedToolCalls[existingIndex],
                    input: { ...collectedToolCalls[existingIndex].input, ...parsedInput, todos: todosArray },
                    tool_input: { ...collectedToolCalls[existingIndex].tool_input, ...parsedInput, todos: todosArray }
                  };
                  
                  console.log('%c✅ [toolInputDelta] 更新工具调用 input', 'color: #34C759; font-weight: bold', {
                    tool_use_id: tool_use_id?.substring(0, 20),
                    todos_count: todosArray.length,
                    todos_statuses: todosArray.map((t: any) => ({ content: t.content?.substring(0, 20), status: t.status }))
                  });
                  
                  // 🔧 核心简化方案：如果是 TodoWrite 工具，总是使用最新的 enhanced_todo_write 工具调用来更新进度
                  const currentToolCall = collectedToolCalls[existingIndex];
                  if (isTodoTool(currentToolCall.tool_name || '')) {
                    // 🔧 关键修复：查找所有 enhanced_todo_write 工具调用，总是使用最新的
                    const allTodoWriteCalls = collectedToolCalls.filter(tc => isTodoTool(tc.tool_name));
                    const latestTodoWriteCall = allTodoWriteCalls[allTodoWriteCalls.length - 1];
                    
                    // 🔧 使用最新的工具调用的 todos（如果当前事件是最新的，使用当前事件的；否则使用最新的）
                    const latestTodosSource = latestTodoWriteCall === currentToolCall 
                      ? todosArray 
                      : parseTodosData(latestTodoWriteCall.input?.todos || latestTodoWriteCall.tool_input?.todos || []);
                    
                    const extractedTodos = parseTodosData(latestTodosSource).map((todo: any, idx: number) => {
                      // 🔧 修复：使用稳定的 ID 生成策略，确保同一个任务始终使用相同的 ID
                      // 优先使用 todo.id（如果后端提供了稳定的 id）
                      // 否则使用内容+level生成稳定的 id，而不是基于 tool_use_id
                      const stableId = todo.id || `todo-${todo.content || idx}-${todo.level || idx}`;
                      
                      return {
                        id: stableId,
                        content: todo.content || '',
                        status: todo.status || 'pending',
                        activeForm: todo.status === 'completed' ? undefined : todo.activeForm,
                        level: todo.level,
                        parentLevel: todo.parentLevel,
                      };
                    });
                    
                    // 🔧 直接更新 todos 状态，实时显示
                    if (extractedTodos.length > 0) {
                      realtimeTodosRef.current = extractedTodos; // 标记为实时更新
                      setTodos(extractedTodos);
                      console.log('%c🚀 [toolInputDelta] 实时更新 todos（使用最新的 enhanced_todo_write）', 'color: #34C759; font-weight: bold', {
                        current_tool_use_id: tool_use_id?.substring(0, 20),
                        latest_tool_use_id: latestTodoWriteCall.tool_use_id?.substring(0, 20),
                        is_latest: latestTodoWriteCall === currentToolCall,
                        total_todoWrite_calls: allTodoWriteCalls.length,
                        todos_count: extractedTodos.length,
                        todos_statuses: extractedTodos.map((t: any) => `${t.content?.substring(0, 15)}:${t.status}`),
                        note: '总是使用最新的 enhanced_todo_write 工具调用来更新进度'
                      });
                    }
                  }
                  
                  // 实时更新消息的 tool_calls
                  // 🔧 关键修复：保留所有工具调用，包括所有 TodoWrite 调用
                  // extractTodosFromToolCalls 会自己选择最新的 TodoWrite 调用
                  // 🔧 关键修复：在创建 toolCallsInfo 时就深拷贝 tool_input，确保 todos 数组是新引用
                  const toolCallsInfo = collectedToolCalls.map(tc => {
                    const toolInput = tc.input || tc.tool_input || {};
                    // 🔧 深拷贝 tool_input，确保 todos 数组是完全新的引用
                    const processedToolInput = toolInput && Object.keys(toolInput).length > 0
                      ? JSON.parse(JSON.stringify(toolInput))
                      : {};
                    
                    return {
                      tool_use_id: tc.tool_use_id || '',
                      tool_name: tc.tool_name || 'Unknown',
                      tool_input: processedToolInput,
                      tool_output: tc.output || null,
                      conversation_turn_id: null,
                    };
                  });
                  
                  const updatedTodoWrite = collectedToolCalls.find(tc => tc.tool_use_id === tool_use_id);
                  const todoWriteCalls = collectedToolCalls.filter(tc => isTodoTool(tc.tool_name));

                  const updatedTodosData = parseTodosData(updatedTodoWrite?.input?.todos || updatedTodoWrite?.tool_input?.todos);

                  console.log('%c🔄 [toolInputDelta] 更新 messages.tool_calls', 'color: #007AFF; font-weight: bold', {
                    tool_use_id: tool_use_id?.substring(0, 20),
                    total_tool_calls: toolCallsInfo.length,
                    todoWrite_calls: todoWriteCalls.length,
                    updated_todoWrite_tool_use_id: updatedTodoWrite?.tool_use_id?.substring(0, 20),
                    todos_in_updated: updatedTodosData?.length || 0,
                    todos_statuses: updatedTodosData?.map((t: any) => ({ content: t.content?.substring(0, 20), status: t.status })) || []
                  });
                  
                  // 🔧 修复：确保React检测到变化，通过创建新对象和深拷贝tool_calls
                  setMessages(p => p.map(msg => {
                    if (msg.id === aiMessageId) {
                      // 🔧 创建新的tool_calls数组，确保React检测到变化
                      // 🔧 关键修复：再次深拷贝 tool_input，确保完全独立
                      const newToolCalls = toolCallsInfo.map(tc => {
                        // 🔧 深拷贝整个 tool_input，确保 todos 数组是完全新的引用
                        const toolInput = tc.tool_input && Object.keys(tc.tool_input).length > 0
                          ? JSON.parse(JSON.stringify(tc.tool_input))
                          : null;
                        
                        return {
                          ...tc,
                          tool_input: toolInput
                        };
                      });
                      
                      console.log('%c✅ [toolInputDelta] 更新消息，触发重新渲染', 'color: #34C759; font-weight: bold', {
                        message_id: aiMessageId,
                        tool_calls_count: newToolCalls.length,
                        todos_count: updatedTodosData?.length || 0,
                        todos_statuses: updatedTodosData?.map((t: any) => ({ content: t.content?.substring(0, 20), status: t.status })) || []
                      });
                      
                      return {
                        ...msg,
                        tool_calls: newToolCalls,
                        // 🔧 添加一个时间戳字段，确保React检测到变化
                        _updatedAt: Date.now()
                      };
                    }
                    return msg;
                  }));
                }
              } catch (e) {
                console.error('Error processing toolInputDelta:', e);
              }
            }
          }

          // 收集工具调用信息，并实时更新消息
          if (chunk.toolCalls && chunk.toolCalls.length > 0) {
            console.log('%c🔧 收集到工具调用:', 'color: #FF9500; font-weight: bold', chunk.toolCalls.length, '个');
            
            // 🔧 如果检测到 TodoWrite 工具调用，设置自动展开标志
            const hasTodoWrite = chunk.toolCalls.some((tc: any) => isTodoTool(tc.tool_name));
            if (hasTodoWrite) {
              setShouldAutoExpandTodos(true);
              console.log('%c📋 [实时对话] 检测到 TodoWrite，将自动展开 TodoList', 'color: #34C759; font-weight: bold');
            }
            
            // 🔧 修复：去重处理，只保留每个 tool_use_id 的最新版本
            // 如果同一个 tool_use_id 出现多次（如 TodoWrite 更新），只保留最新的
            // ⚠️ 重要：如果新条目是 tool_result（tool_name 为 'Unknown'），保留原有的 tool_name
            chunk.toolCalls.forEach((newTc: any) => {
              // 🔧 关键修复：如果 input.todos 是字符串（JSON字符串），需要解析为数组
              let processedInput = { ...newTc.input };
              if (processedInput.todos && typeof processedInput.todos === 'string') {
                try {
                  processedInput.todos = JSON.parse(processedInput.todos);
                  console.log('%c✅ [toolCalls] 成功解析 todos JSON字符串', 'color: #34C759; font-weight: bold', {
                    tool_name: newTc.tool_name,
                    tool_use_id: newTc.tool_use_id?.substring(0, 20),
                    todos_count: Array.isArray(processedInput.todos) ? processedInput.todos.length : 0
                  });
                } catch (e) {
                  console.warn('%c⚠️ [toolCalls] 解析 todos JSON字符串失败:', 'color: #FF9500; font-weight: bold', e);
                }
              }
              
              // 更新 newTc 的 input
              const processedToolCall = {
                ...newTc,
                input: processedInput
              };
              
              const existingIndex = collectedToolCalls.findIndex(
                (existing: any) => existing.tool_use_id === processedToolCall.tool_use_id
              );
              if (existingIndex >= 0) {
                // 如果新条目是 tool_result（tool_name 为 'Unknown'），保留原有的 tool_name 和 tool_input
                if (processedToolCall.tool_name === 'Unknown' && collectedToolCalls[existingIndex].tool_name !== 'Unknown') {
                  // 合并：保留原有的 tool_name 和 tool_input，更新 output
                  collectedToolCalls[existingIndex] = {
                    ...collectedToolCalls[existingIndex],
                    output: processedToolCall.output,
                    is_error: processedToolCall.is_error,
                    status: 'completed'
                  };
                  
                  // 🔧 关键修复：当其他工具（如 WebSearch）完成时，智能推断并更新相关任务状态
                  // 如果当前有 TodoWrite 工具调用，且该工具执行成功，可以推断相关任务可能已完成或进行中
                  const todoWriteCall = collectedToolCalls.find(tc => isTodoTool(tc.tool_name));
                  if (todoWriteCall && !processedToolCall.is_error) {
                    // 检查是否有待处理或进行中的任务
                    const todos = parseTodosData(todoWriteCall.input?.todos || todoWriteCall.tool_input?.todos);
                    const pendingOrInProgressTodos = todos.filter((t: any) => 
                      t.status === 'pending' || t.status === 'in_progress'
                    );
                    
                    if (pendingOrInProgressTodos.length > 0) {
                      // 🔧 智能推断：如果工具执行成功，第一个待处理的任务可能变为进行中或已完成
                      // 这里我们保守地假设：如果工具执行成功，相关任务可能已完成
                      // 但为了不误判，我们只在 tool_input 中更新状态，不直接修改
                      console.log('%c🔍 [toolCalls] 检测到工具执行完成，可能影响任务状态', 'color: #007AFF; font-weight: bold', {
                        tool_name: collectedToolCalls[existingIndex].tool_name,
                        tool_use_id: processedToolCall.tool_use_id?.substring(0, 20),
                        pending_or_in_progress_todos: pendingOrInProgressTodos.length,
                        note: '任务状态更新需要等待 AI 调用 enhanced_todo_write 来确认'
                      });
                    }
                  }
                } else {
                  // 替换已存在的条目（使用最新的数据）
                  collectedToolCalls[existingIndex] = processedToolCall;
                }
              } else {
                // 添加新条目
                collectedToolCalls.push(processedToolCall);
              }
            });
            
            // 实时更新 AI 消息的 tool_calls
            // 🔧 关键修复：保留所有工具调用，包括所有 TodoWrite 调用
            // extractTodosFromToolCalls 会自己选择最新的 TodoWrite 调用
            // 🔧 关键修复：在创建 toolCallsInfo 时就深拷贝 tool_input，确保 todos 数组是新引用
            const toolCallsInfo = collectedToolCalls.map(tc => {
              const toolInput = tc.input || tc.tool_input || {};
              // 🔧 深拷贝 tool_input，确保 todos 数组是完全新的引用
              let processedToolInput = toolInput && Object.keys(toolInput).length > 0
                ? JSON.parse(JSON.stringify(toolInput))
                : {};
              
              // 🔧 确保 tool_input 中的 todos 是数组而不是字符串
              if (processedToolInput.todos && typeof processedToolInput.todos === 'string') {
                try {
                  processedToolInput.todos = JSON.parse(processedToolInput.todos);
                  console.log('%c✅ [toolCalls] 在 toolCallsInfo 中解析 todos JSON字符串', 'color: #34C759; font-weight: bold', {
                    tool_use_id: tc.tool_use_id?.substring(0, 20),
                    todos_count: Array.isArray(processedToolInput.todos) ? processedToolInput.todos.length : 0
                  });
                } catch (e) {
                  console.warn('[toolCalls] 解析 tool_input.todos 失败:', e);
                }
              }
              
              return {
                tool_use_id: tc.tool_use_id || '',
                tool_name: tc.tool_name || 'Unknown',
                tool_input: processedToolInput,
                tool_output: tc.output || null,
                conversation_turn_id: null,
              };
            });
            
            // 特别检查 TodoWrite 工具调用
            const todoWriteCalls = collectedToolCalls.filter(tc => isTodoTool(tc.tool_name));
            if (todoWriteCalls.length > 0) {
              const latestTodoWrite = todoWriteCalls[todoWriteCalls.length - 1];
              const todosData = parseTodosData(latestTodoWrite?.input?.todos || latestTodoWrite?.tool_input?.todos);
              
              // 🔧 核心简化方案：工具调用完成时，也实时更新 todos
              if (todosData && todosData.length > 0) {
                const extractedTodos = todosData.map((todo: any, idx: number) => {
                  // 🔧 修复：使用稳定的 ID 生成策略，确保同一个任务始终使用相同的 ID
                  // 优先使用 todo.id（如果后端提供了稳定的 id）
                  // 否则使用内容+level生成稳定的 id，而不是基于 tool_use_id
                  const stableId = todo.id || `todo-${todo.content || idx}-${todo.level || idx}`;
                  
                  return {
                    id: stableId,
                    content: todo.content || '',
                    status: todo.status || 'pending',
                    activeForm: todo.status === 'completed' ? undefined : todo.activeForm,
                    level: todo.level,
                    parentLevel: todo.parentLevel,
                  };
                });
                
                realtimeTodosRef.current = extractedTodos; // 标记为实时更新
                setTodos(extractedTodos);
                console.log('%c🚀 [toolCalls] 实时更新 todos（工具调用完成）', 'color: #34C759; font-weight: bold', {
                  tool_use_id: latestTodoWrite.tool_use_id?.substring(0, 20),
                  todos_count: extractedTodos.length,
                  todos_statuses: extractedTodos.map((t: any) => `${t.content?.substring(0, 15)}:${t.status}`),
                  note: '工具调用完成时实时更新'
                });
              }
              
              console.log('%c📋 [toolCalls] TodoWrite 工具调用:', 'color: #34C759; font-weight: bold', {
                todoWrite_count: todoWriteCalls.length,
                total_tool_calls: toolCallsInfo.length,
                latest_todos_count: todosData?.length || 0,
                latest_todos_statuses: todosData?.map((t: any) => t.status) || []
              });
            }
            
            // 🔧 修复：确保React检测到变化，通过创建新对象和深拷贝tool_calls
            setMessages(p => p.map(msg => {
              if (msg.id === aiMessageId) {
                // 🔧 创建新的tool_calls数组，确保React检测到变化
                // 🔧 关键修复：再次深拷贝 tool_input，确保完全独立
                const newToolCalls = toolCallsInfo.map(tc => {
                  // 🔧 深拷贝整个 tool_input，确保 todos 数组是完全新的引用
                  const toolInput = tc.tool_input && Object.keys(tc.tool_input).length > 0
                    ? JSON.parse(JSON.stringify(tc.tool_input))
                    : null;
                  
                  return {
                    ...tc,
                    tool_input: toolInput
                  };
                });
                
                console.log('%c✅ [toolCalls] 更新消息，触发重新渲染', 'color: #34C759; font-weight: bold', {
                  message_id: aiMessageId,
                  tool_calls_count: newToolCalls.length,
                  todoWrite_count: todoWriteCalls.length
                });
                
                return {
                  ...msg,
                  text: full || msg.text,
                  tool_calls: newToolCalls,
                  // 🔧 添加一个时间戳字段，确保React检测到变化
                  _updatedAt: Date.now()
                };
              }
              return msg;
            }));
          }

          if (chunk.text) {
            full += chunk.text;
            chunkCount++;
            if (chunkCount % 20 === 0) {
              console.log(`  📦 Chunk #${chunkCount} | 总长度: ${full.length} 字符`);
            }
            setCurrentResponse(full);
            
            // 实时更新 AI 消息的文本内容
            setMessages(p => p.map(msg => {
              if (msg.id === aiMessageId) {
                return {
                  ...msg,
                  text: full
                };
              }
              return msg;
            }));
          }

          // 🔧 修复：触发完成流程的条件
          // 1. isComplete=true - 正常完成标记
          // 2. isMaxTurnsError - 达到最大轮次限制
          // 3. isStreamEnd - 后端发送 type='end' 事件
          if (chunk.isComplete || isMaxTurnsError || isStreamEnd) {
            const completionReason = isStreamEnd ? '后端关闭流' :
                                   isMaxTurnsError ? '达到最大轮次限制' : '正常完成';
            console.log(`%c✅ 流式响应完成 (${completionReason})`, 'color: #34C759; font-weight: bold');

            // 如果是后端关闭流或达到最大轮次限制，显示提示信息
            if (isStreamEnd || isMaxTurnsError) {
              const reason = isStreamEnd ? '后端关闭流式连接' : '达到最大轮次限制';
              console.warn(`%c⚠️ 对话结束: ${reason}`, 'color: #FF9500; font-weight: bold', {
                num_turns: collectedResultInfo?.num_turns,
                message: isStreamEnd ? '后端已完成处理并关闭连接' : '当前对话已达到系统设置的最大轮次限制。如需继续，请创建新会话。'
              });
              // TODO: 可以添加 toast 提示用户（可选）
            }

            // 🔄 方案一：对话完成后重新从后端拉取历史，确保数据完整性
            // 这样可以确保文件链接、工具调用合并等问题都由后端处理
            if (sessionId || chunk.sessionId) {
              const finalSessionId = chunk.sessionId || sessionId;
              console.log('%c🔄 [方案一] 对话完成，重新加载历史以确保数据完整性', 'color: #007AFF; font-weight: bold', {
                session_id: finalSessionId,
                reason: '确保文件链接、工具调用合并等数据完整性',
                temp_ai_message_id: aiMessageId
              });
              
              try {
                const refreshedHistory = await getConversationHistory(finalSessionId, MESSAGES_PER_PAGE, 0);
                if (refreshedHistory && refreshedHistory.messages.length > 0) {
                  setHistoryTotal(refreshedHistory.total || null);
                  setHistoryHasMore(refreshedHistory.has_more || false);
                  setHistoryOffset(refreshedHistory.messages.length);
                  console.log('%c✅ [方案一] 重新加载历史成功:', 'color: #34C759; font-weight: bold', {
                    message_count: refreshedHistory.messages.length,
                    total: refreshedHistory.total,
                    has_more: refreshedHistory.has_more,
                    file_events_count: refreshedHistory.file_events?.length || 0,
                    temp_ai_message_id: aiMessageId,
                    backend_ai_message_ids: refreshedHistory.messages.filter((m: any) => m.sender === 'ai').map((m: any) => m.id)
                  });
                  
                  // 🔧 修复：完全覆盖实时对话的消息，彻底移除临时的
                  // 流式过程中创建的临时消息 ID 是 ai-${Date.now()}，后端返回的消息 ID 是后端生成的（如 ai-1）
                  // 直接使用后端返回的完整消息列表完全替换，不保留任何临时消息
                  console.log('%c🔧 [方案一] 完全覆盖消息列表，移除所有临时消息:', 'color: #FF9500; font-weight: bold', {
                    temp_ai_message_id: aiMessageId,
                    messages_before: messages.length,
                    backend_messages_count: refreshedHistory.messages.length,
                    backend_ai_message_ids: refreshedHistory.messages.filter((m: any) => m.sender === 'ai').map((m: any) => m.id)
                  });
                  // 直接使用后端返回的完整消息列表完全替换（后端已经包含了最新的 AI 消息）
                  setMessages(refreshedHistory.messages);
                  
                  // 🔧 修复：自动设置 selectedTurnId 为最新消息的 conversation_turn_id
                  // 这样用户无需点击"数据已经同步到工作区"按钮也能看到工具、链路等信息
                  const latestAIMessage = refreshedHistory.messages
                    .filter((msg: any) => msg.sender === 'ai')
                    .sort((a: any, b: any) => {
                      const timeA = new Date(a.timestamp).getTime();
                      const timeB = new Date(b.timestamp).getTime();
                      return timeB - timeA; // 最新的在前
                    })[0];
                  
                  if (latestAIMessage && latestAIMessage.conversation_turn_id) {
                    const latestTurnId = String(latestAIMessage.conversation_turn_id);
                    setSelectedTurnId(latestTurnId);
                    localStorage.setItem('selected_conversation_turn_id', latestTurnId);
                    console.log('%c✅ [方案一] 自动设置 selectedTurnId:', 'color: #34C759; font-weight: bold', {
                      conversation_turn_id: latestTurnId,
                      message_id: latestAIMessage.id,
                      reason: '确保工具、链路等标签页可以正确显示'
                    });
                  } else {
                    console.warn('⚠️ [方案一] 无法自动设置 selectedTurnId: 最新AI消息没有 conversation_turn_id', {
                      latest_message: latestAIMessage
                    });
                  }
                  
                  // 🔧 修复问题1：确保文件链接不丢失
                  if (refreshedHistory.file_events && refreshedHistory.file_events.length > 0) {
                    console.log('%c📁 [方案一] 重新加载文件事件，确保文件链接完整:', 'color: #5856D6; font-weight: bold', {
                      file_count: refreshedHistory.file_events.length,
                      files_with_url: refreshedHistory.file_events.filter((fe: any) => fe.file_url).length,
                      files_detail: refreshedHistory.file_events.map((fe: any) => ({
                        name: fe.file_name,
                        path: fe.file_path,
                        url: fe.file_url || '(缺失)',
                        conversation_turn_id: fe.conversation_turn_id
                      }))
                    });
                    
                    const refreshedFileInfos = refreshedHistory.file_events.map((fe: any, index: number) => {
                      // 🔧 确保所有字段都正确设置，特别是 file_url
                      const fileInfo = {
                        id: `file-refresh-${index}-${Date.now()}`,
                        name: fe.file_name || '未知文件',
                        path: fe.file_path || '',
                        url: fe.file_url || '', // 确保 file_url 被正确设置
                        size: fe.file_size || 0,
                        type: fe.file_type || '文件',
                        conversation_turn_id: fe.conversation_turn_id || '',
                        created_at: new Date(fe.created_at),
                      };
                      
                      // 如果 file_url 缺失，记录警告
                      if (!fileInfo.url && fe.file_path) {
                        console.warn('⚠️ [方案一] 文件事件缺少 file_url:', {
                          file_name: fileInfo.name,
                          file_path: fileInfo.path,
                          conversation_turn_id: fileInfo.conversation_turn_id
                        });
                      }
                      
                      return fileInfo;
                    });
                    
                    setFiles(refreshedFileInfos);
                    console.log('%c✅ [方案一] 文件列表已更新，包含完整链接信息', 'color: #34C759; font-weight: bold', {
                      total_files: refreshedFileInfos.length,
                      files_with_url: refreshedFileInfos.filter(f => f.url).length
                    });
                  } else {
                    // 如果没有文件事件，保留当前的文件列表（可能是在实时对话中收集的）
                    console.log('%c📁 [方案一] 重新加载的历史中没有文件事件，保留当前文件列表', 'color: #FF9500', {
                      current_files_count: files.length
                    });
                  }
                } else {
                  console.warn('⚠️ [方案一] 重新加载历史为空或失败', {
                    session_id: finalSessionId
                  });
                }
              } catch (error) {
                console.error('❌ [方案一] 重新加载历史失败:', error);
                // 即使重新加载失败，也不影响当前对话流程
              }
            }
            
            // 🔧 修复：重新加载历史后，直接返回，不再执行后续的 setMessages 更新
            // 这样可以避免创建重复的 AI 消息
            console.log('%c✅ [方案一] 历史已重新加载，跳过后续消息更新', 'color: #34C759; font-weight: bold');
            return; // 直接返回，不执行后续的 setMessages 更新
          }
        }
      } else {
        // 使用 Gemini 接口
        const stream = await streamGeminiResponse(
          txt,
          messages.map(m => ({ role: m.sender === Sender.User ? 'user' : 'model', parts: [{ text: m.text }] })),
          multimodalParts
        );

        console.log('%c📥 开始接收 Gemini 流式响应', 'color: #34C759; font-weight: bold');

        for await (const chunk of stream) {
          if (chunk.text) {
            full += chunk.text;
            chunkCount++;
            if (chunkCount % 20 === 0) {
              console.log(`  📦 Chunk #${chunkCount} | 总长度: ${full.length} 字符`);
            }
            setCurrentResponse(full);
          }
        }
      }

      console.log(`%c✅ 流式响应完成 | 总共 ${chunkCount} chunks | ${full.length} 字符`, 'color: #34C759; font-weight: bold');
      console.log('%c━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'color: #007AFF');

      // 转换收集到的工具调用为 ToolCallInfo 格式
      // 🔧 如果有多个 TodoWrite 调用，只保留最新的一个（按在数组中的位置，越靠后越新）
      const todoWriteCalls = collectedToolCalls.filter(tc => isTodoTool(tc.tool_name));
      const otherToolCalls = collectedToolCalls.filter(tc => tc.tool_name !== 'TodoWrite');
      
      // 只保留最新的 TodoWrite 调用（数组中的最后一个）
      const latestTodoWrite = todoWriteCalls.length > 0 ? todoWriteCalls[todoWriteCalls.length - 1] : null;
      
      // 构建最终的 toolCalls 列表
      const allToolCalls = [...otherToolCalls];
      if (latestTodoWrite) {
        allToolCalls.push(latestTodoWrite);
        if (todoWriteCalls.length > 1) {
          console.log('%c🔧 [handleSend] 过滤 TodoWrite 调用，只保留最新的:', 'color: #FF9500; font-weight: bold', {
            before_count: todoWriteCalls.length,
            after_count: 1,
            latest_tool_use_id: latestTodoWrite.tool_use_id?.substring(0, 20),
            latest_todos: latestTodoWrite.input?.todos || latestTodoWrite.tool_input?.todos
          });
        }
      }
      
      const toolCallsInfo = allToolCalls.map(tc => {
        const toolInput = tc.input || tc.tool_input || {};
        // 特别检查 TodoWrite 工具调用
        if (isTodoTool(tc.tool_name)) {
          console.log('%c📋 [handleSend] TodoWrite 工具调用详情:', 'color: #34C759; font-weight: bold', {
            tool_use_id: tc.tool_use_id,
            tool_name: tc.tool_name,
            input: tc.input,
            tool_input: tc.tool_input,
            final_tool_input: toolInput,
            has_todos: !!(toolInput && toolInput.todos),
            todos: toolInput.todos
          });
        }
        return {
          tool_use_id: tc.tool_use_id || '',
          tool_name: tc.tool_name || 'Unknown',
          tool_input: toolInput,
          tool_output: tc.output || null,
          conversation_turn_id: null, // 将在后续从历史消息中获取
        };
      });

      // 更新已存在的 AI 消息（在流式响应过程中已创建），而不是创建新消息
      setMessages(p => {
        const existingMessageIndex = p.findIndex(msg => msg.id === aiMessageId);
        if (existingMessageIndex >= 0) {
          // 更新已存在的消息
          const updated = [...p];
          updated[existingMessageIndex] = {
            ...updated[existingMessageIndex],
            text: full,
            resultInfo: collectedResultInfo,
            tool_calls: toolCallsInfo.length > 0 ? toolCallsInfo : undefined
          };
          
          // 特别检查 TodoWrite 工具调用
          const todoWriteCalls = toolCallsInfo.filter(tc => tc.tool_name === 'TodoWrite');
          if (todoWriteCalls.length > 0) {
            console.log('%c📋 [handleSend] 已更新消息的 TodoWrite 工具调用:', 'color: #34C759; font-weight: bold', {
              message_id: aiMessageId,
              todoWrite_count: todoWriteCalls.length,
              tool_calls_count: toolCallsInfo.length,
              latest_todos: todoWriteCalls[todoWriteCalls.length - 1]?.tool_input?.todos
            });
          }
          
          return updated;
        } else {
          // 如果没有找到临时消息，创建新消息（向后兼容）
          const newAIMessage = { 
            id: aiMessageId, 
        text: full, 
        sender: Sender.AI, 
        timestamp: new Date(),
            resultInfo: collectedResultInfo,
            tool_calls: toolCallsInfo.length > 0 ? toolCallsInfo : undefined
          };
          
          // 特别检查 TodoWrite 工具调用
          const todoWriteCalls = toolCallsInfo.filter(tc => tc.tool_name === 'TodoWrite');
          if (todoWriteCalls.length > 0) {
            console.log('%c📋 [handleSend] 新消息包含 TodoWrite 工具调用:', 'color: #34C759; font-weight: bold', {
              message_id: newAIMessage.id,
              todoWrite_count: todoWriteCalls.length,
              tool_calls_count: toolCallsInfo.length,
              todoWrite_calls: todoWriteCalls.map(tc => ({
                tool_use_id: tc.tool_use_id,
                tool_input: tc.tool_input,
                has_todos: !!(tc.tool_input && tc.tool_input.todos),
                todos: tc.tool_input?.todos
              })),
              message_will_have_tool_calls: !!newAIMessage.tool_calls,
              tool_calls_length: newAIMessage.tool_calls?.length
            });
          }
          
          return [...p, newAIMessage];
        }
      });

      // 同时更新 toolCalls 状态，以便 TodoList 可以立即显示
      if (toolCallsInfo.length > 0) {
        const toolCallsForState: ToolCall[] = toolCallsInfo.map(tc => ({
          tool_use_id: tc.tool_use_id,
          tool_name: tc.tool_name,
          input: tc.tool_input,
          output: tc.tool_output,
          timestamp: new Date().toLocaleTimeString('zh-CN'),
          // 🔍 判断工具状态：如果 tool_output 存在（不为 null/undefined），即使为空字符串也视为成功
          status: (tc.tool_output !== null && tc.tool_output !== undefined) ? 'success' : 'running',
          conversation_turn_id: null,
        }));
        setToolCalls(prev => [...prev, ...toolCallsForState]);
        console.log('%c✅ 工具调用已添加到消息和状态:', 'color: #34C759; font-weight: bold', {
          tool_calls_in_message: toolCallsInfo.length,
          toolCalls_in_state: toolCallsForState.length,
        });
      }

      // 处理收集到的工具调用信息
      console.log('%c📊 工具调用统计:', 'color: #007AFF; font-weight: bold', {
        总共收集: collectedToolCalls.length,
        工具发起: collectedToolCalls.filter(t => t.status === 'running').length,
        工具结果: collectedToolCalls.filter(t => t.output).length
      });

      if (collectedToolCalls.length > 0) {
        // 配对工具调用：将发起和结果配对
        const pairedToolCalls: any[] = [];
        const toolUsesMap = new Map<string, any>();

        for (const call of collectedToolCalls) {
          if (call.status === 'running') {
            // 工具发起
            toolUsesMap.set(call.tool_use_id, call);
          } else if (call.output) {
            // 工具结果
            const toolUse = toolUsesMap.get(call.tool_use_id);
            if (toolUse) {
              // 配对成功
              pairedToolCalls.push({
                tool_use_id: call.tool_use_id,
                tool_name: toolUse.tool_name,
                input: toolUse.input,
                output: call.output,
                timestamp: toolUse.timestamp,
                status: 'success',
                // 流式收集的工具调用属于当前轮次，但 conversation_turn_id 需要从消息中获取
                // 这里先不设置，等 useEffect 从消息中提取时会自动获取
                conversation_turn_id: null
              });
            } else {
              // 没有找到对应的发起
              pairedToolCalls.push({
                tool_use_id: call.tool_use_id,
                tool_name: 'Unknown',
                input: {},
                output: call.output,
                timestamp: call.timestamp,
                status: 'success',
                conversation_turn_id: null
              });
            }
          }
        }

        console.log('%c✅ 配对成功的工具调用:', 'color: #00BC8C; font-weight: bold', pairedToolCalls.length, '个');

        // ⚠️ 重要：流式收集的工具调用属于当前轮次
        // 只有当 selectedTurnId 为 null（显示当前轮次）时，才更新 toolCalls
        // 如果用户选择了其他轮次（selectedTurnId 不为 null），不覆盖，让 useEffect 来处理
        if (!selectedTurnId) {
          setToolCalls(pairedToolCalls);
          console.log('%c💾 已更新工具调用状态（当前轮次）:', 'color: #FF9500; font-weight: bold', {
            当前轮次工具数: pairedToolCalls.length
          });
        } else {
          console.log('%c⏭️ 跳过流式工具调用更新（用户选择了其他轮次）:', 'color: #FF9500; font-weight: bold', {
            selectedTurnId: selectedTurnId,
            流式工具数: pairedToolCalls.length
          });
        }
      } else {
        // 如果没有工具调用，且用户没有选择其他轮次，清空
        if (!selectedTurnId) {
          setToolCalls([]);
        }
      }
    } catch (e) {
      console.error('❌ 请求异常:', e);
      setCurrentResponse('解析异常，重连中...');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full bg-white overflow-hidden selection:bg-blue-50 font-sans">
      {/* 视频框 - 全页面可拖拽 */}
      {isCameraActive && (
        <div 
          ref={videoContainerRef}
          className="w-32 h-32 bg-black rounded-[24px] overflow-hidden shadow-2xl border-4 border-white relative ring-1 ring-black/5 select-none"
          style={{
            position: 'fixed',
            left: `${videoPosition.x}px`,
            top: `${videoPosition.y}px`,
            cursor: isDragging ? 'grabbing' : 'grab',
            transition: isDragging ? 'none' : 'all 0.2s ease-out',
            zIndex: 9999
          }}
          onMouseDown={handleVideoMouseDown}
        >
          <video 
            ref={videoRef} 
            autoPlay 
            playsInline 
            muted 
            className="w-full h-full object-cover pointer-events-none"
            style={{ transform: 'scaleX(-1)' }} // 镜像显示，更自然
          />
          <button 
            onClick={toggleCamera} 
            className="absolute top-1.5 right-1.5 bg-black/50 hover:bg-black/70 text-white p-1 rounded-full transition-colors z-10 pointer-events-auto"
            title="关闭摄像头"
            onMouseDown={(e) => e.stopPropagation()} // 防止触发拖拽
          >
            <X size={10}/>
          </button>
          {/* 拖拽提示 */}
          {!isDragging && (
            <div className="absolute bottom-1 left-1/2 transform -translate-x-1/2 bg-black/30 text-white text-[8px] px-2 py-0.5 rounded-full pointer-events-none">
              可拖动
            </div>
          )}
        </div>
      )}
      
      {/* 左侧对话 */}
      <div className={`flex flex-col border-r border-black/[0.05] transition-all duration-700 ${
        isWorkspaceOpen ? 'hidden md:flex md:w-2/5' : 'w-full'
      }`}>
        <header className="h-16 border-b border-black/[0.04] flex items-center justify-between bg-white/95 backdrop-blur-3xl px-6">
          <div className="flex items-center space-x-3">
             <div className="w-8 h-8 bg-apple-gray rounded-xl flex items-center justify-center text-white shadow-lg"><Zap size={14} fill="white" /></div>
             <div className="flex flex-col">
               <span className="text-[9px] font-black tracking-widest uppercase text-gray-400">Intelligence</span>
               <span className="text-[14px] font-black text-apple-gray tracking-tight leading-none">Console</span>
             </div>
          </div>
          {!isWorkspaceOpen && <button onClick={() => setIsWorkspaceOpen(true)} className="p-2 text-gray-300 hover:text-black hover:bg-gray-50 rounded-full transition-all"><Maximize2 size={16}/></button>}
        </header>

        <div className="flex-1 overflow-y-auto custom-scrollbar bg-[#FBFBFD] px-6 py-8 space-y-6">
          {/* 推荐问题区域 - 仅在初始状态显示 */}
          {showRecommendations && messages.length === 1 && !isLoading && (
            <div className="space-y-3 mb-8 animate-apple-fade">
              <div className="text-center mb-4">
                <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-blue-50 rounded-full border border-blue-100">
                  <SparklesIcon size={12} className="text-blue-600 animate-pulse" />
                  <span className="text-[10px] font-bold text-blue-700 uppercase tracking-widest">智能推荐</span>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-3xl mx-auto">
                {RECOMMENDED_QUESTIONS.map((item, index) => (
                  <RecommendationCard
                    key={item.id}
                    item={item}
                    index={index}
                    isDisappearing={disappearingCardId === item.id}
                    onClick={() => {
                      setDisappearingCardId(item.id);
                      setTimeout(() => {
                        setInput(item.question);
                        handleSend(item.question);
                      }, 500); // 等待消失动画完成
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          {(() => {
            console.log('[ChatInterface] Rendering messages section, count:', messages.length);
            if (messages.length === 0) {
              return (
                <div className="text-center py-12 text-[#86868B]">
                  <p className="text-sm">暂无消息</p>
                  <p className="text-xs mt-2 opacity-50">消息数组长度: {messages.length}</p>
                </div>
              );
            }
            // 🔧 修改逻辑：找到最后一个（最新的）有 TodoWrite 的 AI 消息
            // 因为用户可能会多次修正 todolist，应该显示最新的版本
            let latestAIMessageWithTodosIndex = -1;
            for (let i = messages.length - 1; i >= 0; i--) {
              const msg = messages[i];
              if (msg.sender === Sender.AI && msg.tool_calls && msg.tool_calls.length > 0) {
                if (msg.tool_calls.some(tc => isTodoTool(tc.tool_name))) {
                  latestAIMessageWithTodosIndex = i;
                  break; // 找到最后一个就退出
                }
              }
            }
            
            console.log('%c📋 [TodoList] 查找所有有 todos 的 AI 消息', 'color: #007AFF; font-weight: bold', {
              latestAIMessageWithTodosIndex: latestAIMessageWithTodosIndex,
              extractTodosFromToolCalls_length: extractTodosFromToolCalls.length,
              messages_count: messages.length,
              messages_with_tool_calls: messages.filter(m => m.tool_calls && m.tool_calls.length > 0).length,
              all_todoWrite_messages: messages
                .map((m, idx) => ({ 
                  index: idx, 
                  sender: m.sender, 
                  has_todoWrite: m.tool_calls?.some(tc => isTodoTool(tc.tool_name)) || false,
                  message_id: m.id,
                  conversation_turn_id: m.conversation_turn_id
                }))
                .filter(m => m.has_todoWrite),
              note: '现在每个有 TodoWrite 的消息都会显示对应的 TodoList，可以看到任务演进历史'
            });
            
            // 加载更多历史消息的函数
            const loadMoreHistory = async () => {
              if (loadingMoreHistory || !historyHasMore || !sessionId) return;
              
              setLoadingMoreHistory(true);
              try {
                const history = await getConversationHistory(sessionId, MESSAGES_PER_PAGE, historyOffset);
                if (history && history.messages.length > 0) {
                  // 将新消息添加到现有消息列表的前面（因为历史消息是按时间倒序的）
                  setMessages(prev => [...history.messages, ...prev]);
                  setHistoryHasMore(history.has_more || false);
                  setHistoryOffset(prev => prev + history.messages.length);
                  console.log('加载更多历史消息成功:', {
                    new_count: history.messages.length,
                    total: history.total,
                    has_more: history.has_more
                  });
                }
              } catch (error) {
                console.error('加载更多历史消息失败:', error);
              } finally {
                setLoadingMoreHistory(false);
              }
            };
            
            return (
              <>
                {/* 显示总数和加载更多按钮（在消息列表顶部） */}
                {historyTotal !== null && (
                  <div className="text-center py-4 border-b border-gray-100 mb-4">
                    <div className="text-xs text-[#86868B] mb-3">
                      共 {historyTotal} 条消息，已加载 {messages.length} 条
                    </div>
                    {historyHasMore && (
                      <button
                        onClick={loadMoreHistory}
                        disabled={loadingMoreHistory}
                        className="px-4 py-2 text-sm text-[#0066CC] hover:text-[#0052A3] disabled:text-[#86868B] disabled:cursor-not-allowed transition-colors rounded-lg border border-[#0066CC]/20 hover:border-[#0066CC]/40 hover:bg-blue-50"
                      >
                        {loadingMoreHistory ? (
                          <span className="flex items-center justify-center">
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            加载中...
                          </span>
                        ) : (
                          `加载更多历史消息 (还有 ${historyTotal - messages.length} 条)`
                        )}
                      </button>
                    )}
                  </div>
                )}
                
                {messages.map((m, index) => {
              // 🔧 渲染消息（去掉高频调试日志，避免鼠标移动时频繁触发控制台输出导致卡顿）
              return (
              <div
                key={m.id}
                className={`flex flex-col ${m.sender === Sender.User ? 'items-end' : 'items-start'} animate-apple-slide`}
              >
                  <div className="flex items-start space-x-3 max-w-[95%]">
                    {/* AI 消息使用 MarkdownRenderer 渲染，用户消息直接显示 */}
                    {m.sender === Sender.AI ? (() => {
                      const display = getMessageDisplay(m.text || '');
                  return (
                    <div className="px-4 py-3 text-[14px] leading-relaxed shadow-sm bg-white border border-black/[0.03] text-apple-gray rounded-[24px] rounded-tl-sm">
                      {display.isLong ? (
                        // 长消息（>100字符）：只显示提示，可点击
                        <button
                          onClick={() => {
                            console.log('%c🖱️ 点击长消息按钮:', 'color: #FF9500; font-weight: bold', {
                              message_id: m.id,
                              conversation_turn_id: m.conversation_turn_id,
                              conversation_turn_id_type: typeof m.conversation_turn_id,
                              has_conversation_turn_id: !!m.conversation_turn_id
                            });
                            // ⚠️ 重要：统一设置 conversation_turn_id，确保左侧和右侧工作区显示同一轮次的内容
                            if (m.conversation_turn_id) {
                              const turnId = String(m.conversation_turn_id); // 确保是字符串
                              // 同时更新状态和 localStorage
                              setSelectedTurnId(turnId);
                              localStorage.setItem('selected_conversation_turn_id', turnId);
                              // 同时设置 workspaceMessageId（向后兼容）
                            setWorkspaceMessageId(m.id);
                              
                              console.log('%c✅ 已统一设置 conversation_turn_id:', 'color: #34C759; font-weight: bold', {
                                message_id: m.id,
                                conversation_turn_id: turnId,
                                conversation_turn_id_value: turnId,
                                turn_id_type: typeof turnId,
                                message_tool_calls: m.tool_calls?.length || 0,
                                saved_to_localStorage: true,
                                workspaceMessageId: m.id,
                                note: '左侧和右侧工作区的所有标签页（realtime、tools等）都会根据此 conversation_turn_id 显示内容'
                              });
                            } else {
                              console.warn('%c⚠️ 消息没有 conversation_turn_id:', 'color: #FF9500; font-weight: bold', {
                                message_id: m.id,
                                message: m
                              });
                              // 即使没有 conversation_turn_id，也设置 workspaceMessageId（向后兼容）
                              setWorkspaceMessageId(m.id);
                            }
                            // 默认显示追踪（realtime 标签页）
                            if (!isWorkspaceOpen) {
                              setIsWorkspaceOpen(true);
                            }
                            setActiveTab('realtime');
                          }}
                          className="text-center py-2 w-full hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                        >
                          <span className="text-[11px] text-blue-600 font-semibold hover:text-blue-700">
                            数据已经同步到工作区 →
                          </span>
                        </button>
                      ) : (
                        // 短消息（≤100字符）：显示完整内容，但也可以点击设置轮次
                        <div 
                          onClick={() => {
                            console.log('%c🖱️ 点击短消息:', 'color: #FF9500; font-weight: bold', {
                              message_id: m.id,
                              conversation_turn_id: m.conversation_turn_id,
                              conversation_turn_id_type: typeof m.conversation_turn_id,
                              has_conversation_turn_id: !!m.conversation_turn_id,
                              message_tool_calls: m.tool_calls?.length || 0
                            });
                            // ⚠️ 重要：统一设置 conversation_turn_id，确保左侧和右侧工作区显示同一轮次的内容
                            if (m.conversation_turn_id) {
                              const turnId = String(m.conversation_turn_id); // 确保是字符串
                              // 同时更新状态和 localStorage
                              setSelectedTurnId(turnId);
                              localStorage.setItem('selected_conversation_turn_id', turnId);
                              // 同时设置 workspaceMessageId（向后兼容）
                              setWorkspaceMessageId(m.id);
                              
                              console.log('%c✅ 已统一设置 conversation_turn_id:', 'color: #34C759; font-weight: bold', {
                                message_id: m.id,
                                conversation_turn_id: turnId,
                                conversation_turn_id_value: turnId,
                                turn_id_type: typeof turnId,
                                saved_to_localStorage: true,
                                workspaceMessageId: m.id,
                                note: '左侧和右侧工作区的所有标签页（realtime、tools等）都会根据此 conversation_turn_id 显示内容'
                              });
                            } else {
                              console.warn('%c⚠️ 消息没有 conversation_turn_id:', 'color: #FF9500; font-weight: bold', {
                                message_id: m.id,
                                message: m
                              });
                              // 即使没有 conversation_turn_id，也设置 workspaceMessageId（向后兼容）
                              setWorkspaceMessageId(m.id);
                            }
                          }}
                          className="cursor-pointer"
                        >
                        <MarkdownRendererWithCharts content={display.chatContent} isStreaming={false} />
                        </div>
                      )}
                    </div>
                  );
                })() : (
                  // 用户消息也可以点击设置轮次
                  <div 
                    onClick={() => {
                      console.log('%c🖱️ 点击用户消息:', 'color: #FF9500; font-weight: bold', {
                        message_id: m.id,
                        conversation_turn_id: m.conversation_turn_id,
                        conversation_turn_id_type: typeof m.conversation_turn_id,
                        has_conversation_turn_id: !!m.conversation_turn_id
                      });
                      // ⚠️ 重要：统一设置 conversation_turn_id，确保左侧和右侧工作区显示同一轮次的内容
                      if (m.conversation_turn_id) {
                        const turnId = String(m.conversation_turn_id); // 确保是字符串
                        // 同时更新状态和 localStorage
                        setSelectedTurnId(turnId);
                        localStorage.setItem('selected_conversation_turn_id', turnId);
                        // 同时设置 workspaceMessageId（向后兼容）
                        setWorkspaceMessageId(m.id);
                        
                        console.log('%c✅ 已统一设置 conversation_turn_id:', 'color: #34C759; font-weight: bold', {
                          message_id: m.id,
                          conversation_turn_id: turnId,
                          conversation_turn_id_value: turnId,
                          turn_id_type: typeof turnId,
                          saved_to_localStorage: true,
                          workspaceMessageId: m.id,
                          note: '左侧和右侧工作区的所有标签页（realtime、tools等）都会根据此 conversation_turn_id 显示内容'
                        });
                      } else {
                        console.warn('%c⚠️ 消息没有 conversation_turn_id:', 'color: #FF9500; font-weight: bold', {
                          message_id: m.id,
                          message: m
                        });
                        // 即使没有 conversation_turn_id，也设置 workspaceMessageId（向后兼容）
                        setWorkspaceMessageId(m.id);
                      }
                    }}
                    className="px-4 py-3 text-[14px] font-semibold leading-relaxed shadow-sm bg-apple-blue text-white rounded-[24px] rounded-tr-sm shadow-blue-500/10 cursor-pointer hover:opacity-90 transition-opacity"
                  >
                    {typeof m.text === 'string' ? m.text : String(m.text)}
                  </div>
                )}
              </div>
              
              {/* Todo 列表显示 - 只在最新的AI消息下方显示统一的todos */}
              {(() => {
                const isAIMessage = m.sender === Sender.AI;
                const hasTodoWrite = isAIMessage && m.tool_calls && m.tool_calls.some(tc => isTodoTool(tc.tool_name));
                
                // 🔧 方案3：只在最新的AI消息下方显示统一的todos
                // 判断是否是最新的有TodoWrite的AI消息
                const isLatestAIMessageWithTodos = hasTodoWrite && index === latestAIMessageWithTodosIndex;
                
                if (isLatestAIMessageWithTodos && todos && todos.length > 0) {
                  // 🔧 使用统一的 todos（通过 extractTodosFromToolCalls 提取）
                  // 判断是否是最新的一条历史消息，如果是则自动展开
                  const isLatestHistoryMessage = m.id === latestHistoryMessageIdWithTodos;
                  const shouldAutoExpand = shouldAutoExpandTodos || isLatestHistoryMessage;
                  
                  // 🔧 使用稳定的key（只基于message_id），让React更新组件而不是重新挂载
                  const todosKey = `${m.id}`;
                  
                  // 🔧 确保每次渲染都创建新的todos数组引用，让React检测到变化
                  const todosWithNewRef = JSON.parse(JSON.stringify(todos));
                  
                  console.log('%c📋 [统一TodoList] 在最新AI消息下方渲染 TodoList', 'color: #34C759; font-weight: bold', {
                    message_id: m.id,
                    message_index: index,
                    latestAIMessageWithTodosIndex: latestAIMessageWithTodosIndex,
                    todos_count: todosWithNewRef.length,
                    todos_statuses: todosWithNewRef.map((t: any) => `${t.content?.substring(0, 15)}:${t.status}`),
                    todos_key: todosKey
                  });
                  
                  return (
                    <TodoList 
                      key={todosKey}
                      todos={todosWithNewRef}
                      defaultExpanded={false}
                      autoExpand={shouldAutoExpand}
                    />
                  );
                }
                
                return null;
              })()}
              
              {/* ResultMessage 信息显示 */}
              {m.sender === Sender.AI && m.resultInfo && (() => {
                const isExpanded = expandedStats.has(m.id);
                const toggleExpanded = () => {
                  setExpandedStats(prev => {
                    const next = new Set(prev);
                    if (next.has(m.id)) {
                      next.delete(m.id);
                    } else {
                      next.add(m.id);
                    }
                    return next;
                  });
                };
                return (
                <div className="mt-2 max-w-[95%] w-full">
                    <div className="bg-[#F5F5F7] rounded-[16px] border border-black/[0.03] overflow-hidden">
                      {/* 可点击的标题栏 */}
                      <button
                        onClick={toggleExpanded}
                        className="w-full px-3 py-2 flex items-center justify-between hover:bg-[#EBEBED] transition-colors duration-200"
                      >
                        <span className="text-[11px] text-[#1D1D1F] font-semibold">统计信息</span>
                        {isExpanded ? (
                          <ChevronUp size={14} className="text-[#86868B]" />
                        ) : (
                          <ChevronDown size={14} className="text-[#86868B]" />
                        )}
                      </button>
                      
                      {/* 折叠内容 */}
                      {isExpanded && (
                        <div className="px-3 pb-3">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
                      {m.resultInfo.subtype && (
                        <div className="flex flex-col">
                                <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">类型</span>
                          <span className="text-[#1D1D1F] font-semibold">{m.resultInfo.subtype}</span>
                        </div>
                      )}
                      {m.resultInfo.duration_ms !== undefined && (
                        <div className="flex flex-col">
                                <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">总耗时</span>
                                <span className="text-[#1D1D1F] font-semibold">{(m.resultInfo.duration_ms / 1000).toFixed(2)}秒</span>
                        </div>
                      )}
                      {m.resultInfo.duration_api_ms !== undefined && (
                        <div className="flex flex-col">
                                <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">API耗时</span>
                                <span className="text-[#1D1D1F] font-semibold">{(m.resultInfo.duration_api_ms / 1000).toFixed(2)}秒</span>
                        </div>
                      )}
                      {m.resultInfo.num_turns !== undefined && (
                        <div className="flex flex-col">
                                <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">轮次</span>
                          <span className="text-[#1D1D1F] font-semibold">{m.resultInfo.num_turns}</span>
                        </div>
                      )}
                      {m.resultInfo.total_cost_usd !== null && m.resultInfo.total_cost_usd !== undefined && (
                        <div className="flex flex-col">
                                <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">费用</span>
                          <span className="text-[#1D1D1F] font-semibold">${m.resultInfo.total_cost_usd.toFixed(6)}</span>
                        </div>
                      )}
                      {m.resultInfo.is_error !== undefined && (
                        <div className="flex flex-col">
                                <span className="text-[#86868B] font-bold uppercase tracking-wider mb-0.5">状态</span>
                          <span className={`font-semibold ${m.resultInfo.is_error ? 'text-red-600' : 'text-green-600'}`}>
                                  {m.resultInfo.is_error ? '错误' : '成功'}
                          </span>
                        </div>
                      )}
                      {m.resultInfo.usage && (
                        <div className="flex flex-col col-span-2 md:col-span-4">
                                <span className="text-[#86868B] font-bold uppercase tracking-wider mb-2">使用情况</span>
                          <div className="bg-white rounded-lg p-3 border border-black/[0.03] space-y-2">
                            {/* Token 使用情况 */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                              {m.resultInfo.usage.input_tokens !== undefined && (
                                <div className="flex flex-col">
                                        <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider mb-0.5">输入Token</span>
                                  <span className="text-[12px] text-[#1D1D1F] font-semibold">{m.resultInfo.usage.input_tokens.toLocaleString()}</span>
                                </div>
                              )}
                              {m.resultInfo.usage.output_tokens !== undefined && (
                                <div className="flex flex-col">
                                        <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider mb-0.5">输出Token</span>
                                  <span className="text-[12px] text-[#1D1D1F] font-semibold">{m.resultInfo.usage.output_tokens.toLocaleString()}</span>
                                </div>
                              )}
                              {m.resultInfo.usage.cache_read_input_tokens !== undefined && m.resultInfo.usage.cache_read_input_tokens > 0 && (
                                <div className="flex flex-col">
                                        <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider mb-0.5">缓存读取</span>
                                  <span className="text-[12px] text-[#1D1D1F] font-semibold">{m.resultInfo.usage.cache_read_input_tokens.toLocaleString()}</span>
                                </div>
                              )}
                              {m.resultInfo.usage.cache_creation_input_tokens !== undefined && m.resultInfo.usage.cache_creation_input_tokens > 0 && (
                                <div className="flex flex-col">
                                        <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider mb-0.5">缓存创建</span>
                                  <span className="text-[12px] text-[#1D1D1F] font-semibold">{m.resultInfo.usage.cache_creation_input_tokens.toLocaleString()}</span>
                                </div>
                              )}
                            </div>
                            
                            {/* 服务层级和工具使用 */}
                            <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                              {m.resultInfo.usage.service_tier && (
                                <div className="flex items-center space-x-2">
                                        <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider">层级:</span>
                                  <span className="text-[11px] text-[#1D1D1F] font-semibold bg-blue-50 px-2 py-0.5 rounded-md">{m.resultInfo.usage.service_tier}</span>
                                </div>
                              )}
                              {m.resultInfo.usage.server_tool_use && (
                                <div className="flex items-center space-x-2">
                                        <span className="text-[9px] text-[#86868B] font-bold uppercase tracking-wider">工具:</span>
                                  <span className="text-[11px] text-[#1D1D1F] font-semibold">
                                    {Object.entries(m.resultInfo.usage.server_tool_use)
                                      .filter(([_, value]) => typeof value === 'number' && value > 0)
                                      .map(([key, value]) => `${key}: ${value}`)
                                            .join(', ') || '无'}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              )}
                    </div>
                  </div>
                );
              })()}
              
              {m.sender === Sender.AI && (
                // 🔧 完全取消 hover 出现/隐藏，工具条始终显示，避免任何因显示状态切换导致的布局抖动
                <div className="flex items-center space-x-4 mt-2 px-2">
                  <button
                    onClick={() => handleRegenerate(m.id)}
                    className="text-gray-300 hover:text-blue-600 transition-colors p-1"
                    title="重新生成"
                  >
                    <RefreshCw size={13} />
                  </button>
                  <button
                    onClick={() => handleCopy(m.text, m.id)}
                    className="text-gray-300 hover:text-gray-900 transition-colors p-1"
                    title="复制"
                  >
                    {copiedId === m.id ? <Check size={13} className="text-green-500" /> : <Copy size={13} />}
                  </button>
                  <div className="w-px h-3 bg-gray-200" />
                  <MessageFeedback
                    messageId={m.id}
                    sessionId={sessionId || undefined}
                    conversationTurnId={m.conversation_turn_id || undefined}
                    userPrompt={messages.find(
                      msg => msg.sender === Sender.User && msg.id === m.parent_message_id?.toString()
                    )?.text}
                    assistantResponse={m.text}
                    onFeedbackSubmitted={(type) => {
                      console.log(`反馈已提交: ${type}`, m.id);
                    }}
                    onCorrectClick={() => {
                      setFeedbackTarget({
                        messageId: m.id,
                        sessionId: sessionId || undefined,
                        conversationTurnId: m.conversation_turn_id || undefined,
                        userPrompt: messages.find(
                          msg => msg.sender === Sender.User && msg.id === m.parent_message_id?.toString()
                        )?.text,
                        assistantResponse: m.text,
                      });
                      setFeedbackCorrectText('');
                      setIsFeedbackModalOpen(true);
                    }}
                  />
                </div>
              )}
              
              <span
                className="text-[8px] text-gray-400 font-black uppercase mt-1 px-1 tracking-[0.2em] opacity-40"
              >
                {m.sender === Sender.User ? 'Identity' : 'X AI Core'}
              </span>
            </div>
              );
            })}
              </>
            );
          })()}
          <div ref={msgEnd} />
        </div>

        {/* 全局纠正反馈弹框（简单固定蒙层，不影响下方列表布局） */}
        {isFeedbackModalOpen && (
          <>
            <div
              className="fixed inset-0 bg-black/20 z-[9998]"
              onClick={(e) => {
                // 点击蒙层不关闭，避免误触
                e.stopPropagation();
              }}
            />
            <div
              className="fixed bg-white rounded-lg shadow-xl border border-gray-200 p-4 z-[9999] min-w-[320px] max-w-[480px]"
              style={{
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
              }}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-gray-700">纠正回答</span>
                <button
                  onClick={() => {
                    setIsFeedbackModalOpen(false);
                    setFeedbackCorrectText('');
                    setFeedbackTarget(null);
                  }}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                  type="button"
                >
                  <X size={16} />
                </button>
              </div>
              <textarea
                value={feedbackCorrectText}
                onChange={(e) => setFeedbackCorrectText(e.target.value)}
                placeholder="请输入正确的回答..."
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={4}
              />
              <div className="flex justify-end space-x-2 mt-3">
                <button
                  onClick={() => {
                    setIsFeedbackModalOpen(false);
                    setFeedbackCorrectText('');
                    setFeedbackTarget(null);
                  }}
                  className="px-3 py-1.5 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
                  type="button"
                >
                  取消
                </button>
                <button
                  onClick={handleSubmitCorrectFeedback}
                  disabled={!feedbackCorrectText.trim() || isSubmittingFeedback}
                  className="px-3 py-1.5 text-sm text-white bg-blue-600 rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  type="button"
                >
                  {isSubmittingFeedback ? '提交中...' : '提交'}
                </button>
              </div>
            </div>
          </>
        )}

        {/* 输入区 */}
        <ChatInputArea
          input={input}
          setInput={setInput}
          onSend={handleSend}
          isLoading={isLoading}
          pendingFiles={pendingFiles}
          onFileChange={handleFileChange}
          onRemovePendingFile={removePendingFile}
          fileInputRef={fileInputRef}
          isCameraActive={isCameraActive}
          onToggleCamera={toggleCamera}
          isRecording={isRecording}
          recordingTime={recordingTime}
          onToggleRecording={toggleRecording}
          mentionFiles={mentionFiles}
          showMentionDropdown={showMentionDropdown}
          mentionQuery={mentionQuery}
          mentionPosition={mentionPosition}
          selectedMentionIndex={selectedMentionIndex}
          inputRef={inputRef}
          mentionDropdownRef={mentionDropdownRef}
          onMentionInputChange={(value, cursorPos, inputElement) => {
                  const textBeforeCursor = value.substring(0, cursorPos);
                  const lastAtIndex = textBeforeCursor.lastIndexOf('@');
                  
                  if (lastAtIndex !== -1) {
                    const afterAt = textBeforeCursor.substring(lastAtIndex + 1);
                    if (!afterAt.includes(' ') && !afterAt.includes('\n')) {
                      const query = afterAt.toLowerCase();
                      setMentionQuery(query);
                      
                      if (mentionFiles.length > 0) {
                        setShowMentionDropdown(true);
                        setSelectedMentionIndex(0);
                        
                  if (inputElement) {
                    const rect = inputElement.getBoundingClientRect();
                          setMentionPosition({
                            top: rect.bottom + 4,
                            left: rect.left
                          });
                        }
                      } else {
                        setShowMentionDropdown(false);
                }
                      return;
                    }
                  }
                  setShowMentionDropdown(false);
                }}
          onMentionKeyDown={(e, inputVal, setInputFn, onEnter) => {
                  if (showMentionDropdown && mentionFiles.length > 0) {
                    if (e.key === 'ArrowDown') {
                      e.preventDefault();
                setSelectedMentionIndex(prev => prev < mentionFiles.length - 1 ? prev + 1 : prev);
                return true;
                    } else if (e.key === 'ArrowUp') {
                      e.preventDefault();
                      setSelectedMentionIndex(prev => prev > 0 ? prev - 1 : 0);
                return true;
                    } else if (e.key === 'Enter' || e.key === 'Tab') {
                      e.preventDefault();
                      const selectedFile = mentionFiles[selectedMentionIndex];
                if (selectedFile && inputRef.current) {
                  const cursorPos = inputRef.current.selectionStart || 0;
                  const textBeforeCursor = inputVal.substring(0, cursorPos);
                        const lastAtIndex = textBeforeCursor.lastIndexOf('@');
                  const textAfterCursor = inputVal.substring(cursorPos);
                  
                  const newText = inputVal.substring(0, lastAtIndex) + `@${selectedFile.file_name}` + textAfterCursor;
                  setInputFn(newText);
                        setShowMentionDropdown(false);
                        
                        setTimeout(() => {
                          if (inputRef.current) {
                            const newPos = lastAtIndex + selectedFile.file_name.length + 1;
                            inputRef.current.setSelectionRange(newPos, newPos);
                          }
                        }, 0);
                      }
                return true;
                    } else if (e.key === 'Escape') {
                      e.preventDefault();
                      setShowMentionDropdown(false);
                return true;
              }
            }
            // ⚠️ 重要：不要在这里调用 onEnter，让 ChatInputArea 的 onKeyDown 来处理
            // 这样可以避免重复调用 onSend
            return false;
          }}
          onSelectMentionFile={(file, inputVal, setInputFn) => {
            if (!inputRef.current) return;
            
            const cursorPos = inputRef.current.selectionStart || 0;
            const textBeforeCursor = inputVal.substring(0, cursorPos);
                          const lastAtIndex = textBeforeCursor.lastIndexOf('@');
            const textAfterCursor = inputVal.substring(cursorPos);
            
            const newText = inputVal.substring(0, lastAtIndex) + `@${file.file_name}` + textAfterCursor;
            setInputFn(newText);
                          setShowMentionDropdown(false);
                          
                          setTimeout(() => {
                            if (inputRef.current) {
                              const newPos = lastAtIndex + file.file_name.length + 1;
                              inputRef.current.setSelectionRange(newPos, newPos);
                              inputRef.current.focus();
                            }
                          }, 0);
                        }}
        />
      </div>

      {/* 右侧工作区 - 已优化为宽屏仪表盘布局 */}
      {isWorkspaceOpen && (
        <WorkspacePanel
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          setIsWorkspaceOpen={setIsWorkspaceOpen}
          messages={messages}
          files={files}
          toolCalls={toolCalls}
          selectedTurnId={selectedTurnId}
          selectedToolCall={selectedToolCall}
          setSelectedToolCall={setSelectedToolCall}
          previewFile={previewFile}
          setPreviewFile={setPreviewFile}
          isLoading={isLoading}
          currentResponse={currentResponse}
          workspaceMessageId={workspaceMessageId}
          getMessageDisplay={getMessageDisplay}
          wsEnd={msgEnd}
          sessionId={sessionId}
        />
      )}
    </div>
  );
};
