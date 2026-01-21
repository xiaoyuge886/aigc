"""
pytest configuration for shared tests.

This file is intentionally minimal - fixtures are inherited from
the parent tests/conftest.py which is automatically loaded by pytest.

Only add fixtures here if they are specific to the shared/ test module.
"""
# Fixtures from tests/conftest.py are automatically available via pytest's
# conftest discovery mechanism. No need to duplicate them here.
