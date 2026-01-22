"""
Migration: Add advanced parameters to business_scenarios table

Adds permission_mode, max_turns, and work_dir fields to support
more comprehensive Claude Agent SDK parameter coverage.
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text


async def upgrade():
    """Add new fields to business_scenarios table"""
    from services.database import DatabaseService
    db_service = DatabaseService()
    await db_service.initialize()
    
    async with db_service.async_session() as session:
        try:
            # Add permission_mode column
            await session.execute(text("""
                ALTER TABLE business_scenarios 
                ADD COLUMN permission_mode VARCHAR(50) NULL
            """))
            print("✅ Added permission_mode column")
            
            # Add max_turns column
            await session.execute(text("""
                ALTER TABLE business_scenarios 
                ADD COLUMN max_turns INTEGER NULL
            """))
            print("✅ Added max_turns column")
            
            # Add work_dir column
            await session.execute(text("""
                ALTER TABLE business_scenarios 
                ADD COLUMN work_dir VARCHAR(500) NULL
            """))
            print("✅ Added work_dir column")
            
            await session.commit()
            print("✅ Migration completed successfully")
        except Exception as e:
            await session.rollback()
            print(f"❌ Migration failed: {e}")
            raise


async def downgrade():
    """Remove new fields from business_scenarios table"""
    from services.database import DatabaseService
    db_service = DatabaseService()
    await db_service.initialize()
    
    async with db_service.async_session() as session:
        try:
            # Remove work_dir column
            await session.execute(text("""
                ALTER TABLE business_scenarios 
                DROP COLUMN work_dir
            """))
            print("✅ Removed work_dir column")
            
            # Remove max_turns column
            await session.execute(text("""
                ALTER TABLE business_scenarios 
                DROP COLUMN max_turns
            """))
            print("✅ Removed max_turns column")
            
            # Remove permission_mode column
            await session.execute(text("""
                ALTER TABLE business_scenarios 
                DROP COLUMN permission_mode
            """))
            print("✅ Removed permission_mode column")
            
            await session.commit()
            print("✅ Rollback completed successfully")
        except Exception as e:
            await session.rollback()
            print(f"❌ Rollback failed: {e}")
            raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        asyncio.run(downgrade())
    else:
        asyncio.run(upgrade())
