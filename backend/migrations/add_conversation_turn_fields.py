"""
Migration: Add conversation_turn_id and parent_message_id fields to messages table

This migration adds:
1. conversation_turn_id: For pairing user questions with AI responses
2. parent_message_id: For referencing parent messages (e.g., tool calls)
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
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(messages)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add conversation_turn_id column
        if "conversation_turn_id" not in columns:
            print("Adding conversation_turn_id column...")
            cursor.execute("""
                ALTER TABLE messages 
                ADD COLUMN conversation_turn_id VARCHAR(32)
            """)
            # Create index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS ix_messages_conversation_turn_id 
                ON messages(conversation_turn_id)
            """)
            print("✓ Added conversation_turn_id column and index")
        else:
            print("✓ conversation_turn_id column already exists")
        
        # Add parent_message_id column
        if "parent_message_id" not in columns:
            print("Adding parent_message_id column...")
            cursor.execute("""
                ALTER TABLE messages 
                ADD COLUMN parent_message_id INTEGER
            """)
            # Create index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS ix_messages_parent_message_id 
                ON messages(parent_message_id)
            """)
            # Add foreign key constraint (SQLite doesn't support adding FK after table creation,
            # but we can at least create the index)
            print("✓ Added parent_message_id column and index")
        else:
            print("✓ parent_message_id column already exists")
        
        # Update turn_number index if needed
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_messages_turn_number 
            ON messages(turn_number)
        """)
        
        conn.commit()
        print("✓ Migration completed successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())

