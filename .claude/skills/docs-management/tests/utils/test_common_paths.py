#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for common_paths module - centralized path resolution utilities."""

import sys
from pathlib import Path

# Standard test bootstrap
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))



class TestFindRepoRoot:
    """Test find_repo_root() function."""

    def test_finds_git_directory(self):
        """Should find .git directory when walking up from skill."""
        from utils.common_paths import find_repo_root

        repo_root = find_repo_root()

        assert repo_root.exists()
        assert (repo_root / '.git').exists()

    def test_returns_path_object(self):
        """Should return a Path object."""
        from utils.common_paths import find_repo_root

        result = find_repo_root()

        assert isinstance(result, Path)

    def test_accepts_start_path(self):
        """Should accept optional start path parameter."""
        from utils.common_paths import find_repo_root

        # Start from scripts directory
        scripts_dir = Path(__file__).resolve().parents[2] / 'scripts'
        result = find_repo_root(scripts_dir)

        assert result.exists()
        assert (result / '.git').exists()


class TestGetSkillDir:
    """Test get_skill_dir() function."""

    def test_returns_skill_directory(self):
        """Should return the docs-management skill directory."""
        from utils.common_paths import get_skill_dir

        skill_dir = get_skill_dir()

        assert skill_dir.exists()
        assert skill_dir.name == 'docs-management'
        assert (skill_dir / 'SKILL.md').exists()

    def test_returns_absolute_path(self):
        """Should return absolute path."""
        from utils.common_paths import get_skill_dir

        skill_dir = get_skill_dir()

        assert skill_dir.is_absolute()

    def test_accepts_from_path(self):
        """Should work when given explicit starting path."""
        from utils.common_paths import get_skill_dir

        test_file = Path(__file__).resolve()
        skill_dir = get_skill_dir(test_file)

        assert skill_dir.exists()
        assert (skill_dir / 'SKILL.md').exists()

    def test_contains_expected_subdirectories(self):
        """Skill directory should contain scripts/ and config/."""
        from utils.common_paths import get_skill_dir

        skill_dir = get_skill_dir()

        assert (skill_dir / 'scripts').exists()
        assert (skill_dir / 'config').exists()
        assert (skill_dir / 'canonical').exists()


class TestGetScriptsDir:
    """Test get_scripts_dir() function."""

    def test_returns_scripts_directory(self):
        """Should return the scripts directory."""
        from utils.common_paths import get_scripts_dir

        scripts_dir = get_scripts_dir()

        assert scripts_dir.exists()
        assert scripts_dir.name == 'scripts'

    def test_is_child_of_skill_dir(self):
        """scripts_dir should be child of skill_dir."""
        from utils.common_paths import get_skill_dir, get_scripts_dir

        skill_dir = get_skill_dir()
        scripts_dir = get_scripts_dir()

        assert scripts_dir.parent == skill_dir

    def test_contains_core_subdirectory(self):
        """Scripts directory should contain core/ subdirectory."""
        from utils.common_paths import get_scripts_dir

        scripts_dir = get_scripts_dir()

        assert (scripts_dir / 'core').exists()
        assert (scripts_dir / 'utils').exists()


class TestGetConfigDir:
    """Test get_config_dir() function."""

    def test_returns_config_directory(self):
        """Should return the config directory."""
        from utils.common_paths import get_config_dir

        config_dir = get_config_dir()

        assert config_dir.exists()
        assert config_dir.name == 'config'

    def test_is_child_of_skill_dir(self):
        """config_dir should be child of skill_dir."""
        from utils.common_paths import get_skill_dir, get_config_dir

        skill_dir = get_skill_dir()
        config_dir = get_config_dir()

        assert config_dir.parent == skill_dir

    def test_contains_yaml_configs(self):
        """Config directory should contain YAML config files."""
        from utils.common_paths import get_config_dir

        config_dir = get_config_dir()
        yaml_files = list(config_dir.glob('*.yaml'))

        assert len(yaml_files) > 0, "Expected YAML config files in config/"


class TestSetupPythonPath:
    """Test setup_python_path() function."""

    def test_returns_three_paths(self):
        """Should return tuple of (skill_dir, scripts_dir, config_dir)."""
        from utils.common_paths import setup_python_path

        result = setup_python_path()

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_all_paths_exist(self):
        """All returned paths should exist."""
        from utils.common_paths import setup_python_path

        skill_dir, scripts_dir, config_dir = setup_python_path()

        assert skill_dir.exists()
        assert scripts_dir.exists()
        assert config_dir.exists()

    def test_adds_paths_to_sys_path(self):
        """Should add scripts_dir and config_dir to sys.path."""
        from utils.common_paths import setup_python_path

        _, scripts_dir, config_dir = setup_python_path()

        assert str(scripts_dir) in sys.path
        assert str(config_dir) in sys.path

    def test_path_relationships(self):
        """scripts_dir and config_dir should be under skill_dir."""
        from utils.common_paths import setup_python_path

        skill_dir, scripts_dir, config_dir = setup_python_path()

        assert scripts_dir.parent == skill_dir
        assert config_dir.parent == skill_dir


class TestPathConfigIntegration:
    """Test integration with path_config module.

    Note: get_base_dir, get_index_path, get_temp_dir are in path_config,
    not re-exported from common_paths. This avoids circular imports.
    """

    def test_get_base_dir_exists(self):
        """get_base_dir should be importable from path_config and return valid path."""
        from utils.path_config import get_base_dir

        base_dir = get_base_dir()

        assert isinstance(base_dir, Path)

    def test_get_index_path_exists(self):
        """get_index_path should be importable from path_config and return valid path."""
        from utils.path_config import get_index_path

        index_path = get_index_path()

        assert isinstance(index_path, Path)
        assert index_path.name in ('index.yaml', 'index.json')

    def test_get_temp_dir_exists(self):
        """get_temp_dir should be importable from path_config."""
        from utils.path_config import get_temp_dir

        temp_dir = get_temp_dir()

        assert isinstance(temp_dir, Path)
