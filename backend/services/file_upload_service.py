"""
File upload service for handling file uploads and integration with docs-management
"""
import base64
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from loguru import logger

from core.config import settings
from services.database import DatabaseService


class FileUploadService:
    """Service for handling file uploads"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        # Base directory for user uploads (will be integrated with docs-management)
        self.uploads_base_dir = Path(settings.work_dir) / ".claude" / "skills" / "docs-management" / "canonical" / "user-uploads"
        self.uploads_base_dir.mkdir(parents=True, exist_ok=True)
    
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
            
            # 7. TODO: Add to docs-management index
            # This will be implemented when integrating with docs-management skill
            # For now, we just save the file and create the relationship
            
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
