"""
Migration: Add conversation_turn_configs table

This migration creates a table to store configuration logs for each conversation turn,
including the final merged configuration and the source of each configuration item.
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
            WHERE type='table' AND name='conversation_turn_configs'
        """)
        if cursor.fetchone():
            print("✓ conversation_turn_configs table already exists")
            return
        
        print("Creating conversation_turn_configs table...")
        cursor.execute("""
            CREATE TABLE conversation_turn_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_turn_id VARCHAR(32) NOT NULL UNIQUE,
                session_id VARCHAR(36) NOT NULL,
                user_id INTEGER,
                final_config TEXT NOT NULL,
                config_sources TEXT NOT NULL,
                scenario_id VARCHAR(100),
                scenario_name VARCHAR(200),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_conversation_turn_configs_conversation_turn_id 
            ON conversation_turn_configs(conversation_turn_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_conversation_turn_configs_session_id 
            ON conversation_turn_configs(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_conversation_turn_configs_user_id 
            ON conversation_turn_configs(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_conversation_turn_configs_scenario_id 
            ON conversation_turn_configs(scenario_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_conversation_turn_configs_created_at 
            ON conversation_turn_configs(created_at)
        """)
        
        conn.commit()
        print("✓ Created conversation_turn_configs table and indexes")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
