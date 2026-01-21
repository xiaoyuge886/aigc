"""
Test Pydantic schemas
"""
import pytest
from pydantic import ValidationError

from models.schemas import (
    AgentRequest,
    SessionCreateRequest,
    ContentBlock,
    AssistantMessage,
    ResultInfo,
    SystemMessage,
    ErrorResponse,
)


class TestAgentRequest:
    """Test AgentRequest schema"""

    def test_valid_request(self):
        """Test creating valid request"""
        request = AgentRequest(
            prompt="Hello, Claude!",
            model="sonnet",
            stream=False
        )
        assert request.prompt == "Hello, Claude!"
        assert request.model == "sonnet"
        assert request.stream is False

    def test_request_with_defaults(self):
        """Test request with default values"""
        request = AgentRequest(prompt="Test")
        assert request.prompt == "Test"
        assert request.stream is False
        assert request.session_id is None
        assert request.system_prompt is None

    def test_invalid_request_empty_prompt(self):
        """Test that empty prompt fails validation"""
        with pytest.raises(ValidationError):
            AgentRequest(prompt="")


class TestSessionCreateRequest:
    """Test SessionCreateRequest schema"""

    def test_valid_session_request(self):
        """Test creating valid session request"""
        request = SessionCreateRequest(
            system_prompt="You are a helpful assistant",
            model="opus",
            allowed_tools=["Read", "Write"]
        )
        assert request.system_prompt == "You are a helpful assistant"
        assert request.model == "opus"
        assert request.allowed_tools == ["Read", "Write"]

    def test_session_request_with_defaults(self):
        """Test session request with defaults"""
        request = SessionCreateRequest()
        assert request.system_prompt is None
        assert request.model is None
        assert request.allowed_tools is None


class TestContentBlock:
    """Test ContentBlock schema"""

    def test_text_block(self):
        """Test text content block"""
        block = ContentBlock(
            type="text",
            text="Hello, world!"
        )
        assert block.type == "text"
        assert block.text == "Hello, world!"

    def test_tool_use_block(self):
        """Test tool use block"""
        block = ContentBlock(
            type="tool_use",
            tool_name="Read",
            tool_use_id="123",
            tool_input={"file_path": "/test.txt"}
        )
        assert block.type == "tool_use"
        assert block.tool_name == "Read"
        assert block.tool_input["file_path"] == "/test.txt"


class TestAssistantMessage:
    """Test AssistantMessage schema"""

    def test_valid_message(self):
        """Test creating valid assistant message"""
        message = AssistantMessage(
            content=[
                ContentBlock(type="text", text="Hello!")
            ],
            model="sonnet"
        )
        assert len(message.content) == 1
        assert message.content[0].text == "Hello!"
        assert message.model == "sonnet"


class TestResultInfo:
    """Test ResultInfo schema"""

    def test_success_result(self):
        """Test success result"""
        result = ResultInfo(
            subtype="success",
            is_error=False,
            duration_ms=1000,
            num_turns=3,
            session_id="test-123",
            result="Task completed successfully"
        )
        assert result.subtype == "success"
        assert result.is_error is False
        assert result.duration_ms == 1000
        assert result.num_turns == 3

    def test_error_result(self):
        """Test error result"""
        result = ResultInfo(
            subtype="error",
            is_error=True,
            duration_ms=500,
            num_turns=1,
            session_id="test-456",
            result="An error occurred"
        )
        assert result.subtype == "error"
        assert result.is_error is True
        assert result.result == "An error occurred"


class TestSystemMessage:
    """Test SystemMessage schema"""

    def test_system_message(self):
        """Test system message"""
        message = SystemMessage(
            subtype="tool_start",
            data={"tool_name": "Read", "file_path": "/test.txt"}
        )
        assert message.subtype == "tool_start"
        assert message.data["tool_name"] == "Read"


class TestErrorResponse:
    """Test ErrorResponse schema"""

    def test_error_response(self):
        """Test error response"""
        response = ErrorResponse(
            error="Session not found",
            detail="Session ID xxx does not exist",
            error_type="not_found"
        )
        assert response.error == "Session not found"
        assert response.detail == "Session ID xxx does not exist"
        assert response.error_type == "not_found"

    def test_minimal_error_response(self):
        """Test minimal error response"""
        response = ErrorResponse(error="Something went wrong")
        assert response.error == "Something went wrong"
        assert response.detail is None
        assert response.error_type is None
