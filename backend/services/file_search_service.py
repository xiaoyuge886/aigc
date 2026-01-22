"""
File search service for searching user-uploaded files
"""
from typing import List, Optional
from pathlib import Path

from loguru import logger

from services.database import DatabaseService
from models.database import UserFileRelationshipDB


class FileInfo:
    """File information object"""
    def __init__(self, relationship: UserFileRelationshipDB):
        self.doc_id = relationship.doc_id
        self.file_name = relationship.file_name
        self.file_type = relationship.file_type
        self.file_size = relationship.file_size
        self.uploaded_at = relationship.created_at
        self.relevance_score: float = 0.0  # For search results


class FileSearchService:
    """Service for searching user-uploaded files"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def search_by_keywords(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        keywords: List[str] = None,
        limit: int = 10
    ) -> List[FileInfo]:
        """
        Search files by keywords
        
        Strategy:
        1. Get user files from relationship table (fast)
        2. Filter by keywords in file names
        3. Return matching files
        
        Args:
            user_id: User ID
            session_id: Optional session ID to filter
            keywords: List of keywords to search
            limit: Maximum number of results
        
        Returns:
            List[FileInfo] - Matching files
        """
        # 1. Get user files
        relationships = await self.db_service.get_user_files(
            user_id=user_id,
            session_id=session_id,
            limit=1000  # Get all files for keyword matching
        )
        
        # 2. Filter by keywords
        if keywords:
            keywords_lower = [k.lower() for k in keywords]
            matched = []
            for rel in relationships:
                file_name_lower = rel.file_name.lower()
                # Check if any keyword matches
                if any(keyword in file_name_lower for keyword in keywords_lower):
                    file_info = FileInfo(rel)
                    # Calculate simple relevance score (number of matching keywords)
                    file_info.relevance_score = sum(
                        1 for keyword in keywords_lower if keyword in file_name_lower
                    ) / len(keywords_lower)
                    matched.append(file_info)
            
            # Sort by relevance score
            matched.sort(key=lambda x: x.relevance_score, reverse=True)
            return matched[:limit]
        else:
            # No keywords, return all files
            return [FileInfo(rel) for rel in relationships[:limit]]
    
    async def search_by_file_name(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        file_name: str = None,
        limit: int = 10
    ) -> List[FileInfo]:
        """Search files by file name (fuzzy match)"""
        relationships = await self.db_service.get_user_files(
            user_id=user_id,
            session_id=session_id,
            limit=1000
        )
        
        if not file_name:
            return [FileInfo(rel) for rel in relationships[:limit]]
        
        # Fuzzy match file name
        file_name_lower = file_name.lower()
        matched = [
            FileInfo(rel) for rel in relationships
            if file_name_lower in rel.file_name.lower()
        ]
        
        # Sort by match position (earlier match = higher relevance)
        matched.sort(key=lambda x: x.file_name.lower().find(file_name_lower))
        
        return matched[:limit]
    
    async def search_by_natural_language(
        self,
        user_id: int,
        session_id: Optional[str] = None,
        query: str = None,
        limit: int = 10
    ) -> List[FileInfo]:
        """
        Search files by natural language query
        
        For now, this is a simple implementation that extracts keywords
        and uses keyword search. In the future, this could be enhanced
        with NLP or integration with docs-management search.
        """
        if not query:
            return []
        
        # Extract keywords (simple: split by spaces)
        keywords = [k.strip() for k in query.split() if len(k.strip()) > 1]
        
        return await self.search_by_keywords(
            user_id=user_id,
            session_id=session_id,
            keywords=keywords,
            limit=limit
        )
    
    async def get_session_files(
        self,
        session_id: str,
        user_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[FileInfo]:
        """Get all files for a session"""
        relationships = await self.db_service.get_session_files(
            session_id=session_id,
            user_id=user_id,
            limit=limit,
        )
        return [FileInfo(rel) for rel in relationships]
