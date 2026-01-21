"""
工具自动注册服务
在应用启动时自动发现 MCP 工具并同步到数据库
"""
import json
from typing import List, Set
from datetime import datetime
from loguru import logger
from tools.custom_tools import get_custom_tools_server


class ToolRegistry:
    """工具自动注册服务"""
    
    # SDK 内置工具列表
    SDK_BUILTIN_TOOLS = [
        "Task", "Bash", "Glob", "Grep", "ExitPlanMode", 
        "Read", "Edit", "Write", "NotebookEdit", "WebFetch", 
        "TodoWrite", "WebSearch", "BashOutput", "KillShell", 
        "Skill", "SlashCommand"
    ]
    
    def __init__(self):
        """初始化工具注册器"""
        self.mcp_server = get_custom_tools_server()
        self._tool_list = None  # 缓存工具列表
    
    def _get_tools_list(self) -> List:
        """获取工具函数列表（带缓存）"""
        if self._tool_list is None:
            # 直接从 custom_tools.py 导入工具列表
            from tools.custom_tools import (
                get_current_time, calculate, string_operations, get_system_info,
                sqlite_query_tool, sqlite_get_tables, sqlite_get_schema,
                sqlite_test_connection, water_institute_search, tavily_search_tool,
                enhanced_todo_write, todo_statistics
            )
            self._tool_list = [
                get_current_time, calculate, string_operations, get_system_info,
                sqlite_query_tool, sqlite_get_tables, sqlite_get_schema,
                sqlite_test_connection, water_institute_search, tavily_search_tool,
                enhanced_todo_write, todo_statistics
            ]
        return self._tool_list

    def discover_mcp_tools(self) -> List[dict]:
        """
        发现所有 MCP 工具

        Returns:
            MCP 工具列表
        """
        mcp_tools = []

        # 从工具函数列表提取元数据
        tools = self._get_tools_list()

        for tool in tools:
            # @tool 装饰器会添加 name 和 description 属性
            tool_name = getattr(tool, 'name', None)
            if not tool_name:
                # 回退到 __name__ 属性
                tool_name = getattr(tool, '__name__', 'unknown')

            tool_desc = getattr(tool, 'description', None)
            if not tool_desc:
                tool_doc = getattr(tool, '__doc__', '')
                tool_desc = self._extract_description(tool_doc)

            mcp_tools.append({
                "name": f"mcp__custom_tools__{tool_name}",
                "display_name": tool_name.replace('_', ' ').title(),
                "description": tool_desc,
                "category": "custom",
                "tool_type": "mcp",
                "is_enabled": True,
                "is_public": True
            })

        logger.info(f"[ToolRegistry] Discovered {len(mcp_tools)} MCP tools")
        return mcp_tools
    
    def _extract_description(self, doc: str) -> str:
        """从文档字符串提取描述"""
        if not doc:
            return "No description"
        
        # 取第一行作为简短描述
        lines = doc.strip().split('\n')
        return lines[0] if lines else "No description"
    
    async def sync_to_database(self, db_service):
        """
        同步所有工具到数据库
        
        Args:
            db_service: 数据库服务实例
        """
        async with db_service.async_session() as session:
            from sqlalchemy import text
            
            # 1. 获取数据库中现有的 MCP 工具
            result = await session.execute(
                text("SELECT name FROM tools WHERE tool_type = 'mcp'")
            )
            existing_tools = {row[0] for row in result}
            
            # 2. 发现所有 MCP 工具
            discovered_tools = self.discover_mcp_tools()
            discovered_names = {t['name'] for t in discovered_tools}
            
            # 3. 计算需要添加和删除的工具
            to_add = discovered_names - existing_tools
            to_remove = existing_tools - discovered_names
            
            # 4. 添加新工具
            added_count = 0
            for tool in discovered_tools:
                if tool['name'] in to_add:
                    try:
                        await session.execute(
                            text("""
                                INSERT INTO tools (
                                    name, display_name, description, category, 
                                    tool_type, is_enabled, is_public, 
                                    created_at, updated_at
                                ) VALUES (
                                    :name, :display_name, :description, :category,
                                    :tool_type, :is_enabled, :is_public,
                                    :created_at, :updated_at
                                )
                                ON CONFLICT(name) DO UPDATE SET
                                    display_name = excluded.display_name,
                                    description = excluded.description,
                                    updated_at = excluded.updated_at
                            """),
                            {
                                **tool,
                                "created_at": datetime.now(),
                                "updated_at": datetime.now()
                            }
                        )
                        added_count += 1
                        logger.info(f"[ToolRegistry] ✅ Added tool: {tool['name']}")
                    except Exception as e:
                        logger.error(f"[ToolRegistry] ❌ Failed to add {tool['name']}: {e}")
            
            # 5. 删除已不存在的工具（可选，这里暂时不删除）
            # for tool_name in to_remove:
            #     await session.execute(
            #         text("DELETE FROM tools WHERE name = :name"),
            #         {"name": tool_name}
            #     )
            #     logger.info(f"[ToolRegistry] 🗑️  Removed tool: {tool_name}")
            
            # 6. 提交更改
            await session.commit()
            
            logger.info(f"[ToolRegistry] ✅ Sync completed:")
            logger.info(f"   - Added: {added_count} tools")
            logger.info(f"   - Removed: {len(to_remove)} tools (skipped)")
            logger.info(f"   - Total MCP tools: {len(discovered_tools)}")
            
            return {
                "success": True,
                "added": added_count,
                "removed": len(to_remove),
                "total": len(discovered_tools)
            }


# 全局实例
_tool_registry = None

def get_tool_registry() -> ToolRegistry:
    """获取工具注册器实例"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


async def auto_register_tools(db_service):
    """
    自动注册工具到数据库
    在应用启动时调用
    
    Args:
        db_service: 数据库服务实例
    """
    try:
        registry = get_tool_registry()
        result = await registry.sync_to_database(db_service)
        logger.info(f"[ToolRegistry] 🎉 Auto-registration completed: {result}")
        return result
    except Exception as e:
        logger.error(f"[ToolRegistry] ❌ Auto-registration failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import asyncio
    from services.database import DatabaseService
    
    async def main():
        db_service = DatabaseService()
        await auto_register_tools(db_service)
    
    asyncio.run(main())
