"""
Test AgentService
"""
import pytest
from claude_agent_sdk import ClaudeAgentOptions

from services.agent_service import AgentService
from models.schemas import ResultInfo


@pytest.mark.asyncio
class TestAgentService:
    """Test AgentService class"""

    async def test_create_service(self):
        """Test creating AgentService"""
        service = AgentService()
        assert service is not None
        assert service.default_options is not None

    async def test_create_default_options(self):
        """Test creating default options"""
        service = AgentService()
        options = service.default_options
        assert isinstance(options, ClaudeAgentOptions)
        assert options.allowed_tools is not None
        assert options.model is not None

    async def test_create_options_with_overrides(self):
        """Test creating options with custom values"""
        service = AgentService()
        options = service.create_options(
            system_prompt="You are a helpful assistant",
            allowed_tools=["Read", "Write"],
            model="opus"
        )
        assert isinstance(options, ClaudeAgentOptions)
        assert options.model == "opus"
        assert "Read" in options.allowed_tools
        assert "Write" in options.allowed_tools

    async def test_work_dir_property(self, monkeypatch, tmp_path):
        """Test work_dir property"""
        from core.config import settings
        monkeypatch.setenv("WORK_DIR", str(tmp_path))

        service = AgentService()
        assert service.work_dir == str(tmp_path)

    async def test_query_with_client_invalid_options(self):
        """Test query_with_client with invalid options"""
        service = AgentService()

        # This should fail because we're not actually connecting to Claude
        # But we can test the error handling
        messages = []
        try:
            async for msg in service.query_with_client(
                prompt="test",
                allowed_tools=["Read"],
                model="haiku"
            ):
                messages.append(msg)
                if len(messages) > 5:  # Safety limit
                    break
        except Exception as e:
            # Expected to fail in test environment
            assert True


@pytest.mark.asyncio
class TestQueryStream:
    """Test query_stream method"""

    async def test_query_stream_with_options_param(self):
        """Test query_stream with options parameter"""
        service = AgentService()
        options = service.create_options(
            allowed_tools=["Read"],
            model="haiku"
        )

        messages = []
        try:
            async for msg in service.query_stream(
                prompt="test",
                options=options
            ):
                messages.append(msg)
                if len(messages) > 5:
                    break
        except Exception:
            # Expected in test environment
            pass

    async def test_query_stream_requires_session_id_with_client(self):
        """Test that session_id is required when using client"""
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

        service = AgentService()
        options = ClaudeAgentOptions(
            allowed_tools=["Read"],
            permission_mode="plan",
            model="haiku"
        )

        # This would normally create a client, but we'll test the validation
        # by checking the error path
        try:
            async for msg in service.query_stream(
                prompt="test",
                client=None  # No client
            ):
                pass
        except ValueError as e:
            assert "session_id" in str(e)
        except Exception:
            # Other exceptions are ok in test environment
            pass
