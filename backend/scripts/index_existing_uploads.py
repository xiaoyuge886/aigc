#!/usr/bin/env python3
"""
Script to index existing uploaded files into docs-management index
"""
import sys
from pathlib import Path

# Add current backend directory to path
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
sys.path.insert(0, str(backend_dir))

from services.docs_index_service import DocsIndexService
from services.database import DatabaseService
from core.config import settings
from loguru import logger


async def index_existing_uploads():
    """Index all existing uploaded files"""
    # Initialize services
    db_service = DatabaseService()
    index_service = DocsIndexService()

    # Get all file relationships from database
    from sqlalchemy import select
    from models.database import UserFileRelationshipDB

    async with db_service.get_session() as session:
        result = await session.execute(select(UserFileRelationshipDB))
        files = result.scalars().all()

    logger.info(f"Found {len(files)} uploaded files to index")

    success_count = 0
    failed_count = 0

    for file_rel in files:
        try:
            # Build file path
            upload_base_dir = Path(settings.work_dir) / ".claude" / "skills" / "docs-management" / "canonical" / "user-uploads"
            file_path = upload_base_dir / str(file_rel.user_id) / f"{file_rel.doc_id}{Path(file_rel.file_name).suffix}"

            # Check if file exists
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                failed_count += 1
                continue

            # Add to index
            success = index_service.add_uploaded_file_to_index(
                doc_id=file_rel.doc_id,
                file_name=file_rel.file_name,
                file_path=str(file_path),
                file_type=file_rel.file_type,
                file_size=file_rel.file_size or 0,
                user_id=file_rel.user_id,
                description=f"User uploaded file (session: {file_rel.session_id})",
            )

            if success:
                logger.info(f"✅ Indexed: {file_rel.doc_id}")
                success_count += 1
            else:
                logger.error(f"❌ Failed to index: {file_rel.doc_id}")
                failed_count += 1

        except Exception as e:
            logger.error(f"Error indexing {file_rel.doc_id}: {e}")
            failed_count += 1

    logger.info(f"\n{'='*50}")
    logger.info(f"Indexing complete:")
    logger.info(f"  ✅ Success: {success_count}")
    logger.info(f"  ❌ Failed: {failed_count}")
    logger.info(f"{'='*50}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(index_existing_uploads())
