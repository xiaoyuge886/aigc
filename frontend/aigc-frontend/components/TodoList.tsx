/**
 * TodoList 组件
 * 
 * 显示 Claude Agent SDK 的 TodoWrite 工具调用产生的待办事项列表
 * 
 * 特性：
 * - 实时显示任务进度
 * - 支持折叠/展开
 * - 清晰的状态指示（待处理/进行中/已完成）
 * - 显示进度统计
 * 
 * @module components/TodoList
 */

import React, { useState, useRef } from 'react';
import { ChevronDown, ChevronUp, CheckCircle2, Loader2, Clock } from 'lucide-react';

/**
 * Todo 项的数据结构
 */
export interface TodoItem {
  id: string;
  content: string;
  status: 'pending' | 'in_progress' | 'completed';
  activeForm?: string; // 当 status 为 'in_progress' 时，显示当前活动表单
  level?: string; // 任务层级，例如 "1", "1.1", "1.2.1"
  parentLevel?: string; // 父任务层级，例如 "1", "1.2"
  completed_subtasks?: number; // 已完成的子任务数量
  total_subtasks?: number; // 总子任务数量
}

/**
 * TodoList 组件的 Props
 */
export interface TodoListProps {
  /** Todo 项列表 */
  todos: TodoItem[];
  /** 是否默认展开 */
  defaultExpanded?: boolean;
  /** 是否自动展开（当有新任务时） */
  autoExpand?: boolean;
  /** 自定义类名 */
  className?: string;
}

/**
 * TodoList 组件
 * 
 * 显示待办事项列表，支持折叠/展开，实时显示任务状态和进度
 */
export const TodoList: React.FC<TodoListProps> = ({
  todos,
  defaultExpanded = false,
  autoExpand = false,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded || autoExpand);
  const hasAutoExpandedRef = useRef(false); // 🔧 跟踪是否已经自动展开过
  const prevTodosRef = useRef<TodoItem[]>([]);
  
  // 🔧 监听todos变化，确保实时更新
  React.useEffect(() => {
    // 🔧 每次 useEffect 执行时都记录，用于调试
    console.log('%c🔍 [TodoList] useEffect 触发', 'color: #FF9500; font-weight: bold', {
      todos_length: todos.length,
      prev_todos_length: prevTodosRef.current.length,
      todos_received: todos.map(t => `${t.id}:${t.status}`).join(', ')
    });
    
    // 检查todos是否有变化（比较状态和内容）
    const prevStatuses = prevTodosRef.current.length > 0 
      ? prevTodosRef.current.map(t => `${t.id}:${t.status}`).join(',')
      : '';
    const newStatuses = todos.map(t => `${t.id}:${t.status}`).join(',');
    const todosChanged = prevStatuses !== newStatuses;
    
    console.log('%c🔍 [TodoList] 比较状态变化', 'color: #FF9500; font-weight: bold', {
      prevStatuses: prevStatuses || '(空)',
      newStatuses: newStatuses,
      todosChanged: todosChanged
    });
    
    if (todosChanged || prevTodosRef.current.length === 0) {
      const prevCompleted = prevTodosRef.current.filter(t => t.status === 'completed').length;
      const newCompleted = todos.filter(t => t.status === 'completed').length;
      const prevInProgress = prevTodosRef.current.filter(t => t.status === 'in_progress').length;
      const newInProgress = todos.filter(t => t.status === 'in_progress').length;
      
      console.log('%c🔄 [TodoList] Todos已更新，触发重新渲染', 'color: #007AFF; font-weight: bold', {
        prev_count: prevTodosRef.current.length,
        new_count: todos.length,
        prev_statuses: prevTodosRef.current.map(t => t.status),
        new_statuses: todos.map(t => t.status),
        prev_completed: prevCompleted,
        new_completed: newCompleted,
        prev_in_progress: prevInProgress,
        new_in_progress: newInProgress,
        status_changed: prevCompleted !== newCompleted || prevInProgress !== newInProgress
      });
      
      // 🔧 更新引用，使用深拷贝确保React检测到变化
      prevTodosRef.current = todos.map(t => ({ ...t }));
    } else {
      console.log('%c⏭️ [TodoList] Todos未变化，跳过更新', 'color: #86868B; font-weight: bold');
    }
  }, [todos]);
  
  // 🔧 当 autoExpand 为 true 时，自动展开（只执行一次，允许用户手动折叠）
  React.useEffect(() => {
    if (autoExpand && !hasAutoExpandedRef.current) {
      setIsExpanded(true);
      hasAutoExpandedRef.current = true;
    }
  }, [autoExpand]);
  
  // 🔧 当 autoExpand 变为 false 时，重置标志（允许下次再次自动展开）
  React.useEffect(() => {
    if (!autoExpand) {
      hasAutoExpandedRef.current = false;
    }
  }, [autoExpand]);

  // 如果没有待办事项，不显示
  if (!todos || todos.length === 0) {
    return null;
  }

  // 计算统计信息
  const stats = {
    total: todos.length,
    completed: todos.filter(t => t.status === 'completed').length,
    inProgress: todos.filter(t => t.status === 'in_progress').length,
    pending: todos.filter(t => t.status === 'pending').length,
  };

  // 计算层级的缩进级别（根据 level 中的点号数量）
  const getIndentLevel = (level?: string): number => {
    if (!level) return 0;
    const parts = level.split('.');
    return Math.max(0, parts.length - 1);
  };

  // 动态计算父任务的子任务进度
  const calculateSubtasksProgress = (currentTodo: TodoItem): { completed: number; total: number } | null => {
    if (!currentTodo.level) return null;

    // 找到所有以当前 level 为前缀的子任务
    const subtasks = todos.filter(todo => {
      if (!todo.level) return false;
      // 检查是否是直接子任务（如 "1" 的子任务是 "1.1", "1.2"）
      return todo.level.startsWith(`${currentTodo.level}.`) &&
             !todo.level.substring(currentTodo.level.length + 1).includes('.');
    });

    if (subtasks.length === 0) return null;

    const completed = subtasks.filter(t => t.status === 'completed').length;
    return {
      completed,
      total: subtasks.length
    };
  };

  // 检查 content 是否已经包含层级编号
  const hasLevelPrefix = (content: string, level?: string): boolean => {
    if (!level) return false;
    // 检查 content 是否以 "数字." 或 "数字 " 开头
    const trimmed = content.trim();
    const levelPattern = new RegExp(`^${level.replace('.', '\\.')}(?:\\.|\\s)`);
    return levelPattern.test(trimmed);
  };

  // 获取状态图标和样式
  const getStatusIcon = (status: TodoItem['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 size={14} className="text-green-600" />;
      case 'in_progress':
        return <Loader2 size={14} className="text-blue-600 animate-spin" />;
      case 'pending':
        return <Clock size={14} className="text-gray-500" />;
      default:
        return <Clock size={14} className="text-gray-500" />;
    }
  };

  const getStatusText = (status: TodoItem['status']) => {
    switch (status) {
      case 'completed':
        return '已完成';
      case 'in_progress':
        return '进行中';
      case 'pending':
        return '待处理';
      default:
        return '未知';
    }
  };

  const getStatusColor = (status: TodoItem['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'in_progress':
        return 'text-blue-600';
      case 'pending':
        return 'text-gray-500';
      default:
        return 'text-gray-500';
    }
  };

  // 计算进度百分比
  const progressPercentage = stats.total > 0 
    ? Math.round((stats.completed / stats.total) * 100) 
    : 0;

  return (
    <div className={`mt-2 max-w-[95%] w-full ${className}`}>
      <div className="bg-[#F5F5F7] rounded-[16px] border border-black/[0.03] overflow-hidden">
        {/* 可点击的标题栏 */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-3 py-2 flex items-center justify-between hover:bg-[#EBEBED] transition-colors duration-200"
          aria-label={isExpanded ? '折叠任务列表' : '展开任务列表'}
        >
          <div className="flex items-center space-x-2">
            <span className="text-[11px] text-[#1D1D1F] font-semibold">📋 任务进度</span>
            <span className="text-[10px] text-[#86868B] font-medium">
              ({stats.completed}/{stats.total} 已完成)
            </span>
            {stats.inProgress > 0 && (
              <span className="text-[10px] text-blue-600 font-medium">
                · {stats.inProgress} 进行中
              </span>
            )}
          </div>
          {isExpanded ? (
            <ChevronUp size={14} className="text-[#86868B]" />
          ) : (
            <ChevronDown size={14} className="text-[#86868B]" />
          )}
        </button>

        {/* 折叠内容 */}
        {isExpanded && (
          <div className="px-3 pb-3 space-y-2">
            {/* 进度条 */}
            <div className="pt-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-[#86868B] font-medium">总体进度</span>
                <span className="text-[10px] text-[#1D1D1F] font-semibold">{progressPercentage}%</span>
              </div>
              <div className="w-full bg-white rounded-full h-1.5 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-300"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
            </div>

            {/* 任务列表 */}
            <div className="space-y-1.5 pt-1">
              {todos.map((todo, index) => {
                const indentLevel = getIndentLevel(todo.level);
                const indentClass = indentLevel > 0 ? `ml-${Math.min(indentLevel * 3, 12)}` : '';

                // 动态计算子任务进度（优先使用动态计算的，如果没有子任务则使用后端返回的）
                const subtasksProgress = calculateSubtasksProgress(todo);
                const completedSubtasks = subtasksProgress?.completed ?? todo.completed_subtasks;
                const totalSubtasks = subtasksProgress?.total ?? todo.total_subtasks;

                return (
                  <div
                    key={todo.id || index}
                    className={`bg-white rounded-lg p-2.5 border border-black/[0.03] hover:border-blue-200 transition-colors ${indentClass}`}
                    style={indentLevel > 0 ? { marginLeft: `${indentLevel * 12}px` } : {}}
                  >
                    <div className="flex items-start space-x-2">
                      {/* 状态图标 */}
                      <div className="flex-shrink-0 mt-0.5">
                        {getStatusIcon(todo.status)}
                      </div>

                      {/* 任务内容 */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2 flex-1 min-w-0">
                            <span className="text-[11px] text-[#1D1D1F] font-medium">
                              {hasLevelPrefix(todo.content, todo.level) ? (
                                // content 已经包含层级编号，直接显示
                                todo.content
                              ) : (
                                // content 不包含层级编号，需要显示 level
                                <>{todo.level || `${index + 1}`}. {todo.content}</>
                              )}
                            </span>
                            <span className={`text-[9px] font-medium px-1.5 py-0.5 rounded ${getStatusColor(todo.status)} bg-opacity-10`}>
                              {getStatusText(todo.status)}
                            </span>
                            {/* 子任务进度 */}
                            {totalSubtasks !== undefined && totalSubtasks > 0 && (
                              <span className="text-[9px] text-[#86868B] font-medium">
                                ({completedSubtasks || 0}/{totalSubtasks})
                              </span>
                            )}
                          </div>
                        </div>

                        {/* 进行中的活动表单 */}
                        {todo.status === 'in_progress' && todo.activeForm && (
                          <div className="mt-1.5 text-[10px] text-blue-600 italic">
                            {todo.activeForm}
                          </div>
                        )}

                        {/* 父任务的子任务进度条 */}
                        {totalSubtasks !== undefined && totalSubtasks > 0 && (
                          <div className="mt-1.5">
                            <div className="w-full bg-gray-100 rounded-full h-1 overflow-hidden">
                              <div
                                className={`h-full transition-all duration-300 ${
                                  todo.status === 'completed' ? 'bg-green-500' :
                                  todo.status === 'in_progress' ? 'bg-blue-500' :
                                  'bg-gray-300'
                                }`}
                                style={{ width: `${((completedSubtasks || 0) / totalSubtasks) * 100}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
