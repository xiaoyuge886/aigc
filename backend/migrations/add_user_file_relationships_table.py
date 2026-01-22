"""
Migration: Add user_file_relationships table

This migration creates a table to store the relationship between users, sessions,
conversation turns, and uploaded files. This table works with the docs-management
index system to enable file search and retrieval in conversations.
"""
import asyncio
import sqlite3
from pathlib import Path


async def migrate():
    """Run migration"""
    # Get database path
    db_path = Path(__file__).parent.parent / "data" / "sessions.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}, skipping migration")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_file_relationships'
        """)
        if cursor.fetchone():
            print("✓ user_file_relationships table already exists")
            return
        
        print("Creating user_file_relationships table...")
        cursor.execute("""
            CREATE TABLE user_file_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id VARCHAR(36) NOT NULL,
                conversation_turn_id VARCHAR(32),
                doc_id VARCHAR(255) NOT NULL UNIQUE,
                file_name VARCHAR(255) NOT NULL,
                file_type VARCHAR(100) NOT NULL,
                file_size INTEGER,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_user_file_relationships_user_id 
            ON user_file_relationships(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_user_file_relationships_session_id 
            ON user_file_relationships(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_user_file_relationships_conversation_turn_id 
            ON user_file_relationships(conversation_turn_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_user_file_relationships_doc_id 
            ON user_file_relationships(doc_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_user_file_relationships_is_active 
            ON user_file_relationships(is_active)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_user_file_relationships_created_at 
            ON user_file_relationships(created_at)
        """)
        
        # Create composite indexes for common query patterns
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_user_file_relationships_session_turn 
            ON user_file_relationships(session_id, conversation_turn_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_user_file_relationships_user_created 
            ON user_file_relationships(user_id, created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_user_file_relationships_session_active 
            ON user_file_relationships(session_id, is_active)
        """)
        
        conn.commit()
        print("✓ Created user_file_relationships table and indexes")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
