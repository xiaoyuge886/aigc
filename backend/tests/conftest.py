"""
Pytest configuration and fixtures
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import settings
from services.agent_service import AgentService
from services.session_manager import SessionManager


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def agent_service():
    """Get agent service instance"""
    service = AgentService()
    yield service
    # Cleanup if needed


@pytest.fixture
async def session_manager():
    """Get session manager instance"""
    mgr = SessionManager(max_sessions=10, timeout_seconds=60)
    await mgr.start()
    yield mgr
    await mgr.stop()


@pytest.fixture
def mock_options():
    """Mock ClaudeAgentOptions for testing"""
    from claude_agent_sdk import ClaudeAgentOptions

    return ClaudeAgentOptions(
        allowed_tools=["Read", "Write"],
        permission_mode="plan",
        max_turns=5,
        model="haiku",
        cwd="/tmp"
    )


@pytest.fixture
def sample_prompt():
    """Sample prompt for testing"""
    return "Hello, this is a test prompt."
