"""
Tests for cli_utils module.
"""
import argparse
from pathlib import Path
from unittest.mock import patch


import pytest
from scripts.utils.cli_utils import (
    add_base_dir_argument,
    resolve_base_dir_from_args,
    add_common_index_args,
)
from scripts.utils.common_paths import find_repo_root


class TestCLIUtils:
    """Test suite for cli_utils module."""

    def test_add_base_dir_argument(self):
        """Test that add_base_dir_argument adds argument to parser."""
        import scripts.bootstrap as bootstrap
        parser = argparse.ArgumentParser()

        with patch('scripts.utils.cli_utils.get_base_dir') as mock_get_base_dir,              patch('scripts.utils.cli_utils.get_skill_dir') as mock_get_skill_dir:
            skill_dir = bootstrap.skill_dir
            mock_get_skill_dir.return_value = skill_dir
            mock_get_base_dir.return_value = skill_dir / 'canonical'

            add_base_dir_argument(parser)

            args = parser.parse_args([])
            assert hasattr(args, 'base_dir')
            # Default should be just 'canonical' (relative to skill_dir)
            assert args.base_dir == 'canonical'

    def test_add_base_dir_argument_with_custom_help(self):
        """Test that add_base_dir_argument uses custom help text."""
        parser = argparse.ArgumentParser()
        
        with patch('scripts.utils.cli_utils.get_base_dir') as mock_get_base_dir:
            repo_root = find_repo_root()
            mock_get_base_dir.return_value = repo_root / '.claude/skills/docs-management/canonical'
            
            add_base_dir_argument(parser, help_text="Custom help text")
            
            # Check that help text is in parser description
            help_output = parser.format_help()
            assert "Custom help text" in help_output

    def test_resolve_base_dir_from_args_default(self):
        """Test that resolve_base_dir_from_args uses config default when default string provided."""
        import scripts.bootstrap as bootstrap
        parser = argparse.ArgumentParser()
        
        # Mock get_base_dir and get_skill_dir
        with patch('scripts.utils.cli_utils.get_base_dir') as mock_get_base_dir,              patch('scripts.utils.cli_utils.get_skill_dir') as mock_get_skill_dir:
            skill_dir = bootstrap.skill_dir
            expected = skill_dir / 'canonical'
            mock_get_skill_dir.return_value = skill_dir
            mock_get_base_dir.return_value = expected
            
            add_base_dir_argument(parser)
            args = parser.parse_args([])
            
            # Reset mock call count since add_base_dir_argument also calls it
            mock_get_base_dir.reset_mock()
            mock_get_base_dir.return_value = expected
            
            result = resolve_base_dir_from_args(args)
            
            assert result == expected.resolve()
            # Should be called in resolve_base_dir_from_args
            assert mock_get_base_dir.call_count >= 1

    def test_resolve_base_dir_from_args_custom_path(self):
        """Test that resolve_base_dir_from_args resolves custom path relative to skill_dir."""
        import scripts.bootstrap as bootstrap
        parser = argparse.ArgumentParser()
        add_base_dir_argument(parser)
        args = parser.parse_args(['--base-dir', 'custom/path'])

        # Custom relative paths are resolved from skill_dir (plugin-friendly)
        skill_dir = bootstrap.skill_dir
        expected = (skill_dir / 'custom/path').resolve()

        result = resolve_base_dir_from_args(args)

        assert result == expected

    def test_resolve_base_dir_from_args_absolute_path_outside_repo_raises(self):
        """Test that resolve_base_dir_from_args rejects paths outside skill dir and repo."""
        parser = argparse.ArgumentParser()
        add_base_dir_argument(parser)
        # D:\absolute\path\references is outside both skill dir and repository root
        abs_path = Path('D:/absolute/path/references')
        args = parser.parse_args(['--base-dir', str(abs_path)])

        # Path traversal protection: should reject paths outside skill dir and repo
        with pytest.raises(ValueError, match="Base directory must be within skill directory or repository"):
            resolve_base_dir_from_args(args)

    def test_add_common_index_args(self):
        """Test that add_common_index_args adds base_dir and optionally json."""
        parser = argparse.ArgumentParser()
        
        with patch('scripts.utils.cli_utils.get_base_dir') as mock_get_base_dir:
            repo_root = find_repo_root()
            mock_get_base_dir.return_value = repo_root / '.claude/skills/docs-management/canonical'
            
            add_common_index_args(parser, include_json=True)
            
            args = parser.parse_args([])
            assert hasattr(args, 'base_dir')
            assert hasattr(args, 'json')
            assert args.json is False

    def test_add_common_index_args_without_json(self):
        """Test that add_common_index_args doesn't add json when include_json=False."""
        parser = argparse.ArgumentParser()
        
        with patch('scripts.utils.cli_utils.get_base_dir') as mock_get_base_dir:
            repo_root = find_repo_root()
            mock_get_base_dir.return_value = repo_root / '.claude/skills/docs-management/canonical'
            
            add_common_index_args(parser, include_json=False)
            
            args = parser.parse_args([])
            assert hasattr(args, 'base_dir')
            assert not hasattr(args, 'json')
