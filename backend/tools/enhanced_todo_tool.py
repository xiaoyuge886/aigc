"""
增强版 Todo 工具 - 扩展 TodoWrite 功能

提供额外的功能：
- 优先级管理
- 标签分类
- 截止日期
- 任务依赖关系
- 任务统计
- 层级任务结构（支持 1, 1.1, 1.1.1 格式）
"""
from typing import Any, List, Dict
import re

from claude_agent_sdk import tool, create_sdk_mcp_server


def parse_task_level(content: str) -> tuple:
    """
    解析任务层级

    支持格式:
    - "1 任务名称" -> level=1, parent=None
    - "1.1 任务名称" -> level=1.1, parent="1"
    - "1.1.1 任务名称" -> level=1.1.1, parent="1.1"

    层级结构示例:
    1. 收集数据
      1.1 搜索温榆河信息
      1.2 搜索水文数据
    2. 编写报告
      2.1 编写第一章
      2.2 编写第二章
        2.2.1 补充数据

    Returns:
        (level_str, parent_level): 层级字符串和父级层级
    """
    # 匹配开头的数字层级格式 (支持任意层级深度)
    match = re.match(r'^(\d+(?:\.\d+)*)(?:\.\s|\s)', content.strip())

    if match:
        level_str = match.group(1)

        # 计算父级：去掉最后一层
        parts = level_str.split('.')
        if len(parts) > 1:
            parent_level = '.'.join(parts[:-1])
        else:
            parent_level = None

        return (level_str, parent_level)

    # 如果没有层级前缀，返回0级
    return (None, None)


def build_task_hierarchy(todos: List[Dict[str, Any]]) -> List[Dict]:
    """
    构建任务层级结构

    Args:
        todos: 任务列表

    Returns:
        层级化的任务树结构
    """
    # 解析所有任务
    parsed_tasks = []
    for todo in todos:
        level_str, parent_level = parse_task_level(todo.get('content', ''))
        parsed_tasks.append({
            'original': todo,
            'level': level_str,
            'parent': parent_level
        })

    # 按层级排序（字符串排序即可，因为 "1" < "1.1" < "2"）
    parsed_tasks.sort(key=lambda x: (x['level'] or '999'))

    # 构建层级树
    root_tasks = []
    task_map = {}  # level -> task

    for task in parsed_tasks:
        level = task['level']
        parent = task['parent']

        # 创建任务节点
        task_node = {
            **task['original'],
            'level': level,
            'subtasks': []
        }

        if parent is None:
            # 顶级任务
            root_tasks.append(task_node)
        else:
            # 子任务，找到父任务并添加
            if parent in task_map:
                task_map[parent]['subtasks'].append(task_node)
            else:
                # 父任务不存在，作为顶级任务
                root_tasks.append(task_node)

        # 记录到map中，供后续子任务查找
        task_map[level] = task_node

    return root_tasks


def update_parent_tasks_status(task_tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    更新父任务的状态，根据子任务的完成情况

    规则：
    - 如果所有子任务都完成 → 父任务完成
    - 如果有子任务进行中 → 父任务进行中
    - 如果有子任务待处理但没进行中 → 父任务待处理
    """
    def update_task_recursive(task: Dict[str, Any]) -> Dict[str, Any]:
        # 先递归更新所有子任务
        if task.get('subtasks'):
            task['subtasks'] = [update_task_recursive(st) for st in task['subtasks']]

            # 根据子任务状态更新父任务状态
            subtasks = task['subtasks']
            total_subtasks = len(subtasks)
            completed_subtasks = sum(1 for st in subtasks if st.get('status') == 'completed')
            in_progress_subtasks = sum(1 for st in subtasks if st.get('status') == 'in_progress')

            # 添加子任务统计信息到父任务
            task['completed_subtasks'] = completed_subtasks
            task['total_subtasks'] = total_subtasks

            # 更新父任务状态
            if completed_subtasks == total_subtasks:
                # 所有子任务都完成
                task['status'] = 'completed'
            elif in_progress_subtasks > 0 or completed_subtasks > 0:
                # 有子任务进行中或部分完成
                task['status'] = 'in_progress'
            else:
                # 所有子任务都待处理
                task['status'] = 'pending'

        return task

    return [update_task_recursive(task) for task in task_tree]


def flatten_task_tree(task_tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将层级树展平为列表，保留更新后的状态和子任务统计信息
    
    注意：展平时会移除 subtasks 字段，避免前端重复显示
    """
    result = []

    def flatten_recursive(task: Dict[str, Any]):
        # 创建任务副本，移除 subtasks 字段（避免前端重复显示）
        task_copy = {k: v for k, v in task.items() if k != 'subtasks'}
        # 添加任务到结果
        result.append(task_copy)

        # 递归处理子任务
        if task.get('subtasks'):
            for subtask in task['subtasks']:
                flatten_recursive(subtask)

    for task in task_tree:
        flatten_recursive(task)

    return result


def format_hierarchical_todos(task_tree: List[Dict[str, Any]], indent: int = 0) -> str:
    """
    格式化层级任务为文本

    Args:
        task_tree: 任务树
        indent: 缩进级别

    Returns:
        格式化的任务列表文本
    """
    result = []
    indent_str = "  " * indent

    for task in task_tree:
        # 状态图标
        status = task.get('status', 'pending')
        status_icon = {
            'completed': '✅',
            'in_progress': '🔄',
            'pending': '⏳'
        }.get(status, '❓')

        # 任务内容（移除层级前缀，因为已经有缩进了）
        content = task.get('content', '')
        content_cleaned = re.sub(r'^\d+(?:\.\d+)*\s*', '', content)

        # 优先级图标
        priority = task.get('priority', 'medium')
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "")

        result.append(f"{indent_str}{status_icon} {priority_icon} {content_cleaned}")

        # 递归处理子任务
        if task.get('subtasks'):
            result.append(format_hierarchical_todos(task['subtasks'], indent + 1))

    return "\n".join(result)


def count_tasks_recursive(tasks: List[Dict], status_filter: str = None) -> int:
    """递归统计任务数量"""
    count = 0
    for task in tasks:
        # 统计当前任务（如果匹配状态过滤器）
        if status_filter is None or task.get('status') == status_filter:
            count += 1
        # 递归统计子任务（无论当前任务是否匹配）
        if task.get('subtasks'):
            count += count_tasks_recursive(task.get('subtasks', []), status_filter)
    return count


@tool("enhanced_todo_write", """增强版待办事项工具，支持层级任务、优先级、标签等功能。

**必须的输入格式：**
{
  "title": str,           # 任务列表标题（必需）
  "todos": str,           # JSON 字符串格式的任务列表数组（必需），格式: "[{...}, {...}]"
  "priority": str,        # 整体优先级：high, medium, low（可选，默认 medium）
  "tags": str,            # JSON 字符串格式的标签数组（可选），格式: "[\"tag1\", \"tag2\"]"
  "due_date": str         # 截止日期 ISO 格式，如 "2025-01-01"（可选）
}

**todos 数组中每个任务对象的格式：**
{
  "content": str,         # 任务内容，支持层级格式如 "1 任务", "1.1 子任务"
  "status": str,          # 任务状态：pending, in_progress, completed（可选，默认 pending）
  "activeForm": str,      # 当前活动状态描述（可选，默认 ""）
  "id": str,              # 任务ID（可选，自动生成）
  "priority": str,        # 任务优先级（可选，继承整体优先级）
  "tags": str|list,       # 任务标签（可选，继承整体标签）
  "due_date": str         # 任务截止日期（可选，继承整体截止日期）
}

**示例输入：**
{
  "title": "未来十年中国农村发展报告（2025-2035）",
  "todos": "[{\"content\": \"1 数据收集与研究\", \"status\": \"completed\"}, {\"content\": \"1.1 搜索中国农村发展现状\", \"status\": \"in_progress\", \"activeForm\": \"正在搜索\"}]",
  "priority": "high",
  "tags": "[\"农村发展\", \"研究报告\", \"乡村振兴\"]",
  "due_date": "2025-01-10"
}""", {
    "todos": str,  # 必须是 JSON 字符串格式的任务列表数组
    "title": str,  # 任务列表标题（必需）
    "priority": str,  # 可选：high, medium, low
    "tags": str,  # 可选：JSON 字符串格式的标签数组
    "due_date": str,  # 可选：截止日期 ISO 格式
})
async def enhanced_todo_write(args: dict[str, Any]) -> dict[str, Any]:
    """
    增强版待办事项工具

    支持的功能：
    - **层级任务结构**：使用 "1 任务", "1.1 子任务", "1.1.1 子子任务" 格式
    - **优先级管理**（high, medium, low）
    - **标签分类**
    - **截止日期**

    **输入格式要求：**
    - todos: 必须是 JSON 字符串格式的数组，如: "[{...}, {...}]"
    - tags: 如果提供，必须是 JSON 字符串格式的数组，如: "[\"tag1\", \"tag2\"]"
    - title: 字符串，任务列表标题（必需）
    - priority: 字符串，可选值：high, medium, low（默认 medium）
    - due_date: 字符串，ISO 格式日期，如 "2025-01-01"（可选）

    Args:
        todos: JSON 字符串格式的待办事项列表数组（必需）
        title: 任务列表标题（必需）
        priority: 整体优先级（可选，默认 medium）
        tags: JSON 字符串格式的标签数组（可选）
        due_date: 整体截止日期 ISO 格式（可选）

    Returns:
        dict with enhanced todo information
    """
    import json
    
    # 获取必需参数
    title = args.get("title")
    if not title:
        return {
            "content": [{
                "type": "text",
                "text": "⚠️ 错误：title 参数是必需的"
            }],
            "is_error": True
        }
    
    # 获取 todos 参数（必须是 JSON 字符串）
    todos_raw = args.get("todos")
    if not todos_raw:
        return {
            "content": [{
                "type": "text",
                "text": "⚠️ 错误：todos 参数是必需的，必须是 JSON 字符串格式的数组"
            }],
            "is_error": True
        }
    
    # 解析 todos JSON 字符串
    if isinstance(todos_raw, str):
        try:
            todos = json.loads(todos_raw)
        except json.JSONDecodeError as e:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ todos参数格式错误：无法解析JSON字符串\n\n错误：{str(e)}\n\n原始数据：{todos_raw[:500]}"
                }],
                "is_error": True
            }
    elif isinstance(todos_raw, list):
        # 如果已经是列表，直接使用（兼容旧格式）
        todos = todos_raw
    else:
        return {
            "content": [{
                "type": "text",
                "text": f"⚠️ todos参数类型错误：必须是 JSON 字符串或列表，当前类型：{type(todos_raw).__name__}"
            }],
            "is_error": True
        }
    
    # 获取可选参数
    priority = args.get("priority", "medium")
    due_date = args.get("due_date")
    
    # 解析 tags JSON 字符串
    tags_raw = args.get("tags", "[]")
    if isinstance(tags_raw, str):
        try:
            tags = json.loads(tags_raw) if tags_raw else []
        except json.JSONDecodeError:
            # 如果解析失败，尝试作为单个标签处理
            tags = [tags_raw] if tags_raw else []
    elif isinstance(tags_raw, list):
        # 如果已经是列表，直接使用（兼容旧格式）
        tags = tags_raw
    else:
        tags = []

    if not todos or not isinstance(todos, list):
        return {
            "content": [{
                "type": "text",
                "text": "⚠️ 任务列表为空或格式错误：todos 必须是包含任务对象的数组"
            }],
            "is_error": True
        }

    # 处理每个任务，添加默认属性
    enhanced_todos = []
    for todo in todos:
        if not isinstance(todo, dict):
            continue  # 跳过无效的任务对象
        
        content = todo.get("content", "")
        if not content:
            continue  # 跳过没有内容的任务
        
        level, parent_level = parse_task_level(content)
        
        # 处理任务的 tags（可能是字符串或列表）
        todo_tags = todo.get("tags", tags)
        if isinstance(todo_tags, str):
            try:
                todo_tags = json.loads(todo_tags) if todo_tags else tags
            except json.JSONDecodeError:
                todo_tags = [todo_tags] if todo_tags else tags
        elif not isinstance(todo_tags, list):
            todo_tags = tags

        enhanced_todo = {
            "id": todo.get("id", f"todo-{len(enhanced_todos) + 1}"),
            "content": content,
            "status": todo.get("status", "pending"),
            "priority": todo.get("priority", priority),
            "tags": todo_tags,
            "due_date": todo.get("due_date", due_date),
            "activeForm": todo.get("activeForm", ""),
            "level": level,
            "parentLevel": parent_level
        }
        enhanced_todos.append(enhanced_todo)

    # 构建层级树
    task_tree = build_task_hierarchy(enhanced_todos)

    # 更新父任务状态（根据子任务完成情况）
    task_tree = update_parent_tasks_status(task_tree)

    # 将层级树展平，保留更新后的状态
    enhanced_todos = flatten_task_tree(task_tree)

    # 统计信息（使用递归函数）
    total = count_tasks_recursive(task_tree)
    completed = count_tasks_recursive(task_tree, 'completed')
    in_progress = count_tasks_recursive(task_tree, 'in_progress')
    pending = count_tasks_recursive(task_tree, 'pending')

    # 计算进度
    progress = (completed / total * 100) if total > 0 else 0

    # 格式化输出
    result_text = f"📋 {title}\n\n"
    result_text += f"📊 任务统计:\n"
    result_text += f"   总任务: {total} 个\n"
    result_text += f"   ✅ 已完成: {completed} 个\n"
    result_text += f"   🔄 进行中: {in_progress} 个\n"
    result_text += f"   ⏳ 待处理: {pending} 个\n"
    result_text += f"   📈 进度: {progress:.1f}%\n\n"
    result_text += "📝 任务列表:\n\n"
    result_text += format_hierarchical_todos(task_tree)

    # 将 enhanced_todos 作为 JSON 附加到文本末尾，供前端解析
    result_text += f"\n\n<!-- ENHANCED_TODOS_JSON:{json.dumps(enhanced_todos, ensure_ascii=False)} -->"

    return {
        "content": [{
            "type": "text",
            "text": result_text
        }],
        "metadata": {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "progress": progress,
            "task_tree": task_tree,
            "enhanced_todos": enhanced_todos
        }
    }


@tool("todo_statistics", "获取待办事项统计信息", {
    "todos": list  # 待办事项列表
})
async def todo_statistics(args: dict[str, Any]) -> dict[str, Any]:
    """
    分析待办事项并生成统计信息
    
    Args:
        todos: 待办事项列表
    
    Returns:
        dict with statistics
    """
    todos = args.get("todos", [])

    # 处理字符串格式的 todos 参数（AI有时会传递JSON字符串）
    if isinstance(todos, str):
        try:
            import json
            todos = json.loads(todos)
        except json.JSONDecodeError:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ todos参数格式错误：无法解析JSON字符串"
                }],
                "is_error": True
            }

    if not todos:
        return {
            "content": [{
                "type": "text",
                "text": "⚠️ 没有待办事项可分析"
            }]
        }
    
    # 统计
    total = len(todos)
    by_status = {}
    by_priority = {}
    
    for todo in todos:
        status = todo.get("status", "pending")
        priority = todo.get("priority", "medium")
        
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1
    
    completed = by_status.get("completed", 0)
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    result_text = f"""📊 待办事项统计报告

总体统计：
- 总任务数：{total}
- 已完成：{completed} ({completion_rate:.1f}%)
- 进行中：{by_status.get('in_progress', 0)}
- 待处理：{by_status.get('pending', 0)}

按优先级分布：
"""
    
    for priority in ["high", "medium", "low"]:
        count = by_priority.get(priority, 0)
        if count > 0:
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[priority]
            result_text += f"- {icon} {priority.capitalize()}: {count} 个\n"
    
    return {
        "content": [{
            "type": "text",
            "text": result_text
        }],
        "metadata": {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "completion_rate": completion_rate
        }
    }


# 创建增强版 Todo 工具服务器
def get_enhanced_todo_server():
    """
    获取增强版 Todo 工具服务器
    
    Returns:
        McpSdkServerConfig
    """
    return create_sdk_mcp_server(
        name="enhanced_todo",
        version="1.0.0",
        tools=[enhanced_todo_write, todo_statistics]
    )
