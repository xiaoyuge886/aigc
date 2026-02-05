"""
File upload service for handling file uploads and integration with docs-management
"""
import base64
import hashlib
import mimetypes
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from loguru import logger

from core.config import settings
from services.database import DatabaseService

# Add docs-management scripts to path
DOCS_MGMT_SCRIPTS = Path(__file__).parent.parent.parent / ".claude" / "skills" / "docs-management" / "scripts"
if str(DOCS_MGMT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DOCS_MGMT_SCRIPTS))

# Try to import IndexManager (optional dependency)
try:
    from management.index_manager import IndexManager
    HAS_INDEX_MANAGER = True
except ImportError:
    logger.warning("IndexManager not available. Files will not be indexed for docs-management.")
    HAS_INDEX_MANAGER = False


class FileUploadService:
    """Service for handling file uploads"""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        # Base directory for user uploads - use project root's docs-management
        # Get project root (backend directory's parent)
        backend_dir = Path(__file__).parent.parent
        project_root = backend_dir.parent
        self.uploads_base_dir = project_root / ".claude" / "skills" / "docs-management" / "canonical" / "user-uploads"
        self.uploads_base_dir.mkdir(parents=True, exist_ok=True)

        # Initialize index manager if available
        self.index_manager = None
        if HAS_INDEX_MANAGER:
            try:
                canonical_dir = self.uploads_base_dir.parent
                self.index_manager = IndexManager(canonical_dir)
                logger.info(f"IndexManager initialized for {canonical_dir}")
            except Exception as e:
                logger.warning(f"Failed to initialize IndexManager: {e}")
    
    async def save_uploaded_file(
        self,
        file_data: bytes,
        file_name: str,
        user_id: int,
        session_id: Optional[str],  # 允许 None，可延迟绑定
        conversation_turn_id: str,  # 必需，提前生成
    ) -> Dict[str, Any]:
        """
        Save uploaded file and create relationship record
        
        Args:
            file_data: File content as bytes
            file_name: Original file name
            user_id: User ID who uploaded the file
            session_id: Session ID where file was uploaded (can be None for first conversation)
            conversation_turn_id: Conversation turn ID (required, should be generated early)
        
        Returns:
            Dict with doc_id, file_path, and relationship info
        
        Note:
            session_id can be None initially and will be bound later when available.
            conversation_turn_id is required and should be generated before calling this method.
        """
        try:
            # 1. Generate file hash for unique identification
            file_hash = hashlib.sha256(file_data).hexdigest()[:16]
            
            # 2. Generate doc_id
            doc_id = f"user-upload-{user_id}-{file_hash}"
            
            # 3. Determine file type
            file_type, _ = mimetypes.guess_type(file_name)
            if not file_type:
                file_type = "application/octet-stream"
            
            # 4. Create user-specific directory
            user_dir = self.uploads_base_dir / str(user_id)
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # 5. Save file (use doc_id as filename to avoid conflicts)
            file_extension = Path(file_name).suffix
            saved_file_name = f"{doc_id}{file_extension}"
            file_path = user_dir / saved_file_name
            
            file_path.write_bytes(file_data)
            logger.info(f"Saved uploaded file: {file_path} (size: {len(file_data)} bytes)")
            
            # 6. Create relationship record in database
            # Check if file already exists (same doc_id)
            existing_relationship = await self.db_service.get_file_relationship(doc_id)
            
            if existing_relationship:
                # File already exists, return existing relationship
                logger.info(f"File already exists with doc_id {doc_id}, returning existing relationship")
                return {
                    "doc_id": doc_id,
                    "file_path": str(file_path),
                    "file_name": existing_relationship.file_name,
                    "file_type": existing_relationship.file_type,
                    "file_size": existing_relationship.file_size,
                    "relationship_id": existing_relationship.id,
                    "is_existing": True,
                }
            
            # Create new relationship
            try:
                relationship = await self.db_service.create_file_relationship(
                    user_id=user_id,
                    session_id=session_id,
                    conversation_turn_id=conversation_turn_id,
                    doc_id=doc_id,
                    file_name=file_name,
                    file_type=file_type,
                    file_size=len(file_data),
                )
            except Exception as db_error:
                # If database insert fails but file exists, try to get existing relationship
                if "UNIQUE constraint" in str(db_error) or "duplicate" in str(db_error).lower():
                    logger.warning(f"Database constraint error, trying to get existing relationship for doc_id {doc_id}")
                    existing_relationship = await self.db_service.get_file_relationship(doc_id)
                    if existing_relationship:
                        logger.info(f"Found existing relationship for doc_id {doc_id}")
                        return {
                            "doc_id": doc_id,
                            "file_path": str(file_path),
                            "file_name": existing_relationship.file_name,
                            "file_type": existing_relationship.file_type,
                            "file_size": existing_relationship.file_size,
                            "relationship_id": existing_relationship.id,
                            "is_existing": True,
                        }
                # Re-raise if we can't recover
                raise
            
            # 7. Add to docs-management index
            if self.index_manager:
                try:
                    # Build relative path from canonical directory
                    relative_path = file_path.relative_to(self.uploads_base_dir.parent)

                    # Extract keywords from filename
                    keywords = self._extract_keywords_from_filename(file_name)

                    # Build metadata for index
                    metadata = {
                        "doc_id": doc_id,
                        "path": str(relative_path),
                        "title": file_name,
                        "description": f"User uploaded file ({file_type})",
                        "category": "user-upload",
                        "source_type": "upload",
                        "file_type": file_type,
                        "file_size": len(file_data),
                        "user_id": user_id,
                        "keywords": keywords,
                        "tags": self._generate_tags(file_type),
                        "uploaded_at": datetime.now(timezone.utc).isoformat(),
                        "hash": f"sha256:{file_hash}",
                        "session_id": session_id,
                        "conversation_turn_id": conversation_turn_id,
                    }

                    # Add to index
                    success = self.index_manager.update_entry(doc_id, metadata)
                    if success:
                        logger.info(f"Successfully added {doc_id} to docs-management index")
                    else:
                        logger.warning(f"Failed to add {doc_id} to docs-management index")
                except Exception as e:
                    # Don't fail the upload if indexing fails
                    logger.warning(f"Failed to index file {doc_id}: {e}")

            return {
                "doc_id": doc_id,
                "file_path": str(file_path),
                "file_name": file_name,
                "file_type": file_type,
                "file_size": len(file_data),
                "relationship_id": relationship.id,
                "is_existing": False,
            }
            
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}", exc_info=True)
            raise
    
    async def save_file_from_base64(
        self,
        base64_data: str,
        file_name: str,
        user_id: int,
        session_id: Optional[str],  # 允许 None，可延迟绑定
        conversation_turn_id: str,  # 必需，提前生成
    ) -> Dict[str, Any]:
        """
        Save file from base64 encoded data
        
        Args:
            base64_data: Base64 encoded file content
            file_name: Original file name
            user_id: User ID who uploaded the file
            session_id: Session ID where file was uploaded
            conversation_turn_id: Conversation turn ID (optional)
        
        Returns:
            Dict with doc_id, file_path, and relationship info
        """
        try:
            # Decode base64 data
            if ',' in base64_data:
                # Remove data URL prefix if present (e.g., "data:image/png;base64,...")
                base64_data = base64_data.split(',')[1]
            
            file_data = base64.b64decode(base64_data)
            return await self.save_uploaded_file(
                file_data=file_data,
                file_name=file_name,
                user_id=user_id,
                session_id=session_id,
                conversation_turn_id=conversation_turn_id,
            )
        except Exception as e:
            logger.error(f"Failed to decode and save base64 file: {e}", exc_info=True)
            raise

    def _extract_keywords_from_filename(self, filename: str) -> list:
        """Extract keywords from filename"""
        name_without_ext = Path(filename).stem
        parts = re.split(r'[-_\s]+', name_without_ext)

        stop_words = {'user', 'upload', 'file', 'document', 'the', 'a', 'an'}
        keywords = [p.lower() for p in parts if len(p) > 2 and p.lower() not in stop_words]

        return keywords[:10]  # Limit to 10 keywords

    def _generate_tags(self, file_type: str) -> list:
        """Generate tags based on file type"""
        tags = ["user-upload"]

        if "pdf" in file_type:
            tags.append("pdf")
        elif "image" in file_type or file_type.startswith("image/"):
            tags.append("image")
            if "png" in file_type:
                tags.append("png")
            elif "jpeg" in file_type or "jpg" in file_type:
                tags.append("jpg")
        elif "text" in file_type:
            tags.append("text")
        elif "markdown" in file_type:
            tags.append("markdown")

        return tags
