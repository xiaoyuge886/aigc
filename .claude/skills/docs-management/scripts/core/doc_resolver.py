#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc_resolver.py - Resolve doc_id and keywords to file paths

Provides efficient resolution of documentation references:
- doc_id → file path (canonical or extract)
- keyword search → doc_ids
- alias resolution (for renamed docs)
- Category/tag filtering

Uses IndexManager for efficient large file handling.
Uses inverted index caching for O(1) keyword lookups.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import re
from typing import Any

# Default cache directory for inverted index persistence (kept for backward compatibility)
# NOTE: Cache paths are now instance-based (relative to base_dir) to prevent
# test isolation issues where tests with mock indices corrupt the real cache.
_DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".cache"
_DEFAULT_INVERTED_INDEX_CACHE = _DEFAULT_CACHE_DIR / "inverted_index.json"

# Import CacheManager for content hash-based cache validation
try:
    from utils.cache_manager import CacheManager
except ImportError:
    CacheManager = None  # Fallback to mtime-based validation if unavailable

from utils.metadata_utils import normalize_tags
from utils.script_utils import configure_utf8_output, EXIT_INDEX_ERROR, normalize_url_for_display
from utils.search_constants import (
    TITLE, DESCRIPTION, KEYWORD, TAG, IDENTIFIER,
    PENALTIES, COVERAGE, SUBSECTION, POSITIONAL
)


def _tokenize_text(value: str) -> list[str]:
    """Split text into alphanumeric tokens."""
    return re.findall(r'[a-z0-9]+', value.lower())


def _keyword_variants(keyword: str) -> set[str]:
    """Return normalized variants for a keyword (raw, normalized, singular)."""
    variants: set[str] = set()
    kw_lower = keyword.lower().strip()
    if not kw_lower:
        return variants

    variants.add(kw_lower)
    normalized = re.sub(r'[^a-z0-9]+', '', kw_lower)
    if normalized:
        variants.add(normalized)

    if kw_lower.endswith('s') and len(kw_lower) > 3:
        singular = kw_lower.rstrip('s')
        variants.add(singular)
        singular_norm = re.sub(r'[^a-z0-9]+', '', singular)
        if singular_norm:
            variants.add(singular_norm)

    return variants


def _build_identifier_tokens(doc_id: str, metadata: dict[str, Any]) -> set[str]:
    """Build a set of identifier tokens from doc_id and path/file names."""
    tokens: set[str] = set(filter(None, re.split(r'[-_/]+', doc_id.lower())))
    normalized_doc_id = re.sub(r'[^a-z0-9]+', '', doc_id.lower())
    if normalized_doc_id:
        tokens.add(normalized_doc_id)

    path_value = metadata.get('path', '')
    if path_value:
        try:
            path_obj = Path(path_value)
            stem = path_obj.stem.lower()
        except (TypeError, ValueError, OSError):
            stem = str(path_value).lower()

        tokens.update(filter(None, re.split(r'[\\/_-]+', stem)))
        normalized_stem = re.sub(r'[^a-z0-9]+', '', stem)
        if normalized_stem:
            tokens.add(normalized_stem)

    return {token for token in tokens if token}

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

# Optional: structured logging for search observability
# Logging is optional in doc_resolver since it's used as a library
try:
    from utils.logging_utils import get_or_setup_logger
    _logger = get_or_setup_logger(__file__, log_category="search")
except ImportError:
    _logger = None

try:
    from management.index_manager import IndexManager
    from utils.config_helpers import (
    get_domain_weight, get_query_stop_words, get_generic_verbs,
    get_generic_config_terms, get_natural_language_stop_words
)
    # Import extract_subsection for content extraction
    try:
        from management.extract_subsection import MarkdownExtractor
    except ImportError:
        MarkdownExtractor = None
except ImportError:
    print("❌ Error: Could not import helpers or index_manager")
    print("Make sure common_paths.py, index_manager.py, and config_helpers.py are available")
    sys.exit(EXIT_INDEX_ERROR)


class DocResolver:
    """Resolve doc_id and keywords to file paths using a cached index snapshot."""

    def __init__(self, base_dir: Path):
        """
        Initialize resolver

        Args:
            base_dir: Base directory containing index.yaml
        """
        self.base_dir = Path(base_dir)
        self.index_manager = IndexManager(self.base_dir)
        # Load index once per resolver instance so that search/related lookups
        # and doc_id resolution share the same in-memory snapshot instead of
        # repeatedly re-reading index.yaml.
        self._index: dict[str, dict] = self.index_manager.load_all() or {}
        self._alias_cache: dict[str, str] = {}  # alias -> doc_id cache

        # Inverted index for O(1) keyword lookup (built lazily on first search)
        self._inverted_index: dict[str, set[str]] | None = None
        self._tag_index: dict[str, set[str]] | None = None
        self._category_index: dict[str, set[str]] | None = None

        # Store index path for cache validation
        self._index_path = self.base_dir / "index.yaml"

        # Initialize CacheManager for hash-based validation (if available)
        self._cache_manager = CacheManager(self.base_dir) if CacheManager else None

        # Cache at skill root level (parent of canonical) - aligned with CacheManager
        # Both inverted_index.json and cache_version.json live in <skill>/.cache/
        self._cache_dir = self.base_dir.parent / ".cache"
        self._inverted_index_cache_path = self._cache_dir / "inverted_index.json"

    def _get_index_mtime(self) -> float:
        """Get modification time of index.yaml."""
        try:
            return self._index_path.stat().st_mtime
        except OSError:
            return 0.0

    def _is_cache_valid(self) -> bool:
        """Check if inverted index cache is valid.
        
        Uses content hash-based validation via CacheManager if available,
        falling back to mtime-based validation otherwise. Hash-based validation
        correctly handles git pull scenarios where mtime changes but content
        may or may not have changed.
        """
        # Use CacheManager for robust hash-based validation
        if self._cache_manager:
            return self._cache_manager.is_inverted_index_valid()
        
        # Fallback to mtime-based validation
        if not self._inverted_index_cache_path.exists():
            return False
        try:
            index_mtime = self._get_index_mtime()
            cache_mtime = self._inverted_index_cache_path.stat().st_mtime
            return cache_mtime > index_mtime
        except OSError:
            return False

    def _load_cached_index(self) -> bool:
        """
        Load inverted index from cache file.

        Returns:
            True if cache was loaded successfully, False otherwise.
        """
        try:
            with open(self._inverted_index_cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert lists back to sets
            self._inverted_index = {k: set(v) for k, v in data.get('inverted_index', {}).items()}
            self._tag_index = {k: set(v) for k, v in data.get('tag_index', {}).items()}
            self._category_index = {k: set(v) for k, v in data.get('category_index', {}).items()}

            if _logger:
                _logger.debug(
                    f"Loaded inverted index from cache: {len(self._inverted_index)} terms, "
                    f"{len(self._tag_index)} tags, {len(self._category_index)} categories"
                )
            return True
        except (json.JSONDecodeError, OSError, KeyError) as e:
            if _logger:
                _logger.warning(f"Failed to load inverted index cache: {e}")
            # Reset indexes on failure
            self._inverted_index = None
            self._tag_index = None
            self._category_index = None
            return False

    def _save_index_cache(self) -> None:
        """Save inverted index to cache file for persistence across sessions."""
        if self._inverted_index is None:
            return

        try:
            # Ensure cache directory exists
            self._cache_dir.mkdir(parents=True, exist_ok=True)

            # Convert sets to lists for JSON serialization
            data = {
                'inverted_index': {k: sorted(v) for k, v in self._inverted_index.items()},
                'tag_index': {k: sorted(v) for k, v in self._tag_index.items()},
                'category_index': {k: sorted(v) for k, v in self._category_index.items()},
            }

            # Write atomically (temp file + rename)
            # Retry logic for Windows where replace() can fail if file is in use
            import time as _time
            temp_cache = self._inverted_index_cache_path.with_suffix('.tmp')
            with open(temp_cache, 'w', encoding='utf-8') as f:
                json.dump(data, f, separators=(',', ':'))  # Compact JSON

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    temp_cache.replace(self._inverted_index_cache_path)
                    break
                except PermissionError:
                    if attempt < max_retries - 1:
                        _time.sleep(0.1)
                    else:
                        raise

            # Mark cache as built with CacheManager (stores content hash)
            if self._cache_manager:
                self._cache_manager.mark_inverted_index_built()

            if _logger:
                _logger.debug(f"Saved inverted index cache: {self._inverted_index_cache_path}")
        except OSError as e:
            if _logger:
                _logger.warning(f"Failed to save inverted index cache: {e}")
    
    def resolve_doc_id(self, doc_id: str, extract_path: str | None = None) -> Path | None:
        """
        Resolve doc_id to file path
        
        Args:
            doc_id: Document ID to resolve
            extract_path: Optional extract path (for skill extracts)
        
        Returns:
            Path to document, or None if not found
        """
        # Check alias cache first
        original_doc_id = doc_id
        if doc_id in self._alias_cache:
            doc_id = self._alias_cache[doc_id]
        
        # Get entry from index
        entry = self._index.get(doc_id)
        if not entry:
            # Try to find by alias (only if we haven't already resolved from cache)
            if doc_id == original_doc_id:
                resolved_doc_id = self._resolve_alias(doc_id)
                if resolved_doc_id and resolved_doc_id != doc_id:
                    doc_id = resolved_doc_id
                    entry = self.index_manager.get_entry(doc_id)
        
        if not entry:
            return None
        
        # If extract_path specified, return extract path (handle both relative and absolute)
        if extract_path:
            extract_path_obj = Path(extract_path)
            # Resolve relative paths
            if not extract_path_obj.is_absolute():
                extract_path_obj = extract_path_obj.resolve()
            if extract_path_obj.exists():
                return extract_path_obj
        
        # Return canonical path (normalize path separators for cross-platform)
        path_str = entry.get('path')
        if not path_str:
            return None
        
        # Normalize path separators (index stores forward slashes)
        path_str_normalized = str(path_str).replace('\\', '/')
        canonical_path = self.base_dir / path_str_normalized
        if canonical_path.exists():
            return canonical_path
        
        return None
    
    def _resolve_alias(self, alias: str) -> str | None:
        """
        Resolve alias to doc_id
        
        Args:
            alias: Alias to resolve
        
        Returns:
            doc_id if found, None otherwise
        """
        # Check cache first
        if alias in self._alias_cache:
            return self._alias_cache[alias]
        
        # Search through all entries for alias
        for doc_id, metadata in self._index.items():
            aliases = metadata.get('aliases', [])
            if isinstance(aliases, list) and alias in aliases:
                self._alias_cache[alias] = doc_id
                return doc_id
        
        return None

    def _build_inverted_index(self) -> None:
        """
        Build inverted indexes for O(1) keyword lookup.

        Creates:
        - _inverted_index: keyword/variant -> set of doc_ids
        - _tag_index: tag -> set of doc_ids
        - _category_index: category -> set of doc_ids

        This is called lazily on first search and cached for subsequent searches.
        Uses file-based caching to persist across script invocations.
        Provides 10-100x speedup by eliminating O(n) full index scans.
        """
        if self._inverted_index is not None:
            return  # Already built in this session

        import time
        start_time = time.time()

        # Try to load from disk cache first (much faster than rebuilding)
        if self._is_cache_valid() and self._load_cached_index():
            cache_time = time.time() - start_time
            if _logger:
                _logger.info(f"Loaded inverted index from cache ({cache_time*1000:.1f}ms)")
            return

        self._inverted_index = {}
        self._tag_index = {}
        self._category_index = {}

        for doc_id, metadata in self._index.items():
            # Index keywords and their variants
            doc_keywords = metadata.get('keywords', [])
            if isinstance(doc_keywords, str):
                doc_keywords = [doc_keywords]

            for kw in doc_keywords:
                kw_lower = kw.lower().strip()
                if not kw_lower:
                    continue

                # Add the keyword itself
                if kw_lower not in self._inverted_index:
                    self._inverted_index[kw_lower] = set()
                self._inverted_index[kw_lower].add(doc_id)

                # Add variants (normalized, singular)
                for variant in _keyword_variants(kw_lower):
                    if variant not in self._inverted_index:
                        self._inverted_index[variant] = set()
                    self._inverted_index[variant].add(doc_id)

                # Add tokens from keyword
                for token in _tokenize_text(kw_lower):
                    if token not in self._inverted_index:
                        self._inverted_index[token] = set()
                    self._inverted_index[token].add(doc_id)

            # Index title words
            title = metadata.get('title', '').lower()
            for token in _tokenize_text(title):
                if token not in self._inverted_index:
                    self._inverted_index[token] = set()
                self._inverted_index[token].add(doc_id)

            # Index description words
            description = metadata.get('description', '').lower()
            for token in _tokenize_text(description):
                if token not in self._inverted_index:
                    self._inverted_index[token] = set()
                self._inverted_index[token].add(doc_id)

            # Index tags
            doc_tags = metadata.get('tags', [])
            if isinstance(doc_tags, str):
                doc_tags = [doc_tags]
            for tag in doc_tags:
                tag_lower = tag.lower().strip()
                if tag_lower:
                    if tag_lower not in self._tag_index:
                        self._tag_index[tag_lower] = set()
                    self._tag_index[tag_lower].add(doc_id)

            # Index category (original field)
            category = metadata.get('category', '').lower().strip()
            if category:
                if category not in self._category_index:
                    self._category_index[category] = set()
                self._category_index[category].add(doc_id)

            # Index doc_map_category (hierarchical category from docs_map.md enrichment)
            doc_map_category = metadata.get('doc_map_category', '').lower().strip()
            if doc_map_category:
                if doc_map_category not in self._category_index:
                    self._category_index[doc_map_category] = set()
                self._category_index[doc_map_category].add(doc_id)

            # Index doc_id tokens (for identifier matching)
            for token in _tokenize_text(doc_id):
                if token not in self._inverted_index:
                    self._inverted_index[token] = set()
                self._inverted_index[token].add(doc_id)

        # Log inverted index build stats
        build_time = time.time() - start_time
        if _logger:
            _logger.info(
                f"Inverted index built: {len(self._inverted_index)} terms, "
                f"{len(self._tag_index)} tags, {len(self._category_index)} categories "
                f"({build_time*1000:.1f}ms)"
            )

        # Save to cache for future invocations
        self._save_index_cache()

    def _score_subsection_matches(
        self,
        subsections: list[dict],
        keyword_lower: list[str],
        has_substantive_match: bool,
        main_content_matches: int
    ) -> tuple[dict | None, int]:
        """
        Score subsection matches and find the best matching subsection.

        Args:
            subsections: List of subsection dicts from document metadata
            keyword_lower: Lowercased search keywords
            has_substantive_match: Whether any substantive (non-generic) keyword matched
            main_content_matches: Count of main content matches

        Returns:
            Tuple of (best_subsection dict or None, subsection_bonus score)
        """
        best_subsection = None
        best_subsection_score = 0
        subsection_bonus = 0

        for subsection in subsections:
            if not isinstance(subsection, dict):
                continue

            subsection_score = 0
            anchor = subsection.get('anchor', '')
            heading = subsection.get('heading', '').lower()

            # Score heading matches
            if all(kw in heading for kw in keyword_lower):
                subsection_score += SUBSECTION.all_kw_in_heading
                if has_substantive_match:
                    subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_all_substantive)
                elif main_content_matches > 0:
                    subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_all_main_content)
                else:
                    subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_all_default)
            else:
                for kw in keyword_lower:
                    if kw in heading:
                        subsection_score += SUBSECTION.single_kw_in_heading
                        if has_substantive_match:
                            subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_single_substantive)
                        elif main_content_matches > 0:
                            subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_single_main_content)
                        else:
                            subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_single_default)

            # Score subsection keyword matches
            sub_keywords = subsection.get('keywords', [])
            if isinstance(sub_keywords, list):
                sub_keywords_lower = [k.lower() for k in sub_keywords]
                if all(any(kw in skw or skw in kw for skw in sub_keywords_lower) for kw in keyword_lower):
                    subsection_score += SUBSECTION.all_kw_in_keywords
                    if has_substantive_match:
                        subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_kw_all_substantive)
                    elif main_content_matches > 0:
                        subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_kw_all_main_content)
                    else:
                        subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_kw_all_default)
                else:
                    for kw in keyword_lower:
                        if kw in sub_keywords_lower:
                            subsection_score += SUBSECTION.single_kw_in_keywords
                            if has_substantive_match:
                                subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_kw_single_substantive)
                            elif main_content_matches > 0:
                                subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_kw_single_main_content)
                            else:
                                subsection_bonus = max(subsection_bonus, SUBSECTION.bonus_kw_single_default)

            # Track best subsection
            if subsection_score > best_subsection_score:
                best_subsection_score = subsection_score
                best_subsection = {
                    'anchor': anchor,
                    'heading': subsection.get('heading', ''),
                    'score': subsection_score
                }

        return best_subsection, subsection_bonus

    def _get_candidate_doc_ids(self, keywords: list[str], category: str | None = None,
                                tags: list[str] | None = None) -> set[str]:
        """
        Get candidate doc_ids using inverted index for O(1) lookup.

        Args:
            keywords: List of search keywords
            category: Optional category filter
            tags: Optional tag filter

        Returns:
            Set of doc_ids that might match the search query
        """
        self._build_inverted_index()

        if not self._inverted_index:
            return set(self._index.keys())  # Fallback to full scan

        candidates = None

        # For each keyword, get matching doc_ids
        for kw in keywords:
            kw_lower = kw.lower().strip()
            if not kw_lower:
                continue

            # Collect all doc_ids matching this keyword or its variants/tokens
            kw_matches = set()

            # Direct match
            if kw_lower in self._inverted_index:
                kw_matches.update(self._inverted_index[kw_lower])

            # Variant matches
            for variant in _keyword_variants(kw_lower):
                if variant in self._inverted_index:
                    kw_matches.update(self._inverted_index[variant])

            # Token matches (for compound terms)
            # Only skip tokenization for true file-like terms (end with extension)
            # This allows "claude.md memory" to be tokenized while keeping "claude.md" atomic
            is_file_like = bool(re.match(r'^[a-z0-9_.-]+\.[a-z]{1,4}$', kw_lower))
            if not is_file_like:
                for token in _tokenize_text(kw_lower):
                    if token in self._inverted_index:
                        kw_matches.update(self._inverted_index[token])

            # Union all matches for this keyword
            if candidates is None:
                candidates = kw_matches
            else:
                # Use union to allow partial matches (any keyword match)
                candidates.update(kw_matches)

        if candidates is None:
            candidates = set()

        # Apply category filter
        if category and self._category_index:
            category_lower = category.lower().strip()
            if category_lower in self._category_index:
                candidates &= self._category_index[category_lower]
            else:
                candidates = set()  # Category doesn't exist

        # Apply tag filter
        if tags and self._tag_index:
            tag_matches = set()
            for tag in tags:
                if tag:
                    tag_lower = tag.lower().strip()
                    if tag_lower in self._tag_index:
                        tag_matches.update(self._tag_index[tag_lower])
            if tag_matches:
                candidates &= tag_matches
            else:
                candidates = set()  # No matching tags

        return candidates

    def search_by_keyword(self, keywords: list[str], category: str | None = None,
                         tags: list[str | None] = None, limit: int = 10,
                         return_scores: bool = False,
                         min_score: float | None = None) -> list[tuple[str, dict]]:
        """
        Search documents by keywords

        Args:
            keywords: List of keywords to search for
            category: Optional category filter
            tags: Optional tags filter
            limit: Maximum number of results
            return_scores: If True, include score in metadata['_score']
            min_score: If set, only return results with score >= this value

        Returns:
            List of (doc_id, metadata) tuples, sorted by relevance
        """
        import time
        search_start = time.time()

        results = []
        keyword_lower = [
            k.lower().strip() for k in keywords
            if isinstance(k, str) and k.strip()
        ]
        if not keyword_lower:
            return results

        # Filter out query stop words (e.g., "when", "how", "to", "best", "practices")
        # This transforms queries like "when to use subagents" → ["subagents"]
        query_stop_words = get_query_stop_words()
        original_keywords = keyword_lower.copy()
        keyword_lower = [kw for kw in keyword_lower if kw not in query_stop_words]

        # If ALL keywords were filtered, fall back to original (rare edge case)
        if not keyword_lower and original_keywords:
            keyword_lower = original_keywords
            if _logger:
                _logger.debug(f"All keywords were stop words, using original: {original_keywords}")

        keyword_variants = {kw: _keyword_variants(kw) for kw in keyword_lower}
        # For file-like terms (containing '.'), don't tokenize - treat as atomic
        # This prevents 'claude.md' from matching via 'claude' token in doc_ids
        keyword_tokens = {
            kw: set() if '.' in kw else (set(_tokenize_text(kw)) or {kw})
            for kw in keyword_lower
        }

        # Load generic verbs from config (with fallback defaults)
        generic_verbs = get_generic_verbs() or {'create', 'use', 'get', 'add', 'remove', 'update', 'delete', 'set', 'configure', 'run', 'build', 'make', 'do'}

        # Use inverted index to get candidate doc_ids (O(1) lookup vs O(n) full scan)
        # This provides 10-100x speedup for typical queries
        candidate_doc_ids = self._get_candidate_doc_ids(keyword_lower, category, tags)

        for doc_id in candidate_doc_ids:
            metadata = self._index.get(doc_id)
            if not metadata:
                continue

            # Category/tag filters already applied by _get_candidate_doc_ids
            # But we still need the tag set for scoring
            doc_tags = metadata.get('tags', [])
            if isinstance(doc_tags, str):
                doc_tags = [doc_tags]
            doc_tags_lower = [t.lower() for t in doc_tags]
            doc_tag_set = set(doc_tags_lower)

            doc_keywords = metadata.get('keywords', [])
            if isinstance(doc_keywords, str):
                doc_keywords = [doc_keywords]
            doc_keywords_lower = [k.lower() for k in doc_keywords]
            # Include index for positional scoring (earlier keywords = higher priority)
            doc_keywords_data = [
                {
                    'value': doc_kw,
                    'variants': _keyword_variants(doc_kw),
                    'tokens': set(_tokenize_text(doc_kw)),
                    'index': idx  # Position in keyword list (0 = first/highest priority)
                }
                for idx, doc_kw in enumerate(doc_keywords_lower)
            ]

            doc_identifier_tokens = _build_identifier_tokens(doc_id, metadata)

            score = 0
            main_content_matches = 0
            matched_keywords = set()
            best_keyword_position = len(doc_keywords)  # Track best (lowest) position of matched keyword

            title = metadata.get('title', '').lower()
            description = metadata.get('description', '').lower()
            path = metadata.get('path', '').lower()
            url = metadata.get('url', '').lower()

            for kw in keyword_lower:
                kw_variants = keyword_variants.get(kw, {kw})
                kw_token_set = keyword_tokens.get(kw, {kw})

                if kw in title:
                    score += TITLE.exact_match
                    main_content_matches += 1
                    matched_keywords.add(kw)
                elif re.search(r'\b' + re.escape(kw) + r'\b', title):
                    score += TITLE.word_boundary_match
                    main_content_matches += 1
                    matched_keywords.add(kw)

                if kw in description:
                    score += DESCRIPTION.exact_match
                    main_content_matches += 1
                    matched_keywords.add(kw)
                elif re.search(r'\b' + re.escape(kw) + r'\b', description):
                    score += DESCRIPTION.word_boundary_match
                    main_content_matches += 1
                    matched_keywords.add(kw)

                for doc_kw in doc_keywords_data:
                    matched = False
                    if kw_variants & doc_kw['variants']:
                        score += KEYWORD.variant_match
                        main_content_matches += 1
                        matched_keywords.add(kw)
                        matched = True
                    elif kw_token_set & doc_kw['tokens']:
                        score += KEYWORD.token_match
                        main_content_matches += 1
                        matched_keywords.add(kw)
                        matched = True
                    elif kw in doc_kw['value'] or doc_kw['value'] in kw:
                        score += KEYWORD.substring_match
                        main_content_matches += 1
                        matched_keywords.add(kw)
                        matched = True

                    if matched:
                        # Track best keyword position for tiebreaking (lower = better)
                        best_keyword_position = min(best_keyword_position, doc_kw['index'])
                        break

                if kw in doc_tag_set:
                    score += TAG.exact_match
                    main_content_matches += 1
                    matched_keywords.add(kw)
                elif any(variant in doc_tag_set for variant in kw_variants):
                    score += TAG.variant_match
                    main_content_matches += 1
                    matched_keywords.add(kw)

                if any(variant in doc_identifier_tokens for variant in kw_variants):
                    score += IDENTIFIER.identifier_match
                    main_content_matches += 1
                    matched_keywords.add(kw)

                if kw in path or kw in url:
                    score += IDENTIFIER.path_url_match

            substantive_keywords = [kw for kw in keyword_lower if kw not in generic_verbs]
            matched_substantive = [kw for kw in substantive_keywords if kw in matched_keywords]
            has_substantive_match = len(matched_substantive) > 0

            # Apply penalty for generic term matches
            # Generic terms like "configuration", "setup", "installation" are too broad
            # and cause ranking collapse when mixed with specific terms
            # Loaded from filtering.yaml for centralized configuration
            generic_config_terms = get_generic_config_terms()
            
            # Identify which matched keywords are generic vs specific
            generic_matches = [kw for kw in matched_keywords if kw in generic_config_terms]
            specific_matches = [kw for kw in matched_keywords if kw not in generic_config_terms]
            
            # If doc ONLY matches generic terms (no specific term matches), severely penalize
            if generic_matches and not specific_matches:
                # Only generic terms matched - reduce score to near zero
                # This effectively filters out generic docs from appearing in results
                score *= PENALTIES.only_generic
            elif generic_matches and matched_keywords:
                # Mix of generic and specific - apply proportional penalty
                generic_ratio = len(generic_matches) / len(matched_keywords)
                if generic_ratio >= PENALTIES.high_threshold:
                    # High generic ratio: reduce score significantly
                    score *= PENALTIES.high_ratio
                elif generic_ratio >= PENALTIES.medium_threshold:
                    # Medium generic ratio: reduce score moderately
                    score *= PENALTIES.medium_ratio

            # Calculate query term coverage (what percentage of query terms matched)
            # Boost docs that match ALL query terms over docs that match only SOME
            num_query_terms = len(keyword_lower)
            num_matched_terms = len(matched_keywords)
            term_coverage = num_matched_terms / num_query_terms if num_query_terms > 0 else 0
            
            # Apply coverage multiplier to score
            # Full coverage (100%) = 1.5x to 2.0x multiplier (depending on title/heading match)
            # Partial coverage (50%) = 1.0x multiplier (no change)
            # This ensures docs matching all terms rank higher
            if term_coverage >= 1.0:
                # All terms matched - check if they ALL appear in title or heading
                all_in_title = all(kw in title for kw in keyword_lower)
                all_in_description = all(kw in description for kw in keyword_lower)

                if all_in_title or all_in_description:
                    # ALL query terms in title/description - strongest signal
                    coverage_multiplier = COVERAGE.all_in_title
                else:
                    # All terms matched across metadata - significant boost
                    coverage_multiplier = COVERAGE.all_terms
            elif term_coverage >= COVERAGE.most_threshold:
                # Most terms matched - moderate boost
                coverage_multiplier = COVERAGE.most_terms
            else:
                # Partial match - no boost
                coverage_multiplier = COVERAGE.partial
            
            score *= coverage_multiplier

            # Score subsection matches (extracted method for readability)
            subsections = metadata.get('subsections', [])
            best_subsection, subsection_bonus = (None, 0)
            if subsections and isinstance(subsections, list):
                best_subsection, subsection_bonus = self._score_subsection_matches(
                    subsections, keyword_lower, has_substantive_match, main_content_matches
                )

            score += subsection_bonus
            matched_subsection_anchor = best_subsection['anchor'] if best_subsection else None

            if main_content_matches == 0:
                continue

            domain = metadata.get('domain', '')
            doc_category_for_weight = metadata.get('category', '')
            domain_key = domain
            if domain == 'anthropic.com' and doc_category_for_weight:
                domain_key = f'anthropic.com/{doc_category_for_weight}'
            domain_weight = get_domain_weight(domain_key)
            score *= domain_weight

            if score > 0:
                # Add positional bonus for tiebreaking (earlier keyword position = higher bonus)
                # Bonus is small to avoid affecting main ranking, but enough to break ties
                # Formula: max_bonus / (position + 1) - so position 0 gets max, position 1 gets half, etc.
                if best_keyword_position < len(doc_keywords):
                    positional_bonus = POSITIONAL.max_bonus / (best_keyword_position + 1)
                    score += positional_bonus

                result_metadata = metadata.copy()

                if matched_subsection_anchor:
                    original_url = result_metadata.get('url', '')
                    if original_url and matched_subsection_anchor:
                        normalized_url = normalize_url_for_display(original_url)
                        if '#' not in normalized_url:
                            result_metadata['url'] = normalized_url + matched_subsection_anchor
                        else:
                            result_metadata['url'] = normalized_url
                        if best_subsection:
                            result_metadata['_matched_subsection'] = {
                                'anchor': matched_subsection_anchor,
                                'heading': best_subsection.get('heading'),
                                'score': best_subsection.get('score', 0)
                            }
                            result_metadata['_subsection_hint'] = True
                            result_metadata['_extraction_command'] = (
                                f"python scripts/get_subsection_content.py {doc_id} "
                                f"--section \"{best_subsection.get('heading')}\""
                            )

                results.append((score, best_keyword_position, doc_id, result_metadata))

        # Sort by score (desc), then by keyword position (asc) for tiebreaking
        results.sort(key=lambda x: (-x[0], x[1]))

        # Apply min_score filter if specified
        if min_score is not None:
            results = [(s, kw_pos, doc_id, meta) for s, kw_pos, doc_id, meta in results if s >= min_score]

        final_results = []
        for score, kw_position, doc_id, metadata in results[:limit]:
            if return_scores:
                metadata['_score'] = round(score, 2)
            final_results.append((doc_id, metadata))

        # Log search performance
        search_time = time.time() - search_start
        if _logger:
            top_result = final_results[0][0] if final_results else "none"
            _logger.debug(
                f"Search: keywords={keyword_lower}, results={len(final_results)}, "
                f"candidates={len(results)}, top={top_result}, time={search_time*1000:.1f}ms"
            )

        return final_results
    
    def search_by_natural_language(self, query: str, limit: int = 10,
                                    return_scores: bool = False,
                                    min_score: float | None = None) -> list[tuple[str, dict]]:
        """
        Search documents using natural language query

        Args:
            query: Natural language search query
            limit: Maximum number of results
            return_scores: If True, include score in metadata['_score']
            min_score: If set, only return results with score >= this value

        Returns:
            List of (doc_id, metadata) tuples, sorted by relevance
        """
        # Extract keywords from query
        # Remove common stop words (loaded from config for centralized management)
        stop_words = get_natural_language_stop_words()
        
        query_lower = query.lower()
        words = re.findall(r'\b[a-z]{3,}\b', query_lower)  # Min 3 chars to filter noise like 'md', 'id'
        keywords = [w for w in words if w not in stop_words]

        # Include file-like tokens (e.g., claude.md) so we can match documentation filenames
        file_terms = re.findall(r'\b[a-z0-9]+(?:\.[a-z0-9]+)+\b', query_lower)
        for term in file_terms:
            if term not in keywords:
                keywords.append(term)
        
        if not keywords:
            return []

        # TODO: Future enhancement - Semantic search fallback
        # When keyword search returns zero or low-quality results, consider:
        # 1. Embedding-based similarity search using sentence transformers
        # 2. Query expansion with synonyms (e.g., "setup" -> "installation", "configure")
        # 3. Fuzzy matching for typos and variations
        # 4. LLM-assisted query reformulation
        # Reference: 2025-11-25 audit recommendation for queries without keyword matches

        return self.search_by_keyword(keywords, limit=limit, return_scores=return_scores, min_score=min_score)

    def get_by_category(self, category: str) -> list[tuple[str, dict]]:
        """
        Get all documents in a category using O(1) index lookup.

        This method searches both the original 'category' field and the
        'doc_map_category' field (from docs_map.md enrichment).

        Args:
            category: Category name to filter by (case-insensitive)

        Returns:
            List of (doc_id, metadata) tuples
        """
        # Ensure inverted index is built (includes category index)
        self._build_inverted_index()

        category_lower = category.lower().strip()
        results = []

        # Use O(1) lookup from category index
        if self._category_index and category_lower in self._category_index:
            for doc_id in self._category_index[category_lower]:
                metadata = self._index.get(doc_id)
                if metadata:
                    results.append((doc_id, metadata))

        return results

    def list_categories(self) -> dict[str, int]:
        """
        List all available categories with document counts.

        Returns both original 'category' values and 'doc_map_category' values
        from docs_map.md enrichment.

        Returns:
            Dictionary mapping category name to document count
        """
        # Ensure inverted index is built
        self._build_inverted_index()

        if not self._category_index:
            return {}

        return {category: len(doc_ids) for category, doc_ids in self._category_index.items()}

    def get_doc_map_categories(self) -> dict[str, list[str]]:
        """
        Get hierarchical categories from docs_map.md with their document IDs.

        This returns only the 'doc_map_category' field values (hierarchical
        categories from the official docs map), not the original 'category' field.

        Returns:
            Dictionary mapping category name to list of doc_ids
        """
        categories: dict[str, list[str]] = {}

        for doc_id, metadata in self._index.items():
            doc_map_category = metadata.get('doc_map_category', '')
            if doc_map_category:
                if doc_map_category not in categories:
                    categories[doc_map_category] = []
                categories[doc_map_category].append(doc_id)

        return categories
    
    def get_by_tag(self, tag: str) -> list[tuple[str, dict]]:
        """Get all documents with a specific tag"""
        results = []
        tag_lower = tag.lower().strip()
        for doc_id, metadata in self._index.items():
            doc_tags_lower = normalize_tags(metadata.get('tags', []))
            if tag_lower in doc_tags_lower:
                results.append((doc_id, metadata))
        return results
    
    def get_related_docs(self, doc_id: str, limit: int = 5) -> list[tuple[str, dict]]:
        """
        Find related documents based on shared keywords/tags
        
        Args:
            doc_id: Document ID to find related docs for
            limit: Maximum number of results
        
        Returns:
            List of (doc_id, metadata) tuples
        """
        entry = self.index_manager.get_entry(doc_id)
        if not entry:
            return []
        
        # Get keywords and tags from source doc
        keywords = entry.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [keywords]
        tags = entry.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        
        if not keywords and not tags:
            return []
        
        # Search for docs with shared keywords/tags
        results = []
        for other_id, other_meta in self._index.items():
            if other_id == doc_id:
                continue
            
            score = 0
            
            # Check shared keywords
            other_keywords = other_meta.get('keywords', [])
            if isinstance(other_keywords, str):
                other_keywords = [other_keywords]
            shared_keywords = set(k.lower() for k in keywords) & set(k.lower() for k in other_keywords)
            score += len(shared_keywords) * 2
            
            # Check shared tags
            other_tags = other_meta.get('tags', [])
            if isinstance(other_tags, str):
                other_tags = [other_tags]
            shared_tags = set(t.lower() for t in tags) & set(t.lower() for t in other_tags)
            score += len(shared_tags) * 3
            
            if score > 0:
                results.append((score, other_id, other_meta))
        
        # Sort by score and return top results
        results.sort(key=lambda x: x[0], reverse=True)
        return [(doc_id, metadata) for _, doc_id, metadata in results[:limit]]
    
    def get_content(self, doc_id: str, section: str | None = None) -> dict[str, Any | None]:
        """
        Get document content (full or partial section).
        
        Args:
            doc_id: Document identifier
            section: Optional section heading to extract (if None, returns full content)
        
        Returns:
            Dictionary with keys:
            - content: Markdown content (partial or full)
            - content_type: "partial" | "full" | "link"
            - section_ref: Hashtag reference if partial (e.g., "#skills-vs-slash-commands")
            - doc_id: Document identifier
            - url: Source URL if available
            - title: Document title
            - description: Document description
            - warning: Warning about not storing file paths
        
        Returns None if doc_id not found or file doesn't exist.
        """
        # Resolve doc_id to file path
        path = self.resolve_doc_id(doc_id)
        if not path or not path.exists():
            return None
        
        # Get metadata from index
        entry = self.index_manager.get_entry(doc_id)
        if not entry:
            return None
        
        # Generate hashtag reference from section heading
        section_ref = None
        if section:
            # Convert section heading to hashtag format (lowercase, replace spaces with hyphens)
            section_ref = '#' + re.sub(r'[^\w\s-]', '', section.lower()).strip().replace(' ', '-')
        
        # Extract content
        content = None
        content_type = "link"
        
        if MarkdownExtractor is None:
            # Fallback: return link only if extractor not available
            return {
                'content': None,
                'content_type': 'link',
                'section_ref': section_ref,
                'doc_id': doc_id,
                'url': normalize_url_for_display(entry.get('url')),
                'title': entry.get('title'),
                'description': entry.get('description'),
                'warning': '⚠️ Do not store file paths. Use doc_id references or invoke docs-management skill for access.'
            }
        
        try:
            extractor = MarkdownExtractor(path)
            
            if section:
                # Extract specific section
                content = extractor.extract_section(section)
                if content:
                    content_type = "partial"
                else:
                    # Section not found, return full content as fallback
                    content = extractor.body
                    content_type = "full"
            else:
                # Return full content
                content = extractor.body
                content_type = "full"
        except Exception:
            # If extraction fails, return link only
            content = None
            content_type = "link"
        
        return {
            'content': content,
            'content_type': content_type,
            'section_ref': section_ref,
            'doc_id': doc_id,
            'url': normalize_url_for_display(entry.get('url')),
            'title': entry.get('title'),
            'description': entry.get('description'),
            'warning': '⚠️ Do not store file paths. Use doc_id references or invoke docs-management skill for access.'
        }

    def _build_path_to_docid_map(self) -> dict[str, str]:
        """
        Build a reverse lookup map from relative paths to doc_ids.

        Returns:
            Dictionary mapping normalized relative paths to doc_ids
        """
        path_map = {}
        for doc_id, metadata in self._index.items():
            path = metadata.get('path', '')
            if path:
                # Normalize path separators and store
                normalized = str(path).replace('\\', '/').lower()
                path_map[normalized] = doc_id
        return path_map

    def search_content(self, keywords: list[str], limit: int = 10,
                       include_context: bool = False, context_lines: int = 0) -> list[tuple[str, dict]]:
        """
        Search document content using ripgrep/grep.

        This searches the actual markdown file content, not just the index.
        Used to find matches that aren't in the keyword index.

        Args:
            keywords: List of keywords to search for
            limit: Maximum number of results
            include_context: If True, include matching line numbers and text snippets
            context_lines: Number of context lines around matches (only if include_context=True)

        Returns:
            List of (doc_id, metadata) tuples for documents containing the keywords.
            Metadata includes:
            - '_content_match': True to indicate content-based match
            - '_grep_matches': List of {line: int, text: str} if include_context=True
        """
        import subprocess
        import shutil
        import time
        import re

        search_start = time.time()

        # Filter empty keywords
        keywords = [k.strip() for k in keywords if k and k.strip()]
        if not keywords:
            return []

        # Build path-to-docid reverse lookup
        path_map = self._build_path_to_docid_map()

        # Search directory is the canonical docs folder
        search_dir = self.base_dir

        # Check for ripgrep availability
        rg_path = shutil.which('rg')

        # Store file -> matches mapping when include_context is True
        file_matches: dict[str, list[dict]] = {}
        matching_files: set[str] = set()

        try:
            if rg_path:
                if include_context:
                    # Use ripgrep with line numbers and context
                    # -i: case insensitive
                    # -n: show line numbers
                    # --no-heading: don't group by file (easier to parse)
                    # --glob: only search markdown files
                    # -F: fixed strings (prevents regex injection from keywords)
                    cmd = [rg_path, '-i', '-n', '-F', '--no-heading', '--glob', '*.md']
                    if context_lines > 0:
                        cmd.extend(['-C', str(context_lines)])
                    for kw in keywords:
                        cmd.extend(['-e', kw])
                    cmd.append(str(search_dir))

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        encoding='utf-8',
                        errors='replace'
                    )

                    if result.returncode == 0 and result.stdout:
                        # Parse output: filepath:line_number:text
                        # On Windows, paths have colons (C:\...), so we need careful parsing
                        for line in result.stdout.strip().split('\n'):
                            if not line:
                                continue
                            # Match pattern: filepath:linenum:text (handle Windows drive letters)
                            match = re.match(r'^(.+?):(\d+):(.*)$', line)
                            if match:
                                filepath = match.group(1)
                                line_num = int(match.group(2))
                                text = match.group(3).strip()
                                # Truncate long lines
                                if len(text) > 150:
                                    text = text[:147] + '...'
                                matching_files.add(filepath)
                                if filepath not in file_matches:
                                    file_matches[filepath] = []
                                # Limit matches per file to avoid bloat
                                if len(file_matches[filepath]) < 5:
                                    file_matches[filepath].append({'line': line_num, 'text': text})
                else:
                    # Use ripgrep (faster) - files only mode
                    # -i: case insensitive
                    # -l: files with matches only
                    # --glob: only search markdown files
                    # -F: fixed strings (prevents regex injection from keywords)
                    cmd = [rg_path, '-i', '-l', '-F', '--glob', '*.md']
                    for kw in keywords:
                        cmd.extend(['-e', kw])
                    cmd.append(str(search_dir))

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        encoding='utf-8',
                        errors='replace'
                    )

                    if result.returncode == 0 and result.stdout:
                        for line in result.stdout.strip().split('\n'):
                            if line:
                                matching_files.add(line.strip())
            else:
                # Fallback to Python-based search
                # Walk directory and search files
                import os
                pattern_lower = [kw.lower() for kw in keywords]

                for root, _, files in os.walk(search_dir):
                    for filename in files:
                        if not filename.endswith('.md'):
                            continue
                        filepath = os.path.join(root, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                                if include_context:
                                    lines = f.readlines()
                                    for i, line_text in enumerate(lines, 1):
                                        if any(kw in line_text.lower() for kw in pattern_lower):
                                            matching_files.add(filepath)
                                            if filepath not in file_matches:
                                                file_matches[filepath] = []
                                            if len(file_matches[filepath]) < 5:
                                                text = line_text.strip()
                                                if len(text) > 150:
                                                    text = text[:147] + '...'
                                                file_matches[filepath].append({'line': i, 'text': text})
                                else:
                                    content = f.read().lower()
                                    if any(kw in content for kw in pattern_lower):
                                        matching_files.add(filepath)
                        except (IOError, OSError):
                            continue

        except subprocess.TimeoutExpired:
            if _logger:
                _logger.warning("Content search timed out after 30s")
            return []
        except Exception as e:
            if _logger:
                _logger.warning(f"Content search failed: {e}")
            return []

        # Map matching files back to doc_ids
        results = []
        seen_doc_ids = set()

        for filepath in matching_files:
            # Normalize the path and make it relative to base_dir
            try:
                filepath_obj = Path(filepath)
                # Get path relative to base_dir
                rel_path = filepath_obj.relative_to(self.base_dir)
                normalized = str(rel_path).replace('\\', '/').lower()
            except (ValueError, TypeError):
                # Path is not relative to base_dir, try direct lookup
                normalized = str(filepath).replace('\\', '/').lower()

            # Look up doc_id from path
            doc_id = path_map.get(normalized)

            if not doc_id:
                # Try partial path matching (in case of path prefix differences)
                for stored_path, stored_doc_id in path_map.items():
                    if normalized.endswith(stored_path) or stored_path.endswith(normalized):
                        doc_id = stored_doc_id
                        break

            if doc_id and doc_id not in seen_doc_ids:
                seen_doc_ids.add(doc_id)
                metadata = self._index.get(doc_id, {}).copy()
                metadata['_content_match'] = True
                # Add grep matches if available
                if include_context and filepath in file_matches:
                    metadata['_grep_matches'] = file_matches[filepath]
                results.append((doc_id, metadata))

                if len(results) >= limit:
                    break

        # Log search performance
        search_time = time.time() - search_start
        if _logger:
            _logger.debug(
                f"Content search: keywords={keywords}, files_matched={len(matching_files)}, "
                f"results={len(results)}, time={search_time*1000:.1f}ms, include_context={include_context}"
            )

        return results


if __name__ == '__main__':
    # Simple CLI wrapper for DocResolver
    import argparse

    parser = argparse.ArgumentParser(
        description='Resolve doc_id to path and optionally show index metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Resolve a document ID to its markdown path
  python doc_resolver.py code-claude-com-docs-en-overview

  # Resolve and show metadata
  python doc_resolver.py code-claude-com-docs-en-overview --show-metadata
""",
    )
    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    add_base_dir_argument(parser)
    parser.add_argument(
        '--show-metadata',
        action='store_true',
        help='Also print the full metadata entry from index.yaml',
    )
    parser.add_argument('doc_id', nargs='?', help='Document ID to resolve')

    args = parser.parse_args()

    # Resolve base directory using cli_utils helper
    base_dir = resolve_base_dir_from_args(args)

    resolver = DocResolver(base_dir)

    if not args.doc_id:
        print("Usage: python doc_resolver.py <doc_id> [--show-metadata]")
        sys.exit(1)
    else:
        path = resolver.resolve_doc_id(args.doc_id)
        if path:
            print(f"✅ Resolved: {path}")
            if args.show_metadata:
                entry = resolver.index_manager.get_entry(args.doc_id)
                if entry is None:
                    print("   (No metadata entry found in index.yaml)")
                else:
                    print("📋 Metadata:")
                    for key, value in entry.items():
                        print(f"  {key}: {value}")
        else:
            print(f"❌ Not found: {args.doc_id}")

