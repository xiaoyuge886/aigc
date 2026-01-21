"""
Database migration: Add platform configuration tables

This migration adds:
1. user_configs table - User-level configuration
2. business_scenarios table - Business scenario templates

Run this migration from the backend directory:
    cd backend
    python migrations/add_platform_tables.py
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


async def migrate():
    """Run migration to add platform tables"""
    db_service = DatabaseService()
    
    # Initialize database connection
    await db_service.initialize()
    
    try:
        async with db_service.async_session() as session:
            try:
                # Create user_configs table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL UNIQUE,
                        default_system_prompt TEXT,
                        default_allowed_tools TEXT,
                        default_model VARCHAR(50),
                        permission_mode VARCHAR(50),
                        max_turns INTEGER,
                        work_dir VARCHAR(500),
                        custom_tools TEXT,
                        custom_skills TEXT,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """))
                
                # Create index on user_id
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_user_configs_user_id ON user_configs(user_id)
                """))
                
                # Create business_scenarios table
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS business_scenarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scenario_id VARCHAR(100) NOT NULL UNIQUE,
                        name VARCHAR(200) NOT NULL,
                        description TEXT,
                        system_prompt TEXT NOT NULL,
                        allowed_tools TEXT,
                        recommended_model VARCHAR(50),
                        custom_tools TEXT,
                        skills TEXT,
                        workflow TEXT,
                        created_by INTEGER,
                        is_public BOOLEAN NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                    )
                """))
                
                # Create indexes
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_business_scenarios_scenario_id ON business_scenarios(scenario_id)
                """))
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_business_scenarios_name ON business_scenarios(name)
                """))
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_business_scenarios_created_by ON business_scenarios(created_by)
                """))
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_business_scenarios_is_public ON business_scenarios(is_public)
                """))
                
                await session.commit()
                logger.info("✅ Platform tables migration completed successfully")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Migration failed: {e}")
                raise
    finally:
        # Close database connection
        await db_service.close()


if __name__ == "__main__":
    asyncio.run(migrate())
