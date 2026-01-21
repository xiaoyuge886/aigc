"""
Test configuration module
"""
import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from core.config import Settings


def test_default_settings():
    """Test default settings values"""
    settings = Settings()
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.debug is False
    assert settings.default_model == "sonnet"


def test_settings_from_env(monkeypatch):
    """Test loading settings from environment variables"""
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DEFAULT_MODEL", "opus")

    settings = Settings()
    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.debug is True
    assert settings.default_model == "opus"


def test_allowed_tools_list():
    """Test parsing allowed_tools into list"""
    settings = Settings(default_allowed_tools="Read,Write,Edit,Bash")
    assert settings.allowed_tools_list == ["Read", "Write", "Edit", "Bash"]


def test_allowed_tools_empty():
    """Test empty allowed_tools"""
    settings = Settings(default_allowed_tools="")
    assert settings.allowed_tools_list == []


def test_work_dir_property(monkeypatch, tmp_path):
    """Test work_dir from environment"""
    monkeypatch.setenv("WORK_DIR", str(tmp_path))
    settings = Settings()
    assert settings.work_dir == tmp_path


def test_get_agent_options(monkeypatch, tmp_path):
    """Test get_agent_options method"""
    monkeypatch.setenv("WORK_DIR", str(tmp_path))
    settings = Settings(
        default_model="haiku",
        permission_mode="plan",
        max_turns=10
    )

    options = settings.get_agent_options()
    assert options["model"] == "haiku"
    assert options["permission_mode"] == "plan"
    assert options["max_turns"] == 10
    assert options["cwd"] == str(tmp_path)
    assert "Read" in options["allowed_tools"]
