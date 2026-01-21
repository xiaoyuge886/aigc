"""
File intent detector for detecting file-related intents in user prompts
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class FileIntent:
    """File intent object"""
    type: str  # "reference", "file_query", "content_query", "none"
    confidence: float  # 0.0-1.0
    needs_search: bool  # Whether file search is needed


class FileIntentDetector:
    """Detect file-related intents in user prompts"""
    
    # File query keywords
    FILE_QUERY_KEYWORDS = [
        "上传", "文件", "文档", "报告", "附件",
        "之前", "历史", "找", "搜索", "查看",
        "有没有", "是否", "哪些"
    ]
    
    # File content query keywords
    FILE_CONTENT_KEYWORDS = [
        "内容", "说了什么", "包含", "分析", "总结",
        "部分", "章节", "段落", "数据", "信息"
    ]
    
    def detect_intent(self, prompt: str) -> FileIntent:
        """
        Detect file-related intent in the prompt
        
        Returns:
            FileIntent - Intent object
        """
        prompt_lower = prompt.lower()
        
        # 1. Check for explicit file reference format
        if re.search(r'\[(doc_id|file|search):', prompt):
            return FileIntent(
                type="reference",
                confidence=1.0,
                needs_search=False  # Reference format doesn't need search, just parse
            )
        
        # 2. Check for @mention format
        if re.search(r'@[^\s@]+', prompt):
            return FileIntent(
                type="reference",
                confidence=0.9,
                needs_search=True  # Need to search for file by name
            )
        
        # 3. Check for file query intent
        has_file_query = any(keyword in prompt_lower for keyword in self.FILE_QUERY_KEYWORDS)
        
        # 4. Check for file content query intent
        has_content_query = any(keyword in prompt_lower for keyword in self.FILE_CONTENT_KEYWORDS)
        
        if has_file_query and has_content_query:
            # Both file query and content query
            return FileIntent(
                type="content_query",
                confidence=0.8,
                needs_search=True
            )
        elif has_file_query:
            # Only file query
            return FileIntent(
                type="file_query",
                confidence=0.7,
                needs_search=True
            )
        elif has_content_query:
            # Only content query (might be asking about current context file)
            return FileIntent(
                type="content_query",
                confidence=0.6,
                needs_search=True
            )
        else:
            # No file-related intent
            return FileIntent(
                type="none",
                confidence=0.0,
                needs_search=False
            )
