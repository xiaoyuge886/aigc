"""
Migration: Update user_file_relationships table schema

This migration recreates the table to:
1. Make session_id nullable (allows NULL for delayed binding)
2. Make conversation_turn_id NOT NULL (required, generated early)
3. Migrate existing data
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


async def migrate():
    """Run migration"""
    db_service = DatabaseService()
    await db_service.initialize()
    
    try:
        async with db_service.async_session() as session:
            # 1. Check if table exists
            logger.info("Checking table existence...")
            result = await session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='user_file_relationships'
            """))
            if not result.fetchone():
                logger.info("Table doesn't exist, will be created by model")
                return
            
            # 2. Backup existing data
            logger.info("Backing up existing data...")
            result = await session.execute(text("""
                SELECT * FROM user_file_relationships
            """))
            existing_records = result.fetchall()
            logger.info(f"Found {len(existing_records)} existing records")
            
            # 3. Create new table with updated schema
            logger.info("Creating new table with updated schema...")
            
            # Drop old table (data is backed up)
            await session.execute(text("DROP TABLE IF EXISTS user_file_relationships_old"))
            await session.execute(text("""
                ALTER TABLE user_file_relationships 
                RENAME TO user_file_relationships_old
            """))
            
            # Create new table with updated schema
            await session.execute(text("""
                CREATE TABLE user_file_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id VARCHAR(36),
                    conversation_turn_id VARCHAR(32) NOT NULL,
                    doc_id VARCHAR(255) NOT NULL UNIQUE,
                    file_name VARCHAR(255) NOT NULL,
                    file_type VARCHAR(100) NOT NULL,
                    file_size INTEGER,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """))
            
            # Create indexes
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_file_user ON user_file_relationships(user_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_file_session ON user_file_relationships(session_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_file_turn ON user_file_relationships(conversation_turn_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_file_doc_id ON user_file_relationships(doc_id)
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_file_active ON user_file_relationships(is_active)
            """))
            
            # 4. Migrate data
            logger.info("Migrating data...")
            import uuid
            
            migrated_count = 0
            for record in existing_records:
                record_id, user_id, old_session_id, old_turn_id, doc_id, file_name, file_type, file_size, is_active, created_at = record
                
                # Convert empty string to NULL for session_id
                session_id = None if (old_session_id == "" or old_session_id is None) else old_session_id
                
                # Generate conversation_turn_id if missing
                conversation_turn_id = old_turn_id if (old_turn_id and old_turn_id != "") else uuid.uuid4().hex[:16]
                
                # Insert into new table
                await session.execute(text("""
                    INSERT INTO user_file_relationships 
                    (id, user_id, session_id, conversation_turn_id, doc_id, file_name, file_type, file_size, is_active, created_at)
                    VALUES (:id, :user_id, :session_id, :conversation_turn_id, :doc_id, :file_name, :file_type, :file_size, :is_active, :created_at)
                """), {
                    "id": record_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "conversation_turn_id": conversation_turn_id,
                    "doc_id": doc_id,
                    "file_name": file_name,
                    "file_type": file_type,
                    "file_size": file_size,
                    "is_active": is_active,
                    "created_at": created_at
                })
                migrated_count += 1
            
            await session.commit()
            logger.info(f"✅ Migrated {migrated_count} records")
            
            # 5. Verify migration
            logger.info("Verifying migration...")
            result = await session.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(session_id) as with_session,
                    COUNT(CASE WHEN session_id IS NULL THEN 1 END) as null_session,
                    COUNT(conversation_turn_id) as with_turn_id
                FROM user_file_relationships
            """))
            stats = result.fetchone()
            logger.info(f"Migration stats: total={stats[0]}, with_session={stats[1]}, null_session={stats[2]}, with_turn_id={stats[3]}")
            
            # 6. Drop old table (optional, can keep as backup)
            # await session.execute(text("DROP TABLE user_file_relationships_old"))
            logger.info("✅ Migration completed. Old table kept as backup: user_file_relationships_old")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        await session.rollback()
        raise
    finally:
        await db_service.close()


if __name__ == "__main__":
    asyncio.run(migrate())
