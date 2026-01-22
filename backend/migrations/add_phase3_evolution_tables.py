"""
Migration: 添加 Phase 3 自我进化机制相关表
创建时间: 2026-01-05
描述: 添加用户反馈、偏好缓存、会话偏好、用户行为统计表
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
            # 创建 user_feedback 表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_id TEXT,
                    message_id INTEGER,
                    conversation_turn_id TEXT,
                    feedback_type TEXT NOT NULL,
                    feedback_data TEXT,
                    user_prompt TEXT,
                    assistant_response TEXT,
                    scenario_ids TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
                    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
                )
            """))
            
            # 创建索引
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_feedback_user_id ON user_feedback(user_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_feedback_session_id ON user_feedback(session_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_feedback_type ON user_feedback(feedback_type)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_feedback_created_at ON user_feedback(created_at)
            """))
            
            # 创建 user_preferences_cache 表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_preferences_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    data_summary_hash TEXT NOT NULL,
                    preferences TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_preferences_cache_user_id ON user_preferences_cache(user_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_preferences_cache_hash ON user_preferences_cache(data_summary_hash)
            """))
            
            # 创建 session_preferences 表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS session_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    preferences TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_session_preferences_session_id ON session_preferences(session_id)
            """))
            
            # 创建 user_behavior_stats 表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_behavior_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    total_sessions INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    total_feedback INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    dislike_count INTEGER DEFAULT 0,
                    scenario_usage TEXT,
                    question_types TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_behavior_stats_user_id ON user_behavior_stats(user_id)
            """))
            
            await session.commit()
            print("✅ 成功创建 Phase 3 自我进化机制相关表")
            print("   - user_feedback")
            print("   - user_preferences_cache")
            print("   - session_preferences")
            print("   - user_behavior_stats")
            
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
            await session.execute(text("DROP TABLE IF EXISTS user_behavior_stats"))
            await session.execute(text("DROP TABLE IF EXISTS session_preferences"))
            await session.execute(text("DROP TABLE IF EXISTS user_preferences_cache"))
            await session.execute(text("DROP TABLE IF EXISTS user_feedback"))
            await session.commit()
            print("✅ 成功删除 Phase 3 自我进化机制相关表")
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
