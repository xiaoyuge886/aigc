"""
Example custom tools using Claude Agent SDK @tool decorator

You can add your own custom tools here following the same pattern.
"""
from typing import Any, Optional
from datetime import datetime
import json
import httpx

from claude_agent_sdk import tool, create_sdk_mcp_server
from services.sqlite_query_service import get_sqlite_query_service
from tools.enhanced_todo_tool import enhanced_todo_write, todo_statistics
from tools.tavily_search import tavily_search


@tool("get_current_time", "Get the current date and time", {})
async def get_current_time(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get the current date and time in ISO format.

    Returns:
        dict with current time in multiple formats
    """
    now = datetime.now()

    return {
        "content": [{
            "type": "text",
            "text": f"Current time: {now.isoformat()}\n"
                   f"Formatted: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                   f"Timestamp: {now.timestamp()}"
        }]
    }


@tool("calculate", "Perform basic mathematical calculations", {
    "expression": str,
    "operation": str  # add, subtract, multiply, divide
})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    """
    Perform basic math calculations safely.

    Args:
        expression: Math expression to evaluate (e.g., "2 + 2")
        operation: Operation type (add, subtract, multiply, divide)

    Returns:
        dict with calculation result
    """
    try:
        expr = args.get("expression", "")
        op = args.get("operation", "eval")

        # Safe evaluation with basic math only
        allowed_names = {
            "abs": abs,
            "min": min,
            "max": max,
            "pow": pow,
            "round": round,
        }

        # Basic arithmetic evaluation (safe)
        result = eval(expr, {"__builtins__": {}}, allowed_names)

        return {
            "content": [{
                "type": "text",
                "text": f"Calculation result: {expr} = {result}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Calculation error: {str(e)}"
            }],
            "is_error": True
        }


@tool("string_operations", "Perform string manipulation operations", {
    "text": str,
    "operation": str,  # upper, lower, title, reverse, length
    "count": str  # optional character to count
})
async def string_operations(args: dict[str, Any]) -> dict[str, Any]:
    """
    Perform various string operations.

    Args:
        text: The input string
        operation: Operation to perform (upper, lower, title, reverse, length, count)
        count: Character to count (for count operation)

    Returns:
        dict with operation result
    """
    text = args.get("text", "")
    operation = args.get("operation", "identity").lower()

    try:
        result_map = {
            "upper": text.upper(),
            "lower": text.lower(),
            "title": text.title(),
            "reverse": text[::-1],
            "length": str(len(text)),
        }

        if operation == "count" and "count" in args:
            char = args["count"]
            result = f"Character '{char}' appears {text.count(char)} times"
        else:
            result = result_map.get(operation, text)

        return {
            "content": [{
                "type": "text",
                "text": f"String operation '{operation}' on '{text}':\nResult: {result}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"String operation error: {str(e)}"
            }],
            "is_error": True
        }


@tool("get_system_info", "Get basic system information", {})
async def get_system_info(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get basic system information like Python version, platform, etc.

    Returns:
        dict with system information
    """
    import sys
    import platform

    info = [
        f"Python Version: {sys.version}",
        f"Platform: {platform.platform()}",
        f"Machine: {platform.machine()}",
        f"Processor: {platform.processor()}",
        f"Architecture: {platform.architecture()[0]}",
    ]

    return {
        "content": [{
            "type": "text",
            "text": "\n".join(info)
        }]
    }


@tool("sqlite_query", "Execute SQL query on SQLite database", {
    "query": str,
    "params": str  # JSON array of parameters
})
async def sqlite_query_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Execute SQL query on SQLite database

    Args:
        query: SQL query string
        params: Optional JSON array of query parameters

    Returns:
        dict with query results
    """
    try:
        query = args.get("query", "")
        params_json = args.get("params", "[]")

        # Parse parameters
        params = json.loads(params_json) if params_json else None
        if params and isinstance(params, list):
            params = tuple(params)

        # Execute query
        service = get_sqlite_query_service()
        result = service.execute_query(query, params)

        # Format results
        if not result:
            return {
                "content": [{
                    "type": "text",
                    "text": "Query executed successfully, no results returned."
                }]
            }

        # Format as table
        headers = list(result[0].keys())
        rows = []
        for row in result:
            rows.append([str(row.get(h, "")) for h in headers])

        # Create markdown table
        table_text = "| " + " | ".join(headers) + " |\n"
        table_text += "|" + "|".join(["---" for _ in headers]) + "|\n"
        for row in rows:
            table_text += "| " + " | ".join(row) + " |\n"

        return {
            "content": [{
                "type": "text",
                "text": f"Query Results ({len(result)} rows):\n\n{table_text}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Query error: {str(e)}"
            }],
            "is_error": True
        }


@tool("sqlite_get_tables", "Get all table names from SQLite database", {})
async def sqlite_get_tables(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get all table names from SQLite database

    Returns:
        dict with table list
    """
    try:
        service = get_sqlite_query_service()
        tables = service.get_tables()

        return {
            "content": [{
                "type": "text",
                "text": f"Database Tables ({len(tables)}):\n\n" + "\n".join(f"- {table}" for table in tables)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error getting tables: {str(e)}"
            }],
            "is_error": True
        }


@tool("sqlite_get_schema", "Get table schema from SQLite database", {
    "table_name": str
})
async def sqlite_get_schema(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get table schema from SQLite database

    Args:
        table_name: Name of the table

    Returns:
        dict with table schema
    """
    try:
        table_name = args.get("table_name", "")
        service = get_sqlite_query_service()
        schema = service.get_table_schema(table_name)

        # Format schema info
        schema_text = f"Table: {table_name}\n\n"
        schema_text += "| Column Name | Data Type | Nullable |\n"
        schema_text += "|-------------|-----------|----------|\n"
        for col in schema:
            schema_text += f"| {col['column_name']} | {col['data_type']} | {col['is_nullable']} |\n"

        return {
            "content": [{
                "type": "text",
                "text": schema_text
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error getting schema: {str(e)}"
            }],
            "is_error": True
        }


@tool("sqlite_test_connection", "Test SQLite database connection", {})
async def sqlite_test_connection(args: dict[str, Any]) -> dict[str, Any]:
    """
    Test SQLite database connection

    Returns:
        dict with test results
    """
    try:
        service = get_sqlite_query_service()
        result = service.test_connection()

        if result["status"] == "success":
            text = f"✅ SQLite Connection Successful\n\n"
            text += f"Database: {result['db_path']}\n"
            text += f"Tables: {result['tables_count']}\n\n"
            text += "Table Statistics:\n"
            for stat in result.get("table_stats", []):
                text += f"  - {stat['table_name']}: {stat['row_count']} rows\n"
        else:
            text = f"❌ Connection Failed\n\nError: {result.get('error', 'Unknown error')}"

        return {
            "content": [{
                "type": "text",
                "text": text
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Connection test error: {str(e)}"
            }],
            "is_error": True
        }


@tool("water_institute_search", "Search water institute knowledge base for reports and research", {
    "query": str
})
async def water_institute_search(args: dict[str, Any]) -> dict[str, Any]:
    """
    Search the water institute knowledge base for reports, research, and documents.

    This tool searches a private knowledge base containing water resources reports,
    research papers, and technical documents from the water institute.

    Args:
        query: Search keywords or topic (e.g., "密云水库", "洪水预警", "水资源管理")

    Returns:
        dict with search results including document titles, excerpts, and metadata

    Example:
        Input: {"query": "密云水库"}
        Output: List of related documents about Miyun Reservoir
    """
    try:
        query = args.get("query", "").strip()

        if not query:
            return {
                "content": [{
                    "type": "text",
                    "text": "❌ Search query cannot be empty. Please provide a search keyword."
                }],
                "is_error": True
            }

        # Prepare request
        url = "http://192.168.1.20:8899/search"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {"q": query}

        # Make async HTTP request with timeout
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

            # Check if request was successful
            if response.status_code != 200:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"❌ Knowledge base search failed with status code {response.status_code}\n\n"
                               f"Please check if the knowledge base service is running at {url}"
                    }],
                    "is_error": True
                }

            # Parse JSON response
            data = response.json()

            # Extract results from response (API returns {organic: [...], totalResults: ..., ...})
            results = data.get("organic", [])
            total_results = data.get("totalResults", 0)
            search_time = data.get("took", 0)

            # Format results
            if not results or len(results) == 0:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"📚 Knowledge Base Search Results\n\n"
                               f"Query: {query}\n\n"
                               f"No results found. Try different keywords."
                    }]
                }

            # Build formatted response
            text = f"📚 Water Institute Knowledge Base Search Results\n\n"
            text += f"🔍 Query: {query}\n"
            text += f"📊 Found: {total_results:,} total results (showing top {len(results)})\n"
            text += f"⏱️ Search time: {search_time/1000:.2f}s\n\n"

            # Format each result
            for idx, result in enumerate(results[:10], 1):  # Limit to top 10 results
                text += f"--- Result {idx} ---\n"

                # Add title if available
                if "title" in result and result["title"]:
                    text += f"📄 Title: {result['title']}\n"

                # Add link if available
                if "link" in result and result["link"]:
                    text += f"🔗 Link: {result['link']}\n"

                # Add snippet/content if available
                if "snippet" in result and result["snippet"]:
                    # Truncate long content
                    snippet = result["snippet"]
                    if len(snippet) > 500:
                        snippet = snippet[:500] + "..."
                    text += f"📝 Summary:\n{snippet}\n"

                text += "\n"

            # Add note if there are more results
            if len(results) < total_results:
                text += f"... and {total_results - len(results):,} more results\n"

            return {
                "content": [{
                    "type": "text",
                    "text": text
                }]
            }

    except httpx.TimeoutException:
        return {
            "content": [{
                "type": "text",
                "text": f"⏱️ Knowledge base search timeout\n\n"
                       f"The request to {url} timed out after 30 seconds.\n"
                       f"Please check if the service is running and accessible."
            }],
            "is_error": True
        }

    except httpx.ConnectError:
        return {
            "content": [{
                "type": "text",
                "text": f"🔌 Connection error\n\n"
                       f"Cannot connect to knowledge base service at {url}\n"
                       f"Please check:\n"
                       f"1. The service is running on 192.168.1.20:8899\n"
                       f"2. Network connectivity to 192.168.1.20\n"
                       f"3. Firewall settings"
            }],
            "is_error": True
        }

    except json.JSONDecodeError as e:
        return {
            "content": [{
                "type": "text",
                "text": f"📋 Response parsing error\n\n"
                       f"The knowledge base returned invalid JSON: {str(e)}\n"
                       f"Raw response: {response.text[:500]}"
            }],
            "is_error": True
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Knowledge base search error: {str(e)}"
            }],
            "is_error": True
        }


@tool("tavily_search", "Search the web using Tavily AI-powered search engine", {
    "query": str,
    "max_results": int,  # Optional, default 10, max 10
    "search_depth": str  # Optional, "basic" or "advanced" (default)
})
async def tavily_search_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Search the web using Tavily's AI-powered search engine.

    Tavily provides fast, accurate, and comprehensive search results optimized for AI agents.
    It's particularly good at finding recent information and understanding complex queries.

    Args:
        query: The search query (what you want to find)
        max_results: Maximum number of results to return (1-10, default 10)
        search_depth: Search depth - "basic" for fast results, "advanced" for comprehensive research

    Returns:
        dict with formatted search results including titles, URLs, snippets, and relevance scores

    Example:
        Input: {"query": "Python async await tutorial", "max_results": 5, "search_depth": "advanced"}
        Output: Top 5 relevant search results with titles, links, and content summaries
    """
    query = args.get("query", "").strip()
    max_results = args.get("max_results", 10)
    search_depth = args.get("search_depth", "advanced")

    if not query:
        return {
            "content": [{
                "type": "text",
                "text": "❌ Search query cannot be empty. Please provide a search query."
            }],
            "is_error": True
        }

    # Call the tavily_search function
    return await tavily_search(query, max_results, search_depth)


# Create the custom tools server
def get_custom_tools_server():
    """
    Get the MCP server with custom tools

    Returns:
        McpSdkServerConfig that can be passed to ClaudeAgentOptions
    """
    return create_sdk_mcp_server(
        name="custom_tools",
        version="1.0.0",
        tools=[
            get_current_time,
            calculate,
            string_operations,
            get_system_info,
            sqlite_query_tool,
            sqlite_get_tables,
            sqlite_get_schema,
            sqlite_test_connection,
            water_institute_search,
            tavily_search_tool,
            enhanced_todo_write,
            todo_statistics
        ]
    )


# Example: How to use custom tools in your agent
"""
from custom_tools import get_custom_tools_server

# In your agent_service.py or routes.py:

options = ClaudeAgentOptions(
    allowed_tools=[
        "Read", "Write", "Edit", "Bash",
        "mcp__custom_tools__get_current_time",
        "mcp__custom_tools__calculate",
        "mcp__custom_tools__string_operations",
        "mcp__custom_tools__get_system_info",
    ],
    mcp_servers={
        "custom_tools": get_custom_tools_server()
    }
)
"""
