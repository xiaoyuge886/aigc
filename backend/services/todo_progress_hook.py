"""
Todo 进度自动跟踪 Hook

使用 Claude Agent SDK 的 Hook 机制，自动跟踪任务进度并更新 enhanced_todo_write 状态。

工作原理：
1. 使用 PostToolUse hook 监听所有工具的执行
2. 当检测到工具执行完成时，通过 systemMessage 提示 Claude 更新对应的任务状态
3. 确保任务进度实时更新，不依赖模型的自觉性
"""
import logging
from typing import Any, Dict, Optional
from claude_agent_sdk import HookMatcher, HookContext

logger = logging.getLogger(__name__)


class TodoProgressTracker:
    """任务进度跟踪器"""
    
    def __init__(self):
        # 维护任务映射：工具名称 -> 任务ID列表
        # 例如：{"WebSearch": ["1.1"], "Write": ["2.1", "2.2"]}
        self.tool_to_tasks: Dict[str, list] = {}
        # 维护任务状态：任务ID -> 状态
        self.task_status: Dict[str, str] = {}
        # 当前会话的任务列表（从 enhanced_todo_write 调用中提取）
        self.current_todos: list = []
    
    def register_tool_task_mapping(self, tool_name: str, task_ids: list):
        """注册工具与任务的映射关系"""
        if tool_name not in self.tool_to_tasks:
            self.tool_to_tasks[tool_name] = []
        self.tool_to_tasks[tool_name].extend(task_ids)
        logger.info(f"[TodoProgressTracker] 注册工具-任务映射: {tool_name} -> {task_ids}")
    
    def update_task_status(self, task_id: str, status: str):
        """更新任务状态"""
        self.task_status[task_id] = status
        logger.info(f"[TodoProgressTracker] 更新任务状态: {task_id} -> {status}")
    
    def set_current_todos(self, todos: list):
        """设置当前会话的任务列表"""
        self.current_todos = todos
        logger.info(f"[TodoProgressTracker] 设置当前任务列表: {len(todos)} 个任务")
    
    def get_pending_tasks_for_tool(self, tool_name: str) -> list:
        """获取指定工具对应的待处理任务"""
        task_ids = self.tool_to_tasks.get(tool_name, [])
        pending = []
        for task_id in task_ids:
            status = self.task_status.get(task_id, "pending")
            if status == "pending":
                pending.append(task_id)
        return pending
    
    def get_in_progress_tasks_for_tool(self, tool_name: str) -> list:
        """获取指定工具对应的进行中任务"""
        task_ids = self.tool_to_tasks.get(tool_name, [])
        in_progress = []
        for task_id in task_ids:
            status = self.task_status.get(task_id, "pending")
            if status == "in_progress":
                in_progress.append(task_id)
        return in_progress
    
    def reset(self):
        """重置跟踪器（新会话开始时调用）"""
        self.tool_to_tasks.clear()
        self.task_status.clear()
        self.current_todos.clear()
        logger.info("[TodoProgressTracker] 重置跟踪器")


# 全局跟踪器实例
_tracker = TodoProgressTracker()


async def post_tool_use_hook(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """
    PostToolUse Hook：工具执行完成后触发
    
    功能：
    1. 检测工具执行是否成功
    2. 如果成功，通过智能匹配找到对应的任务，提示 Claude 更新状态为 completed
    3. 如果失败，提示 Claude 保持任务状态不变
    """
    tool_name = input_data.get('tool_name', '')
    tool_output = input_data.get('tool_output', {})
    is_error = tool_output.get('is_error', False) if isinstance(tool_output, dict) else False
    
    # 跳过 enhanced_todo_write 本身，避免循环
    if tool_name in ['enhanced_todo_write', 'mcp__custom_tools__enhanced_todo_write']:
        # 如果这是 enhanced_todo_write 调用，提取任务列表并更新跟踪器
        tool_input = input_data.get('tool_input', {})
        todos = tool_input.get('todos', [])
        if todos:
            _tracker.set_current_todos(todos)
            # 提取任务ID和状态，并尝试推断工具映射
            for todo in todos:
                if isinstance(todo, dict):
                    content = todo.get('content', '')
                    status = todo.get('status', 'pending')
                    # 提取任务ID（可能是层级格式如 "1.1" 或普通ID）
                    task_id = todo.get('id')
                    if not task_id and content:
                        # 尝试从内容中提取层级ID（如 "1.1 搜索信息"）
                        import re
                        match = re.match(r'^(\d+(?:\.\d+)*)', content.strip())
                        if match:
                            task_id = match.group(1)
                    
                    if task_id:
                        _tracker.update_task_status(task_id, status)
                        
                        # 智能推断工具映射：从任务内容中提取工具名称
                        content_lower = content.lower()
                        tool_keywords = {
                            'websearch': ['搜索', '查询', '查找', 'search', 'web'],
                            'write': ['写入', '创建', '生成', 'write', 'create'],
                            'read': ['读取', '读取', 'read'],
                            'bash': ['执行', '运行', '命令', 'bash', 'command'],
                        }
                        
                        for tool_key, keywords in tool_keywords.items():
                            if any(kw in content_lower for kw in keywords):
                                _tracker.register_tool_task_mapping(tool_key, [task_id])
                                break
        
        return {}
    
    # 智能匹配：从当前任务列表中查找可能相关的任务
    matching_tasks = []
    tool_name_lower = tool_name.lower()
    
    for todo in _tracker.current_todos:
        if isinstance(todo, dict):
            content = todo.get('content', '').lower()
            status = todo.get('status', 'pending')
            task_id = todo.get('id')
            
            # 如果任务状态是 pending 或 in_progress，且内容中提到工具名称
            if status in ['pending', 'in_progress']:
                # 简单的关键词匹配
                tool_keywords_map = {
                    'websearch': ['搜索', '查询', '查找', 'search', 'web', '网络'],
                    'write': ['写入', '创建', '生成', 'write', 'create', '文件'],
                    'read': ['读取', '读取', 'read', '文件'],
                    'bash': ['执行', '运行', '命令', 'bash', 'command', '脚本'],
                }
                
                # 检查任务内容是否包含工具相关的关键词
                keywords = tool_keywords_map.get(tool_name_lower, [])
                if any(kw in content for kw in keywords):
                    if task_id:
                        matching_tasks.append((task_id, status))
    
    # 如果没有匹配的任务，不处理
    if not matching_tasks:
        return {}
    
    # 构建系统消息，提示 Claude 更新任务状态
    if is_error:
        # 工具执行失败，保持任务状态不变
        logger.warning(f"[TodoProgressHook] 工具执行失败: {tool_name}, 任务状态保持不变")
        return {}
    else:
        # 工具执行成功，提示更新任务状态
        # 优先更新 in_progress 的任务，然后是 pending 的任务
        in_progress_tasks = [tid for tid, st in matching_tasks if st == 'in_progress']
        pending_tasks = [tid for tid, st in matching_tasks if st == 'pending']
        tasks_to_complete = in_progress_tasks if in_progress_tasks else pending_tasks
        
        if tasks_to_complete:
            task_ids_str = ", ".join(tasks_to_complete)
            system_message = (
                f"⚠️ **任务进度更新提醒**：\n"
                f"工具 `{tool_name}` 已成功执行。\n"
                f"请立即调用 `enhanced_todo_write` 将以下任务状态更新为 `completed`：{task_ids_str}\n"
                f"这是为了保持任务进度的实时性，让用户能够看到实时进度。\n"
                f"**重要**：必须立即更新，不要等到所有任务完成后再更新。"
            )
            
            logger.info(f"[TodoProgressHook] 提示更新任务状态: {tool_name} -> {task_ids_str}")
            
            return {
                'systemMessage': system_message
            }
    
    return {}


async def pre_tool_use_hook(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: HookContext
) -> dict[str, Any]:
    """
    PreToolUse Hook：工具调用前触发
    
    功能：
    1. 检测是否有对应的待处理任务
    2. 如果有，提示 Claude 先将任务状态更新为 in_progress
    """
    tool_name = input_data.get('tool_name', '')
    
    # 跳过 enhanced_todo_write 本身
    if tool_name in ['enhanced_todo_write', 'mcp__custom_tools__enhanced_todo_write']:
        return {}
    
    # 检查是否有对应的待处理任务
    pending_tasks = _tracker.get_pending_tasks_for_tool(tool_name)
    
    if pending_tasks:
        task_ids_str = ", ".join(pending_tasks)
        system_message = (
            f"⚠️ **任务进度更新提醒**：\n"
            f"即将调用工具 `{tool_name}` 执行任务。\n"
            f"请先调用 `enhanced_todo_write` 将以下任务状态更新为 `in_progress`：{task_ids_str}\n"
            f"然后再执行工具调用。这是为了保持任务进度的实时性。"
        )
        
        logger.info(f"[TodoProgressHook] 提示更新任务为进行中: {tool_name} -> {task_ids_str}")
        
        return {
            'systemMessage': system_message
        }
    
    return {}


def get_todo_progress_hooks() -> dict:
    """
    获取 Todo 进度跟踪的 Hook 配置
    
    返回：
        Hook 配置字典，可以直接传递给 ClaudeAgentOptions
    """
    return {
        'PreToolUse': [
            HookMatcher(
                hooks=[pre_tool_use_hook],
                timeout=5.0  # 5秒超时，避免阻塞
            )
        ],
        'PostToolUse': [
            HookMatcher(
                hooks=[post_tool_use_hook],
                timeout=5.0  # 5秒超时，避免阻塞
            )
        ]
    }


def reset_tracker():
    """重置跟踪器（新会话开始时调用）"""
    _tracker.reset()


def get_tracker() -> TodoProgressTracker:
    """获取跟踪器实例"""
    return _tracker
