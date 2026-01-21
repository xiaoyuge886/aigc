"""
Migration: 添加用户场景配置表和会话场景配置表
创建时间: 2026-01-04
描述: 添加 user_scenario_configs 和 session_scenario_configs 表，支持多场景选择和自定义prompt
"""
import asyncio
from pathlib import Path
import sys

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from services.database import DatabaseService


async def upgrade():
    """执行迁移"""
    db_service = DatabaseService()
    await db_service.initialize()
    
    async with db_service.async_session() as session:
        try:
            # 创建 user_scenario_configs 表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_scenario_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    scenario_ids TEXT,
                    user_custom_prompt TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # 创建索引
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_scenario_configs_user_id 
                ON user_scenario_configs(user_id)
            """))
            
            # 创建 session_scenario_configs 表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS session_scenario_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    scenario_ids TEXT,
                    session_custom_prompt TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """))
            
            # 注意：如果表已存在但没有 id 字段，需要添加
            # 检查并修复表结构（如果表已存在但缺少 id 字段）
            try:
                await session.execute(text("""
                    SELECT id FROM user_scenario_configs LIMIT 1
                """))
            except Exception:
                # 表存在但没有 id 字段，需要重建表
                await session.execute(text("DROP TABLE IF EXISTS user_scenario_configs"))
                await session.execute(text("DROP TABLE IF EXISTS session_scenario_configs"))
                await session.commit()
                
                # 重新创建表
                await session.execute(text("""
                    CREATE TABLE user_scenario_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL UNIQUE,
                        scenario_ids TEXT,
                        user_custom_prompt TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """))
                
                await session.execute(text("""
                    CREATE TABLE session_scenario_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL UNIQUE,
                        scenario_ids TEXT,
                        session_custom_prompt TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                    )
                """))
            
            # 创建索引
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_session_scenario_configs_session_id 
                ON session_scenario_configs(session_id)
            """))
            
            await session.commit()
            print("✅ 成功创建 user_scenario_configs 和 session_scenario_configs 表")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 迁移失败: {e}")
            raise
    await db_service.close()


async def downgrade():
    """回滚迁移"""
    db_service = DatabaseService()
    await db_service.initialize()
    
    async with db_service.async_session() as session:
        try:
            await session.execute(text("DROP TABLE IF EXISTS session_scenario_configs"))
            await session.execute(text("DROP TABLE IF EXISTS user_scenario_configs"))
            await session.commit()
            print("✅ 成功删除 user_scenario_configs 和 session_scenario_configs 表")
        except Exception as e:
            await session.rollback()
            print(f"❌ 回滚失败: {e}")
            raise
    await db_service.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        asyncio.run(downgrade())
    else:
        asyncio.run(upgrade())
