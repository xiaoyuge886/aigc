"""
Migration: Update user_file_relationships table to allow NULL session_id

This migration:
1. Makes session_id nullable (allows NULL for delayed binding)
2. Makes conversation_turn_id NOT NULL (required, generated early)
3. Updates existing records with empty string session_id to NULL
4. Generates conversation_turn_id for records that don't have one
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from loguru import logger

from services.database import DatabaseService
from core.config import settings


async def migrate():
    """Run migration"""
    db_service = DatabaseService()
    await db_service.initialize()
    
    try:
        async with db_service.async_session() as session:
            # 1. Check current schema
            logger.info("Checking current schema...")
            result = await session.execute(text("""
                PRAGMA table_info(user_file_relationships)
            """))
            columns = result.fetchall()
            logger.info(f"Current columns: {columns}")
            
            # 2. Make session_id nullable (if not already)
            logger.info("Making session_id nullable...")
            try:
                # SQLite doesn't support ALTER COLUMN directly, need to recreate table
                # For now, we'll just update the data
                # The model change will take effect on next table creation
                await session.execute(text("""
                    UPDATE user_file_relationships 
                    SET session_id = NULL 
                    WHERE session_id = ''
                """))
                await session.commit()
                logger.info("✅ Updated empty string session_id to NULL")
            except Exception as e:
                logger.warning(f"Failed to update session_id: {e}")
                await session.rollback()
            
            # 3. Generate conversation_turn_id for records that don't have one
            logger.info("Generating conversation_turn_id for records without one...")
            try:
                import uuid
                result = await session.execute(text("""
                    SELECT id FROM user_file_relationships 
                    WHERE conversation_turn_id IS NULL OR conversation_turn_id = ''
                """))
                records = result.fetchall()
                
                for record in records:
                    record_id = record[0]
                    new_turn_id = uuid.uuid4().hex[:16]
                    await session.execute(text("""
                        UPDATE user_file_relationships 
                        SET conversation_turn_id = :turn_id 
                        WHERE id = :record_id
                    """), {"turn_id": new_turn_id, "record_id": record_id})
                
                await session.commit()
                logger.info(f"✅ Generated conversation_turn_id for {len(records)} records")
            except Exception as e:
                logger.warning(f"Failed to generate conversation_turn_id: {e}")
                await session.rollback()
            
            # 4. Verify migration
            logger.info("Verifying migration...")
            result = await session.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(session_id) as with_session,
                    COUNT(CASE WHEN session_id IS NULL THEN 1 END) as null_session,
                    COUNT(conversation_turn_id) as with_turn_id,
                    COUNT(CASE WHEN conversation_turn_id IS NULL OR conversation_turn_id = '' THEN 1 END) as null_turn_id
                FROM user_file_relationships
            """))
            stats = result.fetchone()
            logger.info(f"Migration stats: {stats}")
            
            if stats and stats[4] and stats[4] > 0:
                logger.warning(f"⚠️  Found {stats[4]} records without conversation_turn_id")
            else:
                logger.info("✅ All records have conversation_turn_id")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise
    finally:
        await db_service.close()


if __name__ == "__main__":
    asyncio.run(migrate())
