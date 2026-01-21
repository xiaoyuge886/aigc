"""
Tests for path_config module.

Note: path_config resolves relative paths from skill_dir (via bootstrap),
NOT from repo root. Tests must account for this.
"""
from pathlib import Path
from unittest.mock import patch

import scripts.bootstrap as bootstrap
from scripts.utils.path_config import get_base_dir, get_index_path, get_temp_dir


class TestPathConfig:
    """Test suite for path_config module."""

    def test_get_base_dir_uses_config_default(self, temp_dir):
        """Test that get_base_dir uses config default (relative to skill_dir)."""
        with patch('scripts.utils.path_config.get_default') as mock_get_default:
            # Return 'canonical' which is skill-relative
            mock_get_default.return_value = 'canonical'

            skill_dir = bootstrap.skill_dir
            expected = skill_dir / 'canonical'

            result = get_base_dir()

            assert result == expected.resolve()
            # Should call paths.base_dir with 'canonical' default
            mock_get_default.assert_called_with('paths', 'base_dir', 'canonical')

    def test_get_base_dir_with_custom_config(self, temp_dir):
        """Test that get_base_dir respects config value (relative to skill_dir)."""
        with patch('scripts.utils.path_config.get_default') as mock_get_default:
            mock_get_default.return_value = 'custom/references'

            skill_dir = bootstrap.skill_dir
            expected = skill_dir / 'custom/references'

            result = get_base_dir()

            assert result == expected.resolve()

    def test_get_base_dir_with_absolute_path(self, temp_dir):
        """Test that get_base_dir handles absolute paths."""
        with patch('scripts.utils.path_config.get_default') as mock_get_default:
            abs_path = Path('/absolute/path/references')
            mock_get_default.return_value = str(abs_path)
            
            result = get_base_dir()
            
            assert result == abs_path.resolve()

    def test_get_index_path_uses_config_default(self, temp_dir):
        """Test that get_index_path uses config default."""
        with patch('scripts.utils.path_config.get_default') as mock_get_default:
            # First call for paths.index_filename, second for filesystem fallback
            mock_get_default.side_effect = [
                'index.yaml',  # paths.index_filename
                'index.yaml'   # filesystem.default_index_filename (fallback check)
            ]
            
            base_dir = Path(temp_dir) / 'test_base'
            base_dir.mkdir(parents=True, exist_ok=True)
            
            result = get_index_path(base_dir)
            
            assert result == base_dir / 'index.yaml'
            # Should call paths.index_filename first
            assert mock_get_default.call_args_list[0] == (('paths', 'index_filename', 'index.yaml'),)

    def test_get_index_path_without_base_dir(self, temp_dir):
        """Test that get_index_path resolves base_dir if not provided."""
        with patch('scripts.utils.path_config.get_base_dir') as mock_get_base_dir:
            base_dir = Path(temp_dir) / 'test_base'
            base_dir.mkdir(parents=True, exist_ok=True)
            mock_get_base_dir.return_value = base_dir
            
            with patch('scripts.utils.path_config.get_default') as mock_get_default:
                mock_get_default.return_value = 'index.yaml'
                
                result = get_index_path()
                
                assert result == base_dir / 'index.yaml'

    def test_get_temp_dir_uses_config_default(self, temp_dir):
        """Test that get_temp_dir uses config default (relative to skill_dir)."""
        with patch('scripts.utils.path_config.get_default') as mock_get_default:
            # Return 'temp' which is skill-relative
            mock_get_default.return_value = 'temp'

            skill_dir = bootstrap.skill_dir
            expected = skill_dir / 'temp'

            result = get_temp_dir()

            assert result == expected.resolve()
            mock_get_default.assert_called_with('paths', 'temp_dir', 'temp')

    def test_get_temp_dir_with_custom_config(self, temp_dir):
        """Test that get_temp_dir respects config value (relative to skill_dir)."""
        with patch('scripts.utils.path_config.get_default') as mock_get_default:
            mock_get_default.return_value = 'custom/temp'

            skill_dir = bootstrap.skill_dir
            expected = skill_dir / 'custom/temp'

            result = get_temp_dir()

            assert result == expected.resolve()

    def test_path_config_legacy_conversion(self, temp_dir):
        """Test that path_config converts legacy repo-relative paths to skill-relative."""
        with patch('scripts.utils.path_config.get_default') as mock_get_default:
            # Legacy config used repo-relative paths like .claude/skills/docs-management/canonical
            # These should be converted to just 'canonical' (skill-relative)
            mock_get_default.return_value = '.claude/skills/docs-management/canonical'

            skill_dir = bootstrap.skill_dir
            # The code converts this to just 'canonical' then resolves from skill_dir
            expected = skill_dir / 'canonical'

            result = get_base_dir()

            assert result == expected.resolve()

    def test_path_config_integration(self, temp_dir):
        """Test that path_config functions work together (skill-relative)."""
        with patch('scripts.utils.path_config.get_default') as mock_get_default:
            mock_get_default.side_effect = lambda section, key, default: {
                ('paths', 'base_dir'): 'canonical',
                ('paths', 'index_filename'): 'index.yaml',
                ('paths', 'temp_dir'): 'temp',
            }.get((section, key), default)

            base_dir = get_base_dir()
            index_path = get_index_path(base_dir)
            temp_dir_path = get_temp_dir()

            skill_dir = bootstrap.skill_dir

            # base_dir should be skill_dir/canonical
            assert base_dir == (skill_dir / 'canonical').resolve()
            # index_path should be base_dir/index.yaml
            assert index_path == base_dir / 'index.yaml'
            # temp_dir should be skill_dir/temp
            assert temp_dir_path == (skill_dir / 'temp').resolve()
