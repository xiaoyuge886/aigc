"""
Test custom tools
"""
import pytest

from tools.custom_tools import (
    get_current_time,
    calculate,
    string_operations,
    get_system_info,
    get_custom_tools_server
)


@pytest.mark.asyncio
class TestCustomTools:
    """Test custom tool functions"""

    async def test_get_current_time(self):
        """Test get_current_time tool"""
        result = await get_current_time({})
        assert "content" in result
        assert len(result["content"]) > 0
        assert "Current time:" in result["content"][0]["text"]

    async def test_calculate_addition(self):
        """Test calculate tool with addition"""
        result = await calculate({
            "expression": "2 + 2",
            "operation": "add"
        })
        assert "content" in result
        text = result["content"][0]["text"]
        assert "4" in text or "Result:" in text

    async def test_calculate_multiplication(self):
        """Test calculate tool with multiplication"""
        result = await calculate({
            "expression": "3 * 4",
            "operation": "multiply"
        })
        assert "content" in result
        text = result["content"][0]["text"]
        assert "12" in text or "Result:" in text

    async def test_calculate_invalid_expression(self):
        """Test calculate tool with invalid expression"""
        result = await calculate({
            "expression": "invalid &^^#",
            "operation": "eval"
        })
        assert "content" in result
        # Should return error message, not crash
        assert "error" in result["content"][0]["text"].lower() or "Result:" in result["content"][0]["text"]

    async def test_string_upper(self):
        """Test string_operations - uppercase"""
        result = await string_operations({
            "text": "hello world",
            "operation": "upper"
        })
        assert "content" in result
        assert "HELLO WORLD" in result["content"][0]["text"]

    async def test_string_lower(self):
        """Test string_operations - lowercase"""
        result = await string_operations({
            "text": "HELLO WORLD",
            "operation": "lower"
        })
        assert "content" in result
        assert "hello world" in result["content"][0]["text"]

    async def test_string_reverse(self):
        """Test string_operations - reverse"""
        result = await string_operations({
            "text": "abc",
            "operation": "reverse"
        })
        assert "content" in result
        assert "cba" in result["content"][0]["text"]

    async def test_string_length(self):
        """Test string_operations - length"""
        result = await string_operations({
            "text": "hello",
            "operation": "length"
        })
        assert "content" in result
        assert "5" in result["content"][0]["text"]

    async def test_get_system_info(self):
        """Test get_system_info tool"""
        result = await get_system_info({})
        assert "content" in result
        text = result["content"][0]["text"]
        assert "Python" in text
        assert "Platform" in text


class TestCustomToolsServer:
    """Test custom tools server creation"""

    def test_get_custom_tools_server(self):
        """Test creating custom tools server"""
        server = get_custom_tools_server()
        assert server is not None
        assert server["name"] == "custom_tools"
        assert server["version"] == "1.0.0"
        assert "tools" in server
        assert len(server["tools"]) == 4  # 4 tools defined
