"""
File reference parser for parsing file references in prompts
"""
import re
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class FileReference:
    """File reference object"""
    type: str  # "doc_id", "file_name", "search", "mention"
    value: str  # doc_id, file name, keywords, or mention text
    section: Optional[str] = None  # Subsection name (for doc_id type)
    original_mention: Optional[str] = None  # Original mention text (for replacement)


class FileReferenceParser:
    """Parse file references in prompts"""
    
    def parse_references(self, prompt: str) -> List[FileReference]:
        """
        Parse all file references in the prompt
        
        Supported formats:
        - [doc_id: user-upload-123-abc123]
        - [doc_id: user-upload-123-abc123, section: "市场分析"]
        - [file: 销售报告]
        - [search: 财务 报告]
        - @文件名 (mention format)
        
        Returns:
            List[FileReference] - List of file references
        """
        references = []
        
        # 1. Parse [doc_id: xxx] format
        doc_id_pattern = r'\[doc_id:\s*([^\]]+)\]'
        for match in re.finditer(doc_id_pattern, prompt):
            ref_str = match.group(1)
            ref = self._parse_doc_id_reference(ref_str)
            references.append(ref)
        
        # 2. Parse [file: xxx] format
        file_pattern = r'\[file:\s*([^\]]+)\]'
        for match in re.finditer(file_pattern, prompt):
            file_name = match.group(1).strip()
            references.append(FileReference(
                type="file_name",
                value=file_name,
                original_mention=match.group(0)
            ))
        
        # 3. Parse [search: xxx] format
        search_pattern = r'\[search:\s*([^\]]+)\]'
        for match in re.finditer(search_pattern, prompt):
            keywords = match.group(1).strip()
            references.append(FileReference(
                type="search",
                value=keywords,
                original_mention=match.group(0)
            ))
        
        # 4. Parse @mention format (simple: @文件名)
        mention_pattern = r'@([^\s@]+)'
        for match in re.finditer(mention_pattern, prompt):
            mention_text = match.group(1)
            # Skip if it's part of an email or URL
            if '@' in mention_text or '.' in mention_text and len(mention_text.split('.')) > 2:
                continue
            references.append(FileReference(
                type="mention",
                value=mention_text,
                original_mention=match.group(0)
            ))
        
        return references
    
    def _parse_doc_id_reference(self, ref_str: str) -> FileReference:
        """Parse doc_id reference (may include section parameter)"""
        parts = [p.strip() for p in ref_str.split(',')]
        doc_id = parts[0]
        
        section = None
        for part in parts[1:]:
            if 'section:' in part.lower():
                section = part.split(':', 1)[1].strip().strip('"\'')
        
        return FileReference(
            type="doc_id",
            value=doc_id,
            section=section,
            original_mention=f"[doc_id: {ref_str}]"
        )
