"""
Service for integrating uploaded files with docs-management index
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from loguru import logger

# Add docs-management scripts to path
DOCS_MGMT_SCRIPTS = Path(__file__).parent.parent.parent / ".claude" / "skills" / "docs-management" / "scripts"
if str(DOCS_MGMT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DOCS_MGMT_SCRIPTS))

try:
    from management.index_manager import IndexManager
    HAS_INDEX_MANAGER = True
except ImportError as e:
    logger.warning(f"Could not import IndexManager: {e}")
    HAS_INDEX_MANAGER = False


class DocsIndexService:
    """Service for managing uploaded files in docs-management index"""

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the docs index service

        Args:
            base_dir: Base directory for docs-management canonical storage
                     If None, uses default from work_dir config
        """
        if not HAS_INDEX_MANAGER:
            raise RuntimeError("IndexManager not available. Cannot use docs-index service")

        if base_dir is None:
            from core.config import settings
            base_dir = Path(settings.work_dir) / ".claude" / "skills" / "docs-management" / "canonical"

        self.index_manager = IndexManager(base_dir)
        self.canonical_dir = base_dir

    def add_uploaded_file_to_index(
        self,
        doc_id: str,
        file_name: str,
        file_path: str,
        file_type: str,
        file_size: int,
        user_id: int,
        keywords: Optional[list] = None,
        description: Optional[str] = None,
    ) -> bool:
        """
        Add uploaded file to docs-management index

        Args:
            doc_id: Unique document identifier (e.g., "user-upload-2-abc123")
            file_name: Original file name
            file_path: Absolute path to the file
            file_type: MIME type
            file_size: File size in bytes
            user_id: User ID who uploaded the file
            keywords: Optional list of keywords
            description: Optional description

        Returns:
            True if successfully added to index, False otherwise
        """
        try:
            # Generate relative path from canonical directory
            file_path_obj = Path(file_path)
            relative_path = file_path_obj.relative_to(self.canonical_dir)

            # Build metadata
            metadata = {
                "doc_id": doc_id,
                "path": str(relative_path),
                "title": file_name,
                "description": description or f"User uploaded file ({file_type})",
                "category": "user-upload",
                "source_type": "upload",
                "file_type": file_type,
                "file_size": file_size,
                "user_id": user_id,
                "keywords": keywords or self._extract_keywords_from_filename(file_name),
                "tags": self._generate_tags(file_type),
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "hash": f"sha256:{doc_id.split('-')[-1]}",  # Extract hash from doc_id
            }

            # Add to index
            success = self.index_manager.update_entry(doc_id, metadata)

            if success:
                logger.info(f"Successfully added {doc_id} to docs-management index")
                return True
            else:
                logger.error(f"Failed to add {doc_id} to docs-management index")
                return False

        except Exception as e:
            logger.error(f"Error adding file to index: {e}", exc_info=True)
            return False

    def _extract_keywords_from_filename(self, filename: str) -> list:
        """Extract keywords from filename"""
        # Remove extension and split by common separators
        name_without_ext = Path(filename).stem

        # Split by dash, underscore, space
        import re
        parts = re.split(r'[-_\s]+', name_without_ext)

        # Filter out common words and short parts
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

    def get_doc_from_index(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata from index

        Args:
            doc_id: Document ID

        Returns:
            Metadata dict if found, None otherwise
        """
        try:
            return self.index_manager.get_entry(doc_id)
        except Exception as e:
            logger.error(f"Error getting doc from index: {e}")
            return None

    def remove_doc_from_index(self, doc_id: str) -> bool:
        """
        Remove document from index

        Args:
            doc_id: Document ID

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.index_manager.remove_entry(doc_id)
        except Exception as e:
            logger.error(f"Error removing doc from index: {e}")
            return False

    def search_uploaded_files(self, user_id: Optional[int] = None) -> list:
        """
        Search for uploaded files in index

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of doc_ids matching the criteria
        """
        try:
            all_entries = self.index_manager.load_all()

            uploaded_files = []
            for doc_id, metadata in all_entries.items():
                if metadata.get("source_type") == "upload":
                    if user_id is None or metadata.get("user_id") == user_id:
                        uploaded_files.append(doc_id)

            return uploaded_files

        except Exception as e:
            logger.error(f"Error searching uploaded files: {e}")
            return []
