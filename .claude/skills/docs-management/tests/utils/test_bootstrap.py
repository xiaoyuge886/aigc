#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for bootstrap module."""

import sys
from pathlib import Path

# Standard test bootstrap
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))


class TestBootstrap:
    """Test bootstrap module functionality."""

    def test_setup_returns_tuple_of_three_paths(self):
        """setup() should return (skill_dir, scripts_dir, config_dir)."""
        from bootstrap import setup
        result = setup()

        assert isinstance(result, tuple)
        assert len(result) == 3
        skill_dir, scripts_dir, config_dir = result
        assert isinstance(skill_dir, Path)
        assert isinstance(scripts_dir, Path)
        assert isinstance(config_dir, Path)

    def test_setup_paths_exist(self):
        """Returned paths should exist on disk."""
        from bootstrap import setup
        skill_dir, scripts_dir, config_dir = setup()

        assert skill_dir.exists(), f"skill_dir does not exist: {skill_dir}"
        assert scripts_dir.exists(), f"scripts_dir does not exist: {scripts_dir}"
        assert config_dir.exists(), f"config_dir does not exist: {config_dir}"

    def test_setup_paths_are_absolute(self):
        """Returned paths should be absolute."""
        from bootstrap import setup
        skill_dir, scripts_dir, config_dir = setup()

        assert skill_dir.is_absolute()
        assert scripts_dir.is_absolute()
        assert config_dir.is_absolute()

    def test_setup_path_relationships(self):
        """scripts_dir and config_dir should be children of skill_dir."""
        from bootstrap import setup
        skill_dir, scripts_dir, config_dir = setup()

        assert scripts_dir.parent == skill_dir
        assert config_dir.parent == skill_dir
        assert scripts_dir.name == 'scripts'
        assert config_dir.name == 'config'

    def test_module_level_exports(self):
        """Module should export skill_dir, scripts_dir, config_dir as attributes."""
        import bootstrap

        assert hasattr(bootstrap, 'skill_dir')
        assert hasattr(bootstrap, 'scripts_dir')
        assert hasattr(bootstrap, 'config_dir')
        assert isinstance(bootstrap.skill_dir, Path)
        assert isinstance(bootstrap.scripts_dir, Path)
        assert isinstance(bootstrap.config_dir, Path)

    def test_scripts_dir_in_sys_path(self):
        """After import, scripts_dir should be in sys.path."""
        import bootstrap

        assert str(bootstrap.scripts_dir) in sys.path

    def test_config_dir_in_sys_path(self):
        """After import, config_dir should be in sys.path."""
        import bootstrap

        assert str(bootstrap.config_dir) in sys.path

    def test_skill_dir_contains_skill_md(self):
        """skill_dir should contain SKILL.md marker file."""
        from bootstrap import setup
        skill_dir, _, _ = setup()

        assert (skill_dir / 'SKILL.md').exists()

    def test_idempotent_setup(self):
        """Multiple setup() calls should not add MORE sys.path entries."""
        from bootstrap import setup

        # Get initial counts
        _, scripts_dir, config_dir = setup()
        initial_scripts_count = sys.path.count(str(scripts_dir))
        initial_config_count = sys.path.count(str(config_dir))

        # Call setup multiple times
        setup()
        setup()
        setup()

        # Count should not increase
        final_scripts_count = sys.path.count(str(scripts_dir))
        final_config_count = sys.path.count(str(config_dir))

        assert final_scripts_count == initial_scripts_count, \
            f"scripts_dir count increased from {initial_scripts_count} to {final_scripts_count}"
        assert final_config_count == initial_config_count, \
            f"config_dir count increased from {initial_config_count} to {final_config_count}"
