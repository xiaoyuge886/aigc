"""
Shared test utilities for docs-management test suite.

Provides reusable fixtures, mocks, and helpers for testing scripts and utilities.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict


import yaml
import requests



class MockHTTPResponse:
    """Mock HTTP response for testing"""
    
    def __init__(self, status_code: int = 200, content: bytes = b"", text: str = "", 
                 headers: dict[str, str | None] = None):
        self.status_code = status_code
        self.content = content if content else text.encode('utf-8')
        self.text = text if text else content.decode('utf-8')
        self.headers = headers or {}
    
    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class MockSession:
    """Mock requests.Session for testing"""
    
    def __init__(self):
        self.headers = {}
        self._responses: dict[str, MockHTTPResponse] = {}
    
    def register_response(self, url: str, response: MockHTTPResponse):
        """Register a mock response for a URL"""
        self._responses[url] = response
    
    def get(self, url: str, **kwargs) -> MockHTTPResponse:
        """Mock GET request"""
        if url in self._responses:
            return self._responses[url]
        return MockHTTPResponse(status_code=404, text="Not Found")
    
    def head(self, url: str, **kwargs) -> MockHTTPResponse:
        """Mock HEAD request"""
        if url in self._responses:
            return self._responses[url]
        return MockHTTPResponse(status_code=404, text="")


class TempConfigDir:
    """Temporary configuration directory for testing.

    Supports both explicit cleanup and context manager usage:

        # Explicit cleanup (existing pattern)
        config_dir = TempConfigDir()
        try:
            # ... use config_dir ...
        finally:
            config_dir.cleanup()

        # Context manager (preferred pattern)
        with TempConfigDir() as config_dir:
            # ... use config_dir ...
            # cleanup is automatic
    """

    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_dir = self.temp_dir / "config"
        self.config_dir.mkdir()

    def __enter__(self):
        """Context manager entry - returns self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup unconditionally."""
        self.cleanup()
        return False  # Don't suppress exceptions

    def create_sources_json(self, sources: list) -> Path:
        """Create sources.json file"""
        sources_file = self.temp_dir / "sources.json"
        with open(sources_file, 'w', encoding='utf-8') as f:
            json.dump(sources, f, indent=2)
        return sources_file
    
    def create_filtering_yaml(self, filtering: dict) -> Path:
        """Create filtering.yaml file"""
        filtering_file = self.config_dir / "filtering.yaml"
        with open(filtering_file, 'w', encoding='utf-8') as f:
            yaml.dump(filtering, f)
        return filtering_file
    
    def create_tag_detection_yaml(self, tag_detection: dict) -> Path:
        """Create tag_detection.yaml file"""
        tag_file = self.config_dir / "tag_detection.yaml"
        with open(tag_file, 'w', encoding='utf-8') as f:
            yaml.dump(tag_detection, f)
        return tag_file
    
    def create_defaults_yaml(self, defaults: dict) -> Path:
        """Create defaults.yaml file"""
        defaults_file = self.config_dir / "defaults.yaml"
        with open(defaults_file, 'w', encoding='utf-8') as f:
            yaml.dump(defaults, f)
        return defaults_file
    
    def cleanup(self):
        """Clean up temporary directory"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TempReferencesDir:
    """Temporary references directory for testing.

    Supports both explicit cleanup and context manager usage:

        # Explicit cleanup (existing pattern)
        refs_dir = TempReferencesDir()
        try:
            # ... use refs_dir ...
        finally:
            refs_dir.cleanup()

        # Context manager (preferred pattern)
        with TempReferencesDir() as refs_dir:
            # ... use refs_dir ...
            # cleanup is automatic
    """

    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.references_dir = self.temp_dir / ".claude" / "skills" / "docs-management" / "canonical"
        self.references_dir.mkdir(parents=True)
        self.index_path = self.references_dir / "index.yaml"

    def __enter__(self):
        """Context manager entry - returns self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup unconditionally."""
        self.cleanup()
        return False  # Don't suppress exceptions

    def create_index(self, index: dict) -> Path:
        """Create index.yaml file"""
        with open(self.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(index, f)
        return self.index_path

    def create_doc(self, domain: str, category: str, filename: str, content: str) -> Path:
        """Create a documentation file"""
        doc_dir = self.references_dir / domain / category
        doc_dir.mkdir(parents=True, exist_ok=True)
        doc_file = doc_dir / filename
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return doc_file

    def cleanup(self):
        """Clean up temporary directory"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


def create_mock_sitemap(urls: list) -> str:
    """Create mock sitemap XML content"""
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f'  <url>\n    <loc>{url}</loc>\n  </url>\n'
    xml += '</urlset>'
    return xml


def create_mock_docs_map(urls: list) -> str:
    """Create mock docs map markdown content"""
    md = "# Documentation Map\n\n"
    for url in urls:
        md += f"- [{url}]({url})\n"
    return md


def create_mock_index_entry(doc_id: str, url: str, path: str, **kwargs) -> dict:
    """Create a mock index entry"""
    entry = {
        'doc_id': doc_id,
        'url': url,
        'path': path,
        'source_url': url,
        'last_fetched': '2025-01-01T00:00:00Z',
        'content_hash': 'abc123',
        **kwargs
    }
    return entry


def create_mock_frontmatter(**kwargs) -> str:
    """Create mock YAML frontmatter"""
    frontmatter = yaml.dump(kwargs, default_flow_style=False, sort_keys=False)
    return f"---\n{frontmatter}---\n"


def create_mock_doc_with_frontmatter(content: str, **frontmatter_kwargs) -> str:
    """Create mock document with frontmatter"""
    frontmatter = create_mock_frontmatter(**frontmatter_kwargs)
    return f"{frontmatter}\n{content}"


class MockIndexManager:
    """Mock IndexManager for testing"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.index_path = base_dir / "index.yaml"
        self._index: dict[str, Dict] = {}
    
    def load_all(self) -> dict[str, Dict]:
        """Load all index entries"""
        if self.index_path.exists():
            with open(self.index_path, 'r', encoding='utf-8') as f:
                self._index = yaml.safe_load(f) or {}
        return self._index
    
    def get_entry(self, doc_id: str) -> Dict | None:
        """Get a single entry"""
        return self._index.get(doc_id)
    
    def update_entry(self, doc_id: str, metadata: Dict):
        """Update an entry"""
        self._index[doc_id] = metadata
        self._save()
    
    def remove_entry(self, doc_id: str):
        """Remove an entry"""
        if doc_id in self._index:
            del self._index[doc_id]
            self._save()
    
    def _save(self):
        """Save index to file"""
        with open(self.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._index, f)


def patch_requests_session(monkeypatch, mock_responses: dict[str, MockHTTPResponse]):
    """Patch requests.Session with mock responses"""
    mock_session = MockSession()
    for url, response in mock_responses.items():
        mock_session.register_response(url, response)
    
    def mock_session_factory():
        return mock_session
    
    monkeypatch.setattr('requests.Session', mock_session_factory)
    return mock_session
