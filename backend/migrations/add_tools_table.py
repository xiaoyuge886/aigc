#!/usr/bin/env python3
"""
创建工具管理表

用于集中管理所有可用工具：
- 标准工具（SDK自带：Read, Write, Bash等）
- 自定义工具（custom_tools.py中的工具）
- 用户自定义工具
"""
import asyncio
import sys
from pathlib import Path

# 添加backend到path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.database import get_database_service
from sqlalchemy import text


async def create_tools_table():
    """创建工具管理表"""
    db = get_database_service()
    await db.initialize()

    try:
        async with db.async_session() as session:
            # 创建tools表
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL UNIQUE,
                display_name VARCHAR(200) NOT NULL,
                description TEXT,
                category VARCHAR(50) NOT NULL,  -- 'standard', 'custom', 'user_defined'
                tool_type VARCHAR(50) NOT NULL,  -- 'mcp', 'builtin', 'skill'
                mcp_server VARCHAR(100),  -- MCP服务器名称（如'custom_tools'）
                input_schema JSON,  -- 工具输入参数schema
                is_enabled BOOLEAN NOT NULL DEFAULT 1,
                is_public BOOLEAN NOT NULL DEFAULT 1,
                created_by INTEGER,
                usage_count INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
            """

            await session.execute(text(create_table_sql))

            # 创建索引
            index_sqls = [
                "CREATE INDEX IF NOT EXISTS ix_tools_name ON tools(name)",
                "CREATE INDEX IF NOT EXISTS ix_tools_category ON tools(category)",
                "CREATE INDEX IF NOT EXISTS ix_tools_tool_type ON tools(tool_type)",
                "CREATE INDEX IF NOT EXISTS ix_tools_mcp_server ON tools(mcp_server)",
            ]

            for index_sql in index_sqls:
                await session.execute(text(index_sql))

            await session.commit()

            print("✅ tools表创建成功")

            # 插入标准工具（SDK自带工具）
            standard_tools = [
                {
                    "name": "Read",
                    "display_name": "Read File",
                    "description": "Read file contents",
                    "category": "standard",
                    "tool_type": "builtin"
                },
                {
                    "name": "Write",
                    "display_name": "Write File",
                    "description": "Write content to file",
                    "category": "standard",
                    "tool_type": "builtin"
                },
                {
                    "name": "Edit",
                    "display_name": "Edit File",
                    "description": "Edit file using string replacement",
                    "category": "standard",
                    "tool_type": "builtin"
                },
                {
                    "name": "Bash",
                    "display_name": "Bash Command",
                    "description": "Execute bash commands",
                    "category": "standard",
                    "tool_type": "builtin"
                },
                {
                    "name": "Glob",
                    "display_name": "Glob Pattern",
                    "description": "Find files using glob patterns",
                    "category": "standard",
                    "tool_type": "builtin"
                },
                {
                    "name": "Grep",
                    "display_name": "Grep Search",
                    "description": "Search content using regex",
                    "category": "standard",
                    "tool_type": "builtin"
                },
                {
                    "name": "WebSearch",
                    "display_name": "Web Search",
                    "description": "Search the web",
                    "category": "standard",
                    "tool_type": "builtin"
                },
                {
                    "name": "WebFetch",
                    "display_name": "Web Fetch",
                    "description": "Fetch web content",
                    "category": "standard",
                    "tool_type": "builtin"
                },
                {
                    "name": "TodoWrite",
                    "display_name": "Todo List",
                    "description": "Manage todo items",
                    "category": "standard",
                    "tool_type": "builtin"
                },
                {
                    "name": "Skill",
                    "display_name": "Invoke Skill",
                    "description": "Invoke a specific skill",
                    "category": "standard",
                    "tool_type": "builtin"
                },
            ]

            # 插入custom_tools工具
            custom_tools = [
                {
                    "name": "mcp__custom_tools__get_current_time",
                    "display_name": "Get Current Time",
                    "description": "Get the current date and time",
                    "category": "custom",
                    "tool_type": "mcp",
                    "mcp_server": "custom_tools"
                },
                {
                    "name": "mcp__custom_tools__calculate",
                    "display_name": "Calculate",
                    "description": "Perform basic mathematical calculations",
                    "category": "custom",
                    "tool_type": "mcp",
                    "mcp_server": "custom_tools"
                },
                {
                    "name": "mcp__custom_tools__string_operations",
                    "display_name": "String Operations",
                    "description": "Perform string manipulation operations",
                    "category": "custom",
                    "tool_type": "mcp",
                    "mcp_server": "custom_tools"
                },
                {
                    "name": "mcp__custom_tools__get_system_info",
                    "display_name": "Get System Info",
                    "description": "Get basic system information",
                    "category": "custom",
                    "tool_type": "mcp",
                    "mcp_server": "custom_tools"
                },
                {
                    "name": "mcp__custom_tools__sqlite_query",
                    "display_name": "SQLite Query",
                    "description": "Execute SQL query on SQLite database",
                    "category": "custom",
                    "tool_type": "mcp",
                    "mcp_server": "custom_tools"
                },
                {
                    "name": "mcp__custom_tools__sqlite_get_tables",
                    "display_name": "SQLite Get Tables",
                    "description": "Get all table names from SQLite database",
                    "category": "custom",
                    "tool_type": "mcp",
                    "mcp_server": "custom_tools"
                },
                {
                    "name": "mcp__custom_tools__sqlite_get_schema",
                    "display_name": "SQLite Get Schema",
                    "description": "Get table schema from SQLite database",
                    "category": "custom",
                    "tool_type": "mcp",
                    "mcp_server": "custom_tools"
                },
                {
                    "name": "mcp__custom_tools__sqlite_test_connection",
                    "display_name": "SQLite Test Connection",
                    "description": "Test SQLite database connection",
                    "category": "custom",
                    "tool_type": "mcp",
                    "mcp_server": "custom_tools"
                },
                {
                    "name": "mcp__custom_tools__enhanced_todo_write",
                    "display_name": "Enhanced Todo Write",
                    "description": "Enhanced todo list with priority, tags, due date",
                    "category": "custom",
                    "tool_type": "mcp",
                    "mcp_server": "custom_tools"
                },
                {
                    "name": "mcp__custom_tools__todo_statistics",
                    "display_name": "Todo Statistics",
                    "description": "Get todo list statistics",
                    "category": "custom",
                    "tool_type": "mcp",
                    "mcp_server": "custom_tools"
                },
            ]

            # 合并所有工具
            all_tools = standard_tools + custom_tools

            # 批量插入
            for tool in all_tools:
                # 动态构建INSERT语句，只包含非None的字段
                fields = ['name', 'display_name', 'description', 'category', 'tool_type']
                values = {k: tool[k] for k in fields if k in tool}

                # 如果有mcp_server，添加到字段列表
                if 'mcp_server' in tool and tool['mcp_server']:
                    fields.append('mcp_server')
                    values['mcp_server'] = tool['mcp_server']

                # 构建SQL
                placeholders = ', '.join([f':{f}' for f in fields])
                field_names = ', '.join(fields)
                insert_sql = f"""
                INSERT OR IGNORE INTO tools
                ({field_names})
                VALUES ({placeholders})
                """
                await session.execute(text(insert_sql), values)

            await session.commit()

            print(f"✅ 成功插入 {len(all_tools)} 个工具")
            print(f"   - 标准工具: {len(standard_tools)} 个")
            print(f"   - 自定义工具: {len(custom_tools)} 个")

            # 验证插入
            result = await session.execute(text("SELECT COUNT(*) FROM tools"))
            count = result.scalar()
            print(f"\n📊 工具总数: {count}")

            # 按分类统计
            result = await session.execute(text("""
                SELECT category, COUNT(*) as count
                FROM tools
                GROUP BY category
            """))
            print("\n📋 分类统计:")
            for row in result:
                print(f"   - {row[0]}: {row[1]} 个")

    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        raise
    finally:
        await db.close()


if __name__ == '__main__':
    print("=" * 60)
    print("创建工具管理表")
    print("=" * 60)
    asyncio.run(create_tools_table())
    print("=" * 60)
