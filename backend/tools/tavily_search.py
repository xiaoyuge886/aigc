"""
Tavily 网络搜索工具
使用 Tavily API 进行高性能网络搜索
"""
from typing import Any
from loguru import logger
import os
from tavily import TavilyClient


def get_tavily_client() -> TavilyClient:
    """获取 Tavily 客户端"""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set in environment variables")
    return TavilyClient(api_key)


def format_search_results(response: dict) -> str:
    """格式化搜索结果为可读文本
    
    Args:
        response: Tavily API 响应
        
    Returns:
        格式化后的文本
    """
    formatted = f"🔍 搜索查询: {response.get('query', '')}\n"
    formatted += f"⏱️ 响应时间: {response.get('response_time', 0)}秒\n"
    formatted += f"📊 找到 {len(response.get('results', []))} 个结果\n\n"
    
    for idx, result in enumerate(response.get('results', []), 1):
        formatted += f"## {idx}. {result.get('title', '')}\n"
        formatted += f"**来源**: {result.get('url', '')}\n"
        formatted += f"**相关度**: {result.get('score', 0):.2%}\n\n"
        
        # 内容摘要（截取前500字符）
        content = result.get('content', '')
        if len(content) > 500:
            content = content[:500] + "..."
        formatted += f"{content}\n"
        formatted += "---\n\n"
    
    # 如果有后续问题建议
    if response.get('follow_up_questions'):
        formatted += "\n### 💡 相关问题建议\n"
        for q in response.get('follow_up_questions', [])[:3]:
            formatted += f"- {q}\n"
    
    return formatted


async def tavily_search(query: str, max_results: int = 10, search_depth: str = "advanced") -> dict[str, Any]:
    """
    使用 Tavily 进行网络搜索
    
    Args:
        query: 搜索查询字符串
        max_results: 最大返回结果数（默认10，最大10）
        search_depth: 搜索深度 "basic" 或 "advanced"（默认advanced）
        
    Returns:
        MCP 格式的响应字典
    """
    try:
        logger.info(f"[Tavily] Searching: {query}")
        
        client = get_tavily_client()
        
        # 执行搜索
        response = client.search(
            query=query,
            search_depth=search_depth,
            max_results=min(max_results, 10)  # Tavily 最多10条
        )
        
        logger.info(f"[Tavily] Found {len(response.get('results', []))} results in {response.get('response_time', 0)}s")
        
        # 格式化结果
        formatted_text = format_search_results(response)
        
        return {
            "content": [{
                "type": "text",
                "text": formatted_text
            }]
        }
        
    except ValueError as e:
        # 配置错误
        logger.error(f"[Tavily] Configuration error: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"⚠️ 搜索配置错误: {str(e)}\n请确保 TAVILY_API_KEY 已设置"
            }],
            "isError": True
        }
    except Exception as e:
        logger.error(f"[Tavily] Search error: {e}", exc_info=True)
        return {
            "content": [{
                "type": "text",
                "text": f"❌ 搜索失败: {str(e)}"
            }],
            "isError": True
        }
