#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for dev_mode.py - Development mode detection and path override.

These tests verify that:
1. is_dev_mode() correctly detects dev mode based on environment variable
2. get_effective_skill_dir() returns correct path in both modes
3. Mode info is correctly reported
4. Invalid paths are handled with clear errors
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))

from utils.dev_mode import (
    DEV_ROOT_ENV_VAR,
    is_dev_mode,
    get_effective_skill_dir,
    get_mode_info,
    format_shell_commands,
    _validate_skill_dir,
)


class TestValidateSkillDir:
    """Tests for _validate_skill_dir helper function."""

    def test_returns_false_for_nonexistent_path(self, tmp_path):
        """Non-existent path should return False."""
        nonexistent = tmp_path / "nonexistent"
        assert _validate_skill_dir(nonexistent) is False

    def test_returns_false_for_file(self, tmp_path):
        """File (not directory) should return False."""
        file_path = tmp_path / "somefile.txt"
        file_path.write_text("content")
        assert _validate_skill_dir(file_path) is False

    def test_returns_false_for_dir_without_skill_md(self, tmp_path):
        """Directory without SKILL.md should return False."""
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()
        assert _validate_skill_dir(empty_dir) is False

    def test_returns_true_for_valid_skill_dir(self, tmp_path):
        """Directory with SKILL.md should return True."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")
        assert _validate_skill_dir(skill_dir) is True


class TestIsDevMode:
    """Tests for is_dev_mode() function."""

    def test_returns_false_when_env_not_set(self, monkeypatch):
        """Should return False when env var is not set."""
        monkeypatch.delenv(DEV_ROOT_ENV_VAR, raising=False)
        assert is_dev_mode() is False

    def test_returns_false_when_env_is_empty(self, monkeypatch):
        """Should return False when env var is empty string."""
        monkeypatch.setenv(DEV_ROOT_ENV_VAR, "")
        assert is_dev_mode() is False

    def test_returns_false_when_env_is_whitespace(self, monkeypatch):
        """Should return False when env var is whitespace."""
        monkeypatch.setenv(DEV_ROOT_ENV_VAR, "   ")
        assert is_dev_mode() is False

    def test_returns_false_when_path_not_exists(self, monkeypatch, tmp_path):
        """Should return False when env var path doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(nonexistent))
        assert is_dev_mode() is False

    def test_returns_false_when_path_missing_skill_md(self, monkeypatch, tmp_path):
        """Should return False when env var path exists but lacks SKILL.md."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(empty_dir))
        assert is_dev_mode() is False

    def test_returns_true_when_valid_skill_dir(self, monkeypatch, tmp_path):
        """Should return True when env var points to valid skill directory."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")
        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(skill_dir))
        assert is_dev_mode() is True


class TestGetEffectiveSkillDir:
    """Tests for get_effective_skill_dir() function."""

    def test_returns_fallback_when_env_not_set(self, monkeypatch, tmp_path):
        """Should return fallback when env var not set."""
        monkeypatch.delenv(DEV_ROOT_ENV_VAR, raising=False)
        fallback = tmp_path / "fallback"
        fallback.mkdir()
        result = get_effective_skill_dir(fallback)
        assert result == fallback.resolve()

    def test_returns_fallback_when_env_empty(self, monkeypatch, tmp_path):
        """Should return fallback when env var is empty."""
        monkeypatch.setenv(DEV_ROOT_ENV_VAR, "")
        fallback = tmp_path / "fallback"
        fallback.mkdir()
        result = get_effective_skill_dir(fallback)
        assert result == fallback.resolve()

    def test_returns_dev_root_when_valid(self, monkeypatch, tmp_path):
        """Should return dev root when env var points to valid skill dir."""
        dev_root = tmp_path / "dev"
        dev_root.mkdir()
        (dev_root / "SKILL.md").write_text("# Skill")

        fallback = tmp_path / "fallback"
        fallback.mkdir()

        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(dev_root))
        result = get_effective_skill_dir(fallback)
        assert result == dev_root.resolve()

    def test_raises_when_path_not_exists(self, monkeypatch, tmp_path):
        """Should raise ValueError when env var path doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        fallback = tmp_path / "fallback"
        fallback.mkdir()

        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(nonexistent))
        with pytest.raises(ValueError, match="does not exist"):
            get_effective_skill_dir(fallback)

    def test_raises_when_path_not_directory(self, monkeypatch, tmp_path):
        """Should raise ValueError when env var path is a file."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        fallback = tmp_path / "fallback"
        fallback.mkdir()

        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(file_path))
        with pytest.raises(ValueError, match="not a directory"):
            get_effective_skill_dir(fallback)

    def test_raises_when_missing_skill_md(self, monkeypatch, tmp_path):
        """Should raise ValueError when env var path lacks SKILL.md."""
        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()
        fallback = tmp_path / "fallback"
        fallback.mkdir()

        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(invalid_dir))
        with pytest.raises(ValueError, match="missing SKILL.md"):
            get_effective_skill_dir(fallback)

    def test_resolves_to_absolute_path(self, monkeypatch, tmp_path):
        """Should always return absolute path."""
        dev_root = tmp_path / "dev"
        dev_root.mkdir()
        (dev_root / "SKILL.md").write_text("# Skill")

        fallback = tmp_path / "fallback"

        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(dev_root))
        result = get_effective_skill_dir(fallback)
        assert result.is_absolute()


class TestGetModeInfo:
    """Tests for get_mode_info() function."""

    def test_prod_mode_without_env(self, monkeypatch, tmp_path):
        """Should report prod mode when env var not set."""
        monkeypatch.delenv(DEV_ROOT_ENV_VAR, raising=False)
        fallback = tmp_path / "fallback"
        fallback.mkdir()

        info = get_mode_info(fallback)
        assert info.is_dev is False
        assert info.source == "fallback"
        assert info.env_var_value is None

    def test_dev_mode_with_valid_path(self, monkeypatch, tmp_path):
        """Should report dev mode with valid env var."""
        dev_root = tmp_path / "dev"
        dev_root.mkdir()
        (dev_root / "SKILL.md").write_text("# Skill")

        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(dev_root))
        info = get_mode_info()

        assert info.is_dev is True
        assert info.skill_dir == dev_root.resolve()
        assert info.source == "env_var"
        assert info.env_var_value == str(dev_root)

    def test_reports_invalid_env_value(self, monkeypatch, tmp_path):
        """Should report invalid env var value but still fallback."""
        invalid_path = tmp_path / "invalid"
        fallback = tmp_path / "fallback"
        fallback.mkdir()

        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(invalid_path))
        info = get_mode_info(fallback)

        assert info.is_dev is False
        assert info.source == "fallback"
        assert info.env_var_value == str(invalid_path)  # Reports the invalid value


class TestFormatShellCommands:
    """Tests for format_shell_commands() function."""

    def test_generates_powershell_commands(self, tmp_path):
        """Should generate valid PowerShell commands."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()

        commands = format_shell_commands(skill_dir)

        assert "powershell" in commands
        assert DEV_ROOT_ENV_VAR in commands["powershell"]
        assert "$env:" in commands["powershell"]

        assert "powershell_unset" in commands
        assert "Remove-Item" in commands["powershell_unset"]

    def test_generates_bash_commands(self, tmp_path):
        """Should generate valid Bash commands."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()

        commands = format_shell_commands(skill_dir)

        assert "bash" in commands
        assert DEV_ROOT_ENV_VAR in commands["bash"]
        assert "export" in commands["bash"]

        assert "bash_unset" in commands
        assert "unset" in commands["bash_unset"]

    def test_generates_cmd_commands(self, tmp_path):
        """Should generate valid CMD commands."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()

        commands = format_shell_commands(skill_dir)

        assert "cmd" in commands
        assert DEV_ROOT_ENV_VAR in commands["cmd"]
        assert "set " in commands["cmd"]

    def test_uses_absolute_path(self, tmp_path):
        """Commands should use absolute path."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()

        commands = format_shell_commands(skill_dir)

        # The path in the command should be the resolved absolute path
        expected_path = str(skill_dir.resolve())
        assert expected_path in commands["bash"]


class TestModeBannerIntegration:
    """Integration tests for mode banner output."""

    def test_banner_output_prod_mode(self, monkeypatch):
        """Mode banner should indicate prod mode when env not set."""
        import logging
        from utils.dev_mode import print_mode_banner

        # Use a logger to capture output (more reliable than capsys with UTF-8 reconfiguration)
        logger = logging.getLogger("test_banner_prod")
        logger.setLevel(logging.INFO)
        log_messages = []
        handler = logging.Handler()
        handler.emit = lambda record: log_messages.append(record.getMessage())
        logger.addHandler(handler)

        monkeypatch.delenv(DEV_ROOT_ENV_VAR, raising=False)
        print_mode_banner(logger)

        output = "\n".join(log_messages)
        assert "[PROD MODE]" in output

    def test_banner_output_dev_mode(self, monkeypatch, tmp_path):
        """Mode banner should indicate dev mode when valid env set."""
        import logging
        from utils.dev_mode import print_mode_banner

        logger = logging.getLogger("test_banner_dev")
        logger.setLevel(logging.INFO)
        log_messages = []
        handler = logging.Handler()
        handler.emit = lambda record: log_messages.append(record.getMessage())
        logger.addHandler(handler)

        dev_root = tmp_path / "dev"
        dev_root.mkdir()
        (dev_root / "SKILL.md").write_text("# Skill")

        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(dev_root))
        print_mode_banner(logger)

        output = "\n".join(log_messages)
        assert "[DEV MODE]" in output
        assert str(dev_root.resolve()) in output

    def test_banner_output_invalid_env(self, monkeypatch, tmp_path):
        """Mode banner should warn about invalid env var."""
        import logging
        from utils.dev_mode import print_mode_banner

        logger = logging.getLogger("test_banner_invalid")
        logger.setLevel(logging.INFO)
        log_messages = []
        handler = logging.Handler()
        handler.emit = lambda record: log_messages.append(record.getMessage())
        logger.addHandler(handler)

        invalid_path = tmp_path / "invalid"
        monkeypatch.setenv(DEV_ROOT_ENV_VAR, str(invalid_path))
        print_mode_banner(logger)

        output = "\n".join(log_messages)
        assert "[WARNING]" in output
        assert "invalid" in output.lower()
