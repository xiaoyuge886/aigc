"""
Migration: Add system_prompts and skills tables for resource center

This migration adds two new tables:
1. system_prompts - for managing system prompt templates
2. skills - for managing skill templates

Run this migration from the backend directory:
    cd backend
    python migrations/add_resource_center_tables.py
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text
from loguru import logger

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.database import DatabaseService
from core.config import settings


async def upgrade():
    """Create system_prompts and skills tables"""
    db_service = DatabaseService()
    
    # Initialize database connection
    await db_service.initialize()
    
    try:
        async with db_service.async_session() as session:
            # Create system_prompts table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS system_prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id VARCHAR(100) NOT NULL UNIQUE,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    category VARCHAR(50),
                    content TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    is_default BOOLEAN DEFAULT 0,
                    created_by INTEGER,
                    is_public BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """))
            
            # Create indexes for system_prompts
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_system_prompts_prompt_id ON system_prompts(prompt_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_system_prompts_name ON system_prompts(name)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_system_prompts_category ON system_prompts(category)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_system_prompts_is_default ON system_prompts(is_default)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_system_prompts_is_public ON system_prompts(is_public)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_system_prompts_created_by ON system_prompts(created_by)
            """))
            
            # Create skills table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_id VARCHAR(100) NOT NULL UNIQUE,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    category VARCHAR(50),
                    skill_content TEXT NOT NULL,
                    skill_config TEXT,
                    usage_count INTEGER DEFAULT 0,
                    is_default BOOLEAN DEFAULT 0,
                    created_by INTEGER,
                    is_public BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """))
            
            # Create indexes for skills
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_skills_skill_id ON skills(skill_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_skills_is_default ON skills(is_default)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_skills_is_public ON skills(is_public)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_skills_created_by ON skills(created_by)
            """))
            
            await session.commit()
            logger.info("✅ Migration completed: system_prompts and skills tables created")
            print("✅ Migration completed: system_prompts and skills tables created")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def downgrade():
    """Drop system_prompts and skills tables"""
    db_service = DatabaseService()
    
    # Initialize database connection
    await db_service.initialize()
    
    try:
        async with db_service.async_session() as session:
            await session.execute(text("DROP TABLE IF EXISTS skills"))
            await session.execute(text("DROP TABLE IF EXISTS system_prompts"))
            await session.commit()
            logger.info("✅ Migration rollback completed: system_prompts and skills tables dropped")
            print("✅ Migration rollback completed: system_prompts and skills tables dropped")
    except Exception as e:
        logger.error(f"Migration rollback failed: {e}")
        raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        asyncio.run(downgrade())
    else:
        asyncio.run(upgrade())
