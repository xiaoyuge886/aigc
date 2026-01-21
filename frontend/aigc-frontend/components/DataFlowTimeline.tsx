import React, { useState, useEffect } from 'react';
import { 
  MessageSquare, 
  Bot, 
  Wrench, 
  CheckCircle, 
  FileText, 
  Clock,
  ChevronRight,
  Info
} from 'lucide-react';

// 数据链路节点类型
export interface DataFlowNode {
  node_id: string;
  node_type: 'user_message' | 'assistant_message' | 'tool_use' | 'tool_result' | 'file_event';
  node_name: string;
  timestamp: string;
  content_preview?: string | null;
  extra_data?: {
    tool_use_id?: string;
    tool_name?: string;
    tool_input?: any;
    file_path?: string;
    file_url?: string;
    file_name?: string;
  } | null;
  parent_node_id?: string | null;
  children_node_ids: string[];
}

export interface DataFlowResponse {
  conversation_turn_id: string;
  session_id: string;
  nodes: DataFlowNode[];
  root_node_id?: string | null;
}

interface DataFlowTimelineProps {
  conversationTurnId: string;
  onClose?: () => void;
}

// 节点类型配置 - Apple风格
const NODE_TYPE_CONFIG = {
  user_message: {
    icon: MessageSquare,
    gradient: 'from-blue-500 to-blue-600',
    bgColor: 'bg-blue-50/50',
    textColor: 'text-blue-600',
    label: '用户消息',
    borderColor: 'border-blue-100'
  },
  assistant_message: {
    icon: Bot,
    gradient: 'from-purple-500 to-purple-600',
    bgColor: 'bg-purple-50/50',
    textColor: 'text-purple-600',
    label: 'AI响应',
    borderColor: 'border-purple-100'
  },
  tool_use: {
    icon: Wrench,
    gradient: 'from-orange-500 to-orange-600',
    bgColor: 'bg-orange-50/50',
    textColor: 'text-orange-600',
    label: '工具调用',
    borderColor: 'border-orange-100'
  },
  tool_result: {
    icon: CheckCircle,
    gradient: 'from-green-500 to-green-600',
    bgColor: 'bg-green-50/50',
    textColor: 'text-green-600',
    label: '工具结果',
    borderColor: 'border-green-100'
  },
  file_event: {
    icon: FileText,
    gradient: 'from-indigo-500 to-indigo-600',
    bgColor: 'bg-indigo-50/50',
    textColor: 'text-indigo-600',
    label: '文件事件',
    borderColor: 'border-indigo-100'
  }
};

export const DataFlowTimeline: React.FC<DataFlowTimelineProps> = ({
  conversationTurnId,
  onClose
}) => {
  const [dataFlow, setDataFlow] = useState<DataFlowResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchDataFlow = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const { getConversationDataFlow } = await import('../services/agentService');
        const data = await getConversationDataFlow(conversationTurnId);
        
        if (!data) {
          throw new Error('获取数据链路失败');
        }

        setDataFlow(data);
        
        // 默认展开所有节点
        setExpandedNodes(new Set(data.nodes.map((n: DataFlowNode) => n.node_id)));
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取数据链路失败');
        console.error('Error fetching dataflow:', err);
      } finally {
        setLoading(false);
      }
    };

    if (conversationTurnId) {
      fetchDataFlow();
    }
  }, [conversationTurnId]);

  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: false
    });
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // 格式化耗时（相对于第一个节点的时间差）
  const formatDuration = (timestamp: string, baseTimestamp: string) => {
    const time = new Date(timestamp).getTime();
    const baseTime = new Date(baseTimestamp).getTime();
    const diffMs = time - baseTime;
    
    if (diffMs < 0) return '0ms';
    if (diffMs < 1000) return `${diffMs}ms`;
    
    const seconds = Math.floor(diffMs / 1000);
    if (seconds < 60) return `${seconds}秒`;
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes < 60) {
      return remainingSeconds > 0 ? `${minutes}分${remainingSeconds}秒` : `${minutes}分钟`;
    }
    
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours}小时${remainingMinutes}分钟` : `${hours}小时`;
  };

  // 构建节点树（按时间排序，展示父子关系）
  const sortedNodes = dataFlow?.nodes.sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  ) || [];

  // 获取第一个节点的时间戳作为基准（用于计算耗时）
  const baseTimestamp = sortedNodes.length > 0 ? sortedNodes[0].timestamp : '';

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-6">
          <div className="w-10 h-10 border-[3px] border-gray-200 border-t-gray-900 rounded-full animate-spin" 
               style={{ animationDuration: '0.8s' }} />
          <p className="text-[15px] text-[#86868B] font-medium tracking-tight">加载数据链路中</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 bg-white rounded-2xl border border-gray-200 shadow-sm">
        <div className="flex items-center space-x-3 text-[#1D1D1F]">
          <Info size={20} className="text-red-500" />
          <p className="text-[17px] font-semibold tracking-tight">加载失败</p>
        </div>
        <p className="mt-3 text-[15px] text-[#86868B] leading-relaxed">{error}</p>
      </div>
    );
  }

  if (!dataFlow || sortedNodes.length === 0) {
    return (
      <div className="p-12 bg-white rounded-2xl border border-gray-200 text-center">
        <p className="text-[15px] text-[#86868B] font-medium tracking-tight">暂无数据链路信息</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-5xl mx-auto px-6 py-8">
      {/* 标题 - Apple风格 */}
      <div className="mb-12 flex items-start justify-between">
        <div>
          <h1 className="text-[28px] font-semibold text-[#1D1D1F] tracking-tight leading-tight mb-1.5">
            数据链路
          </h1>
          <p className="text-[13px] text-[#86868B] font-medium tracking-tight">
            对话轮次 <span className="font-mono text-[12px] text-[#1D1D1F]">{conversationTurnId}</span>
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 text-[#86868B] hover:text-[#1D1D1F] hover:bg-gray-100/50 rounded-full transition-all duration-200"
            aria-label="关闭"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </button>
        )}
      </div>

      {/* 时间线 - Apple风格 */}
      <div className="relative">
        {/* 时间轴线 - 更精致的线条 */}
        <div className="absolute left-[28px] top-0 bottom-0 w-[1px] bg-gradient-to-b from-gray-200 via-gray-200 to-transparent" />

        {/* 节点列表 */}
        <div className="space-y-8">
          {sortedNodes.map((node, index) => {
            const config = NODE_TYPE_CONFIG[node.node_type];
            const Icon = config.icon;
            const isExpanded = expandedNodes.has(node.node_id);
            const hasChildren = node.children_node_ids.length > 0;
            const date = formatDate(node.timestamp);
            const time = formatTime(node.timestamp);
            const duration = baseTimestamp ? formatDuration(node.timestamp, baseTimestamp) : '';
            const prevDate = index > 0 ? formatDate(sortedNodes[index - 1].timestamp) : null;
            const showDateSeparator = prevDate !== date;

            return (
              <div key={node.node_id} className="relative">
                {/* 日期分隔符 - Apple风格 */}
                {showDateSeparator && (
                  <div className="flex items-center my-12">
                    <div className="flex-1 h-[1px] bg-gradient-to-r from-transparent via-gray-200 to-gray-200" />
                    <span className="px-6 text-[13px] font-medium text-[#86868B] tracking-tight bg-white">
                      {date}
                    </span>
                    <div className="flex-1 h-[1px] bg-gradient-to-l from-transparent via-gray-200 to-gray-200" />
                  </div>
                )}

                {/* 节点卡片 - Apple风格 */}
                <div className="relative flex items-start space-x-5 group">
                  {/* 时间轴节点 - 重新设计的简洁风格 */}
                  <div className="relative z-10 flex-shrink-0">
                    {/* 图标容器 - 简洁的方形设计 */}
                    <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${config.gradient} flex items-center justify-center shadow-[0_2px_8px_rgba(0,0,0,0.06)] group-hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] transition-all duration-300 group-hover:scale-[1.05] border border-white/20`}>
                      <Icon className="w-5 h-5 text-white" strokeWidth={2.5} />
                    </div>
                    {/* 连接线（如果有子节点） */}
                    {hasChildren && (
                      <div className="absolute left-1/2 top-10 w-[1px] bg-gray-200 transform -translate-x-1/2" style={{ height: '24px' }} />
                    )}
                  </div>

                  {/* 节点内容 - Apple风格卡片 */}
                  <div className="flex-1 min-w-0">
                    <div className={`bg-white rounded-2xl border border-gray-200/80 shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-[0_8px_24px_rgba(0,0,0,0.08)] transition-all duration-300 p-6 backdrop-blur-sm`}>
                      {/* 节点头部 - Apple风格排版 */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2.5 mb-2">
                            <span className={`px-2.5 py-1 rounded-full text-[11px] font-semibold ${config.bgColor} ${config.textColor} tracking-tight`}>
                              {config.label}
                            </span>
                          </div>
                          <h3 className="text-[17px] font-semibold text-[#1D1D1F] tracking-tight mb-2 leading-tight">
                            {node.node_name}
                          </h3>
                          <div className="flex items-center space-x-4 text-[12px] text-[#86868B] font-medium">
                            <div className="flex items-center space-x-1.5">
                              <Clock size={12} className="opacity-60" />
                              <span className="tracking-tight">{time}</span>
                            </div>
                            {duration && (
                              <div className="flex items-center space-x-1.5">
                                <span className="opacity-60">·</span>
                                <span className="tracking-tight">+{duration}</span>
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {/* 展开/收起按钮 - Apple风格 */}
                        {hasChildren && (
                          <button
                            onClick={() => toggleNode(node.node_id)}
                            className="p-2 text-[#86868B] hover:text-[#1D1D1F] hover:bg-gray-100/50 rounded-full transition-all duration-200"
                            aria-label={isExpanded ? "收起" : "展开"}
                          >
                            <ChevronRight 
                              size={18} 
                              className={`transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}
                            />
                          </button>
                        )}
                      </div>

                      {/* 节点内容预览 - Apple风格 */}
                      {node.content_preview && (
                        <div className="mt-5 p-4 bg-[#F5F5F7] rounded-xl border border-gray-100">
                          <p className="text-[13px] text-[#1D1D1F] leading-relaxed line-clamp-3 tracking-tight">
                            {node.content_preview}
                          </p>
                        </div>
                      )}

                      {/* 额外信息 - Apple风格 */}
                      {node.extra_data && (
                        <div className="mt-5 space-y-3">
                          {/* 工具输入 */}
                          {node.extra_data.tool_input && (
                            <div className="p-4 bg-orange-50/50 rounded-xl border border-orange-100/80">
                              <p className="text-[12px] font-semibold text-orange-600 mb-2 tracking-tight">工具输入</p>
                              <pre className="text-[12px] text-[#1D1D1F] overflow-x-auto font-mono leading-relaxed">
                                {JSON.stringify(node.extra_data.tool_input, null, 2)}
                              </pre>
                            </div>
                          )}
                          
                          {/* 文件信息 */}
                          {node.extra_data.file_name && (
                            <div className="p-4 bg-indigo-50/50 rounded-xl border border-indigo-100/80">
                              <p className="text-[13px] font-semibold text-indigo-600 mb-2 tracking-tight">
                                {node.extra_data.file_name}
                              </p>
                              {node.extra_data.file_url && (
                                <a 
                                  href={node.extra_data.file_url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-[13px] text-indigo-600 hover:text-indigo-700 font-medium tracking-tight inline-flex items-center space-x-1 transition-colors"
                                >
                                  <span>查看文件</span>
                                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M4 2L9 7M9 7H6M9 7V4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                                  </svg>
                                </a>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* 子节点（展开时显示） - Apple风格 */}
                      {hasChildren && isExpanded && (
                        <div className="mt-6 ml-5 pl-5 border-l-[1.5px] border-gray-200 space-y-3">
                          {node.children_node_ids.map(childId => {
                            const childNode = sortedNodes.find(n => n.node_id === childId);
                            if (!childNode) return null;
                            
                            const childConfig = NODE_TYPE_CONFIG[childNode.node_type];
                            const ChildIcon = childConfig.icon;
                            
                            return (
                              <div 
                                key={childId}
                                className={`p-3 rounded-xl border ${childConfig.borderColor} ${childConfig.bgColor} backdrop-blur-sm`}
                              >
                                <div className="flex items-center space-x-2.5 mb-1.5">
                                  <div className={`w-5 h-5 rounded-full bg-gradient-to-br ${childConfig.gradient} flex items-center justify-center`}>
                                    <ChildIcon size={12} className="text-white" strokeWidth={2} />
                                  </div>
                                  <span className={`text-[13px] font-semibold ${childConfig.textColor} tracking-tight`}>
                                    {childNode.node_name}
                                  </span>
                                  <span className="text-[11px] text-[#86868B] font-medium">
                                    {formatTime(childNode.timestamp)}
                                  </span>
                                </div>
                                {childNode.content_preview && (
                                  <p className="text-[12px] text-[#1D1D1F] leading-relaxed line-clamp-2 tracking-tight">
                                    {childNode.content_preview}
                                  </p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 图例 - Apple风格 */}
      <div className="mt-12 pt-10 border-t border-gray-200">
        <p className="text-[15px] font-semibold text-[#1D1D1F] mb-5 tracking-tight">图例</p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-5">
          {Object.entries(NODE_TYPE_CONFIG).map(([type, config]) => {
            const Icon = config.icon;
            return (
              <div key={type} className="flex items-center space-x-2.5 group cursor-default">
                <div className={`w-8 h-8 rounded-full bg-gradient-to-br ${config.gradient} flex items-center justify-center shadow-sm group-hover:shadow-md transition-all duration-200`}>
                  <Icon className="w-4 h-4 text-white" strokeWidth={2} />
                </div>
                <span className="text-[13px] text-[#1D1D1F] font-medium tracking-tight">{config.label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
