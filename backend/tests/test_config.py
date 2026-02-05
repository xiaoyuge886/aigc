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
    """Test get_agent_options method (production environment)"""
    monkeypatch.setenv("WORK_DIR", str(tmp_path))
    monkeypatch.setenv("SETTING_SOURCES", "project,builtin")
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
    assert options["setting_sources"] == ["project", "builtin"]


def test_get_debug_agent_options(monkeypatch, tmp_path):
    """Test get_debug_agent_options method (debug environment)"""
    debug_tmp_path = tmp_path / "debug"
    debug_tmp_path.mkdir()

    monkeypatch.setenv("DEBUG_WORK_DIR", str(debug_tmp_path))
    monkeypatch.setenv("DEBUG_SETTING_SOURCES", "project")
    monkeypatch.setenv("ONLINE_DEBUG_MAX_TURNS", "5")

    settings = Settings(
        default_model="sonnet",
        permission_mode="acceptEdits",
        max_turns=100,
        online_debug_max_turns=5
    )

    options = settings.get_debug_agent_options()
    assert options["model"] == "sonnet"
    assert options["permission_mode"] == "acceptEdits"
    assert options["max_turns"] == 5  # 使用调试环境的 max_turns
    assert options["cwd"] == str(debug_tmp_path)  # 使用调试环境的 cwd
    assert "Read" in options["allowed_tools"]
    assert options["setting_sources"] == ["project"]  # 使用调试环境的 setting_sources
