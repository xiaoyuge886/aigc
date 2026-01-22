#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_metadata.py - Extract metadata (title, description, keywords, tags) from markdown files

Extracts metadata from markdown content for indexing:
- Title: First h1 heading or frontmatter title
- Description: First paragraph or excerpt
- Keywords: From frontmatter, headings, or content analysis
- Tags: From frontmatter or auto-categorization
- Category: Auto-detect from path/domain/content
- Domain: Extract from URL

Usage:
    python extract_metadata.py <file_path>
    python extract_metadata.py <file_path> --url <url>
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; config_dir = bootstrap.config_dir

import argparse
import re
from typing import Union
from urllib.parse import urlparse

from utils.script_utils import configure_utf8_output, ensure_yaml_installed

FILE_TOKEN_EXTENSIONS = {
    'md', 'mdx', 'yaml', 'yml', 'json', 'toml', 'ini', 'cfg',
    'ps1', 'sh', 'bat', 'py'
}

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

# Import config helpers for configuration access
try:
    from utils.config_helpers import get_http_head_request_timeout
    from config_registry import get_default
except ImportError:
    # Fallback if config_helpers not available
    def get_http_head_request_timeout() -> float:
        return 10.0
    def get_default(section: str, key: str, default=None):
        return default

from utils.logging_utils import get_or_setup_logger
logger = get_or_setup_logger(__file__, log_category="index")

yaml = ensure_yaml_installed()

# Optional NLP libraries (canonical flags for keyword extraction elsewhere)
# Note: spaCy requires Python 3.13 or earlier (not compatible with Python 3.14+)
from utils.script_utils import suppress_pydantic_v1_warning
suppress_pydantic_v1_warning()  # Must be called before spacy import
try:
    import spacy  # noqa: F401 - availability check, sets SPACY_AVAILABLE
    from spacy.lang.en.stop_words import STOP_WORDS
    SPACY_AVAILABLE = True
except (ImportError, Exception):
    # Catch ImportError and any other exceptions (e.g., Pydantic errors on Python 3.14+)
    SPACY_AVAILABLE = False
    STOP_WORDS = set()
    # Note: Agents can install with: pip install spacy && python -m spacy download en_core_web_sm
    # Note: Use Python 3.13 for spaCy operations: py -3.13 <script>

try:
    import yake
    YAKE_AVAILABLE = True
except ImportError:
    YAKE_AVAILABLE = False
    # Note: Agents can install with: pip install yake

class MetadataExtractor:
    """Extract metadata from markdown files"""
    
    # Class-level caches (avoid repeating expensive work per document)
    _tag_config = None
    _filter_config = None
    _stop_words_cache: set[str] | None = None
    _extraction_limits_cache: dict[str, int] | None = None
    
    @classmethod
    def _get_extraction_limits(cls) -> dict[str, int]:
        """Get keyword extraction limits from config (cached at class level)."""
        if cls._extraction_limits_cache is not None:
            return cls._extraction_limits_cache
        
        # Load from defaults.yaml via config_registry
        limits = {
            'max_file_tokens': get_default('keyword_extraction.limits', 'max_file_tokens', 4),
            'max_heading_phrases': get_default('keyword_extraction.limits', 'max_heading_phrases', 10),
            'max_heading_keywords': get_default('keyword_extraction.limits', 'max_heading_keywords', 8),
            'max_body_keywords': get_default('keyword_extraction.limits', 'max_body_keywords', 6),
            'max_total_keywords': get_default('keyword_extraction.limits', 'max_total_keywords', 12),
        }
        
        cls._extraction_limits_cache = limits
        return limits
    
    def __init__(self, file_path: Path, url: str | None = None):
        """
        Initialize extractor
        
        Args:
            file_path: Path to markdown file
            url: Optional source URL
        
        Raises:
            FileNotFoundError: If file doesn't exist
            UnicodeDecodeError: If file can't be decoded as UTF-8
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        self.url = url
        try:
            self.content = self.file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to read file as UTF-8: {self.file_path}") from e
        
        self.frontmatter = self._parse_frontmatter()
        self.body = self._strip_frontmatter()
        
        # Load configs (cached at class level)
        self._load_configs()
    
    @classmethod
    def _load_configs(cls):
        """Load YAML config files (cached at class level)"""
        if cls._tag_config is not None and cls._filter_config is not None:
            return
        
        # Get config directory using centralized utility (already in sys.path)
        from utils.common_paths import get_config_dir
        config_dir = get_config_dir()
        
        # Load tag detection config
        tag_config_path = config_dir / 'tag_detection.yaml'
        if tag_config_path.exists():
            try:
                with open(tag_config_path, 'r', encoding='utf-8') as f:
                    cls._tag_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️  Warning: Could not load tag_detection.yaml: {e}")
                cls._tag_config = {}
        else:
            cls._tag_config = {}
        
        # Load filtering config
        filter_config_path = config_dir / 'filtering.yaml'
        if filter_config_path.exists():
            try:
                with open(filter_config_path, 'r', encoding='utf-8') as f:
                    cls._filter_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️  Warning: Could not load filtering.yaml: {e}")
                cls._filter_config = {}
        else:
            cls._filter_config = {}
    
    def _get_stop_words(self) -> set[str]:
        """Get stop words from library + domain-specific config.

        Prefer spaCy's official stop-word list when available but always fall back
        to a comprehensive static list so callers never fail due to environment issues.
        """
        # If we've already built the stop word set once, reuse it.
        if MetadataExtractor._stop_words_cache is not None:
            return set(MetadataExtractor._stop_words_cache)

        stop_words: set[str] = set()
        
        # Try to use spaCy stop words if available in this interpreter.
        if SPACY_AVAILABLE:
            stop_words.update(STOP_WORDS)
        
        # Use comprehensive static fallback if spaCy not available
        if not stop_words:
            # Fallback to comprehensive English stop words matching spaCy's list
            # (326 words) for better keyword quality.
            stop_words.update({
                    "'d", "'ll", "'m", "'re", "'s", "'ve", 'a', 'about', 'above', 'across', 'after', 'afterwards',
                    'again', 'against', 'all', 'almost', 'alone', 'along', 'already', 'also', 'although', 'always',
                    'am', 'among', 'amongst', 'amount', 'an', 'and', 'another', 'any', 'anyhow', 'anyone', 'anything',
                    'anyway', 'anywhere', 'are', 'around', 'as', 'at', 'back', 'be', 'became', 'because', 'become',
                    'becomes', 'becoming', 'been', 'before', 'beforehand', 'behind', 'being', 'below', 'beside',
                    'besides', 'between', 'beyond', 'both', 'bottom', 'but', 'by', 'ca', 'call', 'can', 'cannot',
                    'could', 'did', 'do', 'does', 'doing', 'done', 'down', 'due', 'during', 'each', 'eight',
                    'either', 'eleven', 'else', 'elsewhere', 'empty', 'enough', 'even', 'ever', 'every', 'everyone',
                    'everything', 'everywhere', 'except', 'few', 'fifteen', 'fifty', 'first', 'five', 'for', 'former',
                    'formerly', 'forty', 'four', 'from', 'front', 'full', 'further', 'get', 'give', 'go', 'had',
                    'has', 'have', 'he', 'hence', 'her', 'here', 'hereafter', 'hereby', 'herein', 'hereupon', 'hers',
                    'herself', 'him', 'himself', 'his', 'how', 'however', 'hundred', 'i', 'if', 'in', 'indeed', 'into',
                    'is', 'it', 'its', 'itself', 'just', 'keep', 'last', 'latter', 'latterly', 'least', 'less',
                    'made', 'make', 'many', 'may', 'me', 'meanwhile', 'might', 'mine', 'more', 'moreover', 'most',
                    'mostly', 'move', 'much', 'must', 'my', 'myself', "n't", 'name', 'namely', 'neither', 'never',
                    'nevertheless', 'next', 'nine', 'no', 'nobody', 'none', 'noone', 'nor', 'not', 'nothing', 'now',
                    'nowhere', 'of', 'off', 'often', 'on', 'once', 'one', 'only', 'onto', 'or', 'other', 'others',
                    'otherwise', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'part', 'per', 'perhaps', 'please',
                    'put', 'quite', 'rather', 're', 'really', 'regarding', 'same', 'say', 'see', 'seem', 'seemed',
                    'seeming', 'seems', 'serious', 'several', 'she', 'should', 'show', 'side', 'since', 'six', 'sixty',
                    'so', 'some', 'somehow', 'someone', 'something', 'sometime', 'sometimes', 'somewhere', 'still',
                    'such', 'take', 'ten', 'than', 'that', 'the', 'their', 'them', 'themselves', 'then', 'thence',
                    'there', 'thereafter', 'thereby', 'therefore', 'therein', 'thereupon', 'these', 'they', 'third',
                    'this', 'those', 'though', 'three', 'through', 'throughout', 'thru', 'thus', 'to', 'together',
                    'too', 'top', 'toward', 'towards', 'twelve', 'twenty', 'two', 'under', 'unless', 'until', 'up',
                    'upon', 'us', 'used', 'using', 'various', 'very', 'via', 'was', 'we', 'well', 'were', 'what',
                    'whatever', 'when', 'whence', 'whenever', 'where', 'whereafter', 'whereas', 'whereby', 'wherein',
                    'whereupon', 'wherever', 'whether', 'which', 'while', 'whither', 'who', 'whoever', 'whole', 'whom',
                    'whose', 'why', 'will', 'with', 'within', 'without', 'would', 'yet', 'you', 'your', 'yours',
                    'yourself', 'yourselves'
                })
        
        # Add domain-specific stop words from config
        domain_stop_words = self._filter_config.get('domain_stop_words', [])
        stop_words.update(domain_stop_words)
        
        # Add common markdown/document terms
        stop_words.update({'md', 'doc', 'docs', 'guide', 'reference', 'api', 'overview', 'intro', 'about', 'using'})
        
        # Cache for subsequent calls (class-level cache avoids rebuilding per file)
        MetadataExtractor._stop_words_cache = set(stop_words)
        return stop_words
    
    def _get_filtering_lists(self) -> dict[str, set[str]]:
        """Get filtering lists from config"""
        return {
            'generic_verbs': set(self._filter_config.get('generic_verbs', [])),
            'incomplete_endings': set(self._filter_config.get('incomplete_endings', [])),
            'generic_single_words': set(self._filter_config.get('generic_single_words', [])),
            'generic_words': set(self._filter_config.get('generic_words', [])),
            'technical_phrases': set(self._filter_config.get('technical_phrases', [])),
            'stop_phrases': set(self._filter_config.get('stop_phrases', []))
        }
    
    def _extract_technical_phrases(self) -> set[str]:
        """
        Extract technical phrases (multi-word technical terms) from content.
        
        Technical phrases are preserved as single keywords instead of being split.
        For example, "progressive disclosure" is kept as one keyword rather than
        being split into "progressive" and "disclosure".
        
        Returns:
            Set of technical phrases found in content
        """
        technical_phrases = set(self._filter_config.get('technical_phrases', []))
        found_phrases = set()
        
        # Search for technical phrases in content (case-insensitive)
        content_lower = f"{self.body} {self.frontmatter.get('title', '')} {self.frontmatter.get('description', '')}".lower()
        
        for phrase in technical_phrases:
            phrase_lower = phrase.lower()
            if phrase_lower in content_lower:
                found_phrases.add(phrase)
        
        return found_phrases
    
    def _parse_frontmatter(self) -> dict:
        """Parse YAML frontmatter if present"""
        if not self.content.startswith('---'):
            return {}
        
        try:
            parts = self.content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1].strip()
                if frontmatter_text:
                    return yaml.safe_load(frontmatter_text) or {}
        except Exception:
            pass
        
        return {}
    
    def _strip_frontmatter(self) -> str:
        """Remove frontmatter and return body"""
        if self.content.startswith('---'):
            parts = self.content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return self.content.strip()
    
    def extract_title(self) -> str | None:
        """
        Extract document title
        
        Priority:
        1. Frontmatter 'title'
        2. First h1 heading
        3. Filename (without extension)
        """
        # Check frontmatter
        if 'title' in self.frontmatter:
            return str(self.frontmatter['title']).strip()
        
        # Check first h1 heading
        h1_match = re.search(r'^#\s+(.+)$', self.body, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        # Fallback to filename
        return self.file_path.stem.replace('-', ' ').replace('_', ' ').title()
    
    def extract_description(self, max_length: int = 200) -> str | None:
        """
        Extract document description
        
        Priority:
        1. Frontmatter 'description'
        2. First paragraph (non-heading, non-code)
        3. First sentence from content
        """
        # Check frontmatter
        if 'description' in self.frontmatter:
            desc = str(self.frontmatter['description'])
            if desc:
                return desc.strip()[:max_length]
        
        # Extract first paragraph
        lines = self.body.split('\n')
        paragraph_lines = []

        for line in lines:
            line = line.strip()
            # Skip empty lines, headings, code blocks, frontmatter, blockquotes
            if not line:
                if paragraph_lines:
                    break  # End of first paragraph
                continue
            if line.startswith('#'):
                continue
            if line.startswith('```'):
                continue
            if line.startswith('---'):
                continue
            if line.startswith('!['):  # Skip image-only lines
                continue
            if line.startswith('[') and '](' in line:  # Skip link-only lines
                continue
            if line.startswith('>'):  # Skip blockquote lines (markdown artifacts)
                continue

            # Clean any remaining markdown artifacts (e.g., inline blockquote markers)
            line = line.lstrip('> ').strip()
            if not line:
                continue

            paragraph_lines.append(line)
            if len(' '.join(paragraph_lines)) > max_length:
                break
        
        if paragraph_lines:
            desc = ' '.join(paragraph_lines)
            # Truncate to max_length at word boundary
            if len(desc) > max_length:
                # Find last space before max_length
                truncate_pos = desc.rfind(' ', 0, max_length)
                if truncate_pos > 0:
                    desc = desc[:truncate_pos] + '...'
                else:
                    # No space found, truncate at max_length
                    desc = desc[:max_length] + '...'
            return desc.strip()
        
        return None
    
    def _extract_frontmatter_keywords(self, stop_words: set[str]) -> tuple[set[str], int]:
        """
        Extract keywords from frontmatter 'keywords' and 'tags' fields.

        Args:
            stop_words: Set of stop words to filter out

        Returns:
            Tuple of (keywords set, count of keywords added)
        """
        keywords: set[str] = set()
        count = 0

        # From frontmatter 'keywords' field
        if 'keywords' in self.frontmatter:
            kw = self.frontmatter['keywords']
            if isinstance(kw, list):
                frontmatter_kw = [str(k).lower().strip() for k in kw if k]
                keywords.update(frontmatter_kw)
                count += len(frontmatter_kw)
            elif isinstance(kw, str):
                frontmatter_kw = [k.lower().strip() for k in kw.split(',') if k.strip()]
                keywords.update(frontmatter_kw)
                count += len(frontmatter_kw)

        # From frontmatter 'tags' field
        if 'tags' in self.frontmatter:
            tags = self.frontmatter['tags']
            if isinstance(tags, list):
                tag_kw = [str(t).lower().strip() for t in tags if t]
                keywords.update(tag_kw)
                count += len(tag_kw)
            elif isinstance(tags, str):
                tag_kw = [t.lower().strip() for t in tags.split(',') if t.strip()]
                keywords.update(tag_kw)
                count += len(tag_kw)

        return keywords, count

    def _extract_title_desc_keywords(self, stop_words: set[str]) -> tuple[set[str], int]:
        """
        Extract keywords from title and description.

        Args:
            stop_words: Set of stop words to filter out

        Returns:
            Tuple of (keywords set, count of keywords added)
        """
        keywords: set[str] = set()
        count = 0

        # Extract from title (if available)
        title = self.extract_title()
        if title:
            # Extract meaningful words/phrases from title (3+ chars, not stop words)
            title_words = [w for w in re.findall(r'\b[a-z]{3,}\b', title.lower()) if w not in stop_words]
            keywords.update(title_words)
            count += len(title_words)

        # Extract from description (first paragraph) - focus on technical terms
        description = self.extract_description()
        if description:
            # Extract meaningful words from description (5+ chars for better quality)
            # Longer words are usually technical terms
            desc_words = re.findall(r'\b[a-z]{5,}\b', description.lower())
            # Take top words (longer words are usually more meaningful)
            desc_words_sorted = sorted(set(desc_words), key=lambda x: (len(x), x), reverse=True)
            desc_words_filtered = [w for w in desc_words_sorted[:8] if w not in stop_words]
            keywords.update(desc_words_filtered)
            count += len(desc_words_filtered)

        return keywords, count

    def _extract_with_yake(self, stop_words: set[str], filters: dict[str, set[str]]) -> tuple[set[str], bool, int]:
        """
        Extract keywords using YAKE automatic keyword extraction.

        Args:
            stop_words: Set of stop words to filter out
            filters: Dictionary of filtering lists (generic_words, etc.)

        Returns:
            Tuple of (keywords set, yake_used flag, count of keywords added)
            yake_used=True means YAKE was available and attempted (even if no keywords extracted)
        """
        keywords: set[str] = set()
        yake_used = False
        count = 0

        if not YAKE_AVAILABLE:
            return keywords, yake_used, count

        # YAKE is available - mark as used/attempted as soon as we enter the extraction block
        # This tracks "was YAKE attempted" not "did YAKE succeed"
        yake_used = True

        try:
            # Prepare text for YAKE (remove markdown formatting)
            yake_text = re.sub(r'```[\s\S]*?```', '', self.body)  # Remove code blocks
            yake_text = re.sub(r'`[^`]+`', '', yake_text)  # Remove inline code
            yake_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', yake_text)  # Remove links, keep text
            yake_text = re.sub(r'[#*_~]', '', yake_text)  # Remove markdown formatting
            yake_text = yake_text.strip()

            # Get YAKE config from defaults.yaml
            yake_language = get_default('keyword_extraction.yake', 'language', 'en')
            yake_max_ngram = get_default('keyword_extraction.yake', 'max_ngram_size', 3)
            yake_dedup = get_default('keyword_extraction.yake', 'dedup_threshold', 0.7)
            yake_top = get_default('keyword_extraction.yake', 'top_keywords', 15)
            yake_min_length = get_default('keyword_extraction.yake', 'min_text_length', 50)
            
            # YAKE requires a minimum amount of text for meaningful extraction
            # Even if text is too short, YAKE was attempted (yake_used remains True)
            if len(yake_text) < yake_min_length:
                return keywords, yake_used, count

            # Extract keywords with YAKE using config values
            try:
                kw_extractor = yake.KeywordExtractor(
                    lan=yake_language,
                    n=yake_max_ngram,
                    dedupLim=yake_dedup,
                    top=yake_top,
                    features=None
                )
                yake_keywords = kw_extractor.extract_keywords(yake_text)

                # Add YAKE keywords (score, keyword tuple)
                for score, keyword in yake_keywords:
                    # Filter out stop words and normalize
                    keyword_lower = keyword.lower().strip()
                    # Only add meaningful keywords (3+ chars, not stop words, not generic)
                    if (keyword_lower and
                        len(keyword_lower) >= 3 and
                        keyword_lower not in stop_words and
                        keyword_lower not in filters.get('generic_words', set())):
                        keywords.add(keyword_lower)
                        count += 1
            except Exception:
                # YAKE extraction failed for this document, but YAKE was attempted
                # Keep yake_used = True (it was available and attempted, just failed)
                count = 0
        except Exception:
            # If YAKE fails for any other reason, YAKE was still attempted
            # Keep yake_used = True (it was available and attempted, just failed)
            count = 0

        return keywords, yake_used, count

    def _extract_heading_keywords(self, stop_words: set[str], filters: dict[str, set[str]]) -> tuple[set[str], int]:
        """
        Extract keywords from heading text (h1-h6).

        Args:
            stop_words: Set of stop words to filter out
            filters: Dictionary of filtering lists (generic_verbs, incomplete_endings, etc.)

        Returns:
            Tuple of (keywords set, count of keywords added)
        """
        keywords: set[str] = set()
        generic_verbs = filters['generic_verbs']
        incomplete_endings = filters['incomplete_endings']

        # Include ALL headings (h1-h6) for better coverage
        heading_pattern = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
        heading_keywords_set = set()
        heading_phrases = set()
        heading_file_tokens = set()

        for match in heading_pattern.finditer(self.body):
            heading_text = match.group(1).strip()
            # Remove markdown links and formatting
            heading_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', heading_text)  # Remove links, keep text
            heading_text = re.sub(r'`([^`]+)`', r'\1', heading_text)  # Remove code, keep text
            heading_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', heading_text)  # Remove bold
            heading_text = re.sub(r'\*([^\*]+)\*', r'\1', heading_text)  # Remove italic

            heading_lower = heading_text.lower()

            # Extract meaningful words (3+ chars, not stop words)
            words = re.findall(r'\b[a-z]{3,}\b', heading_lower)
            heading_keywords_set.update(w for w in words if w not in stop_words)

            # Extract file-like tokens (e.g., claude.md, config.yaml) for discoverability
            file_tokens = re.findall(r'\b[a-z0-9]+(?:\.[a-z0-9]+)+\b', heading_lower)
            for token in file_tokens:
                ext = token.split('.')[-1]
                if ext in FILE_TOKEN_EXTENSIONS:
                    heading_file_tokens.add(token)

            # Also extract 2-word phrases from headings (more meaningful)
            # Only extract complete phrases (not partial)
            phrases = re.findall(r'\b([a-z]{4,})\s+([a-z]{4,})\b', heading_lower)
            for w1, w2 in phrases:
                if w1 not in stop_words and w2 not in stop_words:
                    # Skip incomplete phrases like "start your", "ask your", "learn about"
                    if w1 not in generic_verbs and w2 not in incomplete_endings:
                        heading_phrases.add(f"{w1} {w2}")

        # Get extraction limits from config
        limits = self._get_extraction_limits()
        
        # Prioritize phrases, then single words, then limited file tokens
        # Sort before slicing to ensure deterministic output (sets have non-deterministic iteration order)
        heading_phrases_list = sorted(heading_phrases)[:limits['max_heading_phrases']]
        heading_keywords_list = sorted(heading_keywords_set)[:limits['max_heading_keywords']]
        file_tokens_list = sorted(heading_file_tokens)[:limits['max_file_tokens']]

        keywords.update(heading_phrases_list)
        keywords.update(heading_keywords_list)
        keywords.update(file_tokens_list)
        count = len(heading_phrases_list) + len(heading_keywords_list) + len(file_tokens_list)

        return keywords, count

    def _extract_filename_keywords(self, stop_words: set[str]) -> tuple[set[str], int]:
        """
        Extract keywords from filename, path segments, and URL.

        Extracts meaningful keywords from:
        1. Filename (e.g., "overview.md" -> "overview")
        2. Parent directory names (e.g., "agent-sdk/overview.md" -> "agent-sdk")
        3. URL path segments (e.g., "/docs/tool-use" -> "tool-use")

        Hyphenated terms are preserved as compound keywords AND split into components:
        - "agent-sdk" yields: "agent-sdk", "agent", "sdk"

        Args:
            stop_words: Set of stop words to filter out

        Returns:
            Tuple of (keywords set, count of keywords added)
        """
        keywords: set[str] = set()

        # Common path/file stop words to filter
        path_stop_words = stop_words | {
            'md', 'doc', 'docs', 'guide', 'reference', 'api', 'overview', 'intro', 'en',
            'index', 'readme', 'main', 'home', 'default', 'page', 'v1', 'v2', 'v3',
            'canonical', 'com', 'www', 'https', 'http'
        }

        # Add domain stop words from config (prevents domain prefixes like 'anthropic-com' as keywords)
        domain_stop_words = set(self._filter_config.get('domain_stop_words', []))
        path_stop_words.update(domain_stop_words)

        def extract_from_segment(segment: str) -> set[str]:
            """Extract keywords from a single path/URL segment."""
            result: set[str] = set()
            segment_lower = segment.lower()

            # Skip if too short or is a stop word
            if len(segment_lower) < 3 or segment_lower in path_stop_words:
                return result

            # If hyphenated, add the compound term AND split it
            if '-' in segment_lower:
                parts = segment_lower.split('-')

                # Add full hyphenated term if not too long (<=4 parts)
                # Also check that the full term is not in stop words
                # FIX 2025-11-25: Previously added segment without checking path_stop_words
                if len(parts) <= 4 and segment_lower not in path_stop_words:
                    result.add(segment_lower)

                # Add individual words
                for word in parts:
                    if len(word) >= 3 and word not in path_stop_words:
                        result.add(word)

                # For longer filenames (5+ parts), extract meaningful sub-compounds
                # This handles cases like "building-agents-with-the-claude-agent-sdk"
                # which should yield "agent-sdk", "claude-agent-sdk"
                if len(parts) >= 4:
                    # Extract 2-3 word compounds from the end (most specific part)
                    for window_size in [2, 3]:
                        for start in range(len(parts) - window_size + 1):
                            sub_compound = '-'.join(parts[start:start + window_size])
                            # Keep compound if all parts are meaningful (>=3 chars, not stop words)
                            sub_parts = sub_compound.split('-')
                            if all(len(p) >= 3 and p not in path_stop_words for p in sub_parts):
                                result.add(sub_compound)
            else:
                # Single word - add if meaningful
                words = re.findall(r'\b[a-z]{3,}\b', segment_lower)
                result.update(w for w in words if w not in path_stop_words)

            return result

        # 1. Extract from filename
        keywords.update(extract_from_segment(self.file_path.stem))

        # 2. Extract from parent directories (up to 3 levels)
        for i, parent in enumerate(self.file_path.parents):
            if i >= 3:  # Only go up 3 levels
                break
            keywords.update(extract_from_segment(parent.name))

        # 3. Extract from URL path if available
        if self.url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.url)
                path_parts = [p for p in parsed.path.split('/') if p]
                for part in path_parts:
                    keywords.update(extract_from_segment(part))
            except Exception:
                pass  # URL parsing failed, skip

        count = len(keywords)
        return keywords, count

    def _extract_body_keywords(self, keywords: set[str], stop_words: set[str]) -> tuple[set[str], int]:
        """
        Extract keywords from body content (important terms that appear multiple times).
        Only runs if we don't have enough keywords yet.

        Args:
            keywords: Existing keywords set (to check if we need more)
            stop_words: Set of stop words to filter out

        Returns:
            Tuple of (new keywords set, count of keywords added)
        """
        new_keywords: set[str] = set()
        count = 0

        # Only do this if we don't have enough keywords yet (to avoid over-extraction)
        if len(keywords) >= 8:
            return new_keywords, count

        # Extract from body content (important terms that appear multiple times)
        body_text = re.sub(r'```[\s\S]*?```', '', self.body)  # Remove code blocks
        body_text = re.sub(r'`[^`]+`', '', body_text)  # Remove inline code
        body_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', body_text)  # Remove links, keep text
        body_text = re.sub(r'[#*_~]', '', body_text)  # Remove markdown formatting

        # Extract technical terms (5+ chars) that appear 2+ times (likely important)
        body_words = re.findall(r'\b[a-z]{5,}\b', body_text.lower())
        word_freq = {}
        for word in body_words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Add frequently occurring technical terms (appear 2+ times)
        # We'll filter generic words later in the cleaning step
        frequent_terms = [w for w, count in word_freq.items() if count >= 2]
        # Sort by frequency, then length (most frequent and longest first)
        frequent_terms_sorted = sorted(frequent_terms, key=lambda x: (word_freq[x], len(x)), reverse=True)
        
        # Get max body keywords from config
        limits = self._get_extraction_limits()
        body_kw = frequent_terms_sorted[:limits['max_body_keywords']]
        new_keywords.update(body_kw)
        count = len(body_kw)

        return new_keywords, count

    def _should_skip_phrase(
        self,
        words: list[str],
        generic_verbs: set[str],
        incomplete_endings: set[str],
        generic_words: set[str],
        generic_single_words: set[str],
        weak_phrase_words: set[str],
        weak_two_word_adverbs: set[str]
    ) -> bool:
        """
        Check if a multi-word phrase should be skipped based on filtering rules.
        
        Args:
            words: List of words in the phrase
            generic_verbs: Set of generic verbs from config
            incomplete_endings: Set of incomplete endings from config
            generic_words: Set of generic words from config
            generic_single_words: Set of generic single words from config
            weak_phrase_words: Set of weak words for phrase filtering
            weak_two_word_adverbs: Set of weak adverbs for 2-word phrases
        
        Returns:
            True if phrase should be skipped, False otherwise
        """
        words_lower = [w.lower() for w in words]
        
        # Skip if starts with incomplete ending
        if words_lower[0] in incomplete_endings:
            return True
        
        # Skip if ends with incomplete endings or starts with generic verb
        if words_lower[-1] in incomplete_endings or words_lower[0] in generic_verbs:
            return True
        
        # Skip 2-word phrases ending with weak adverbs
        if len(words) == 2 and words_lower[1] in weak_two_word_adverbs:
            return True
        
        # Skip if ends with generic verbs (redundant check kept for safety)
        if words_lower[-1] in generic_verbs:
            return True
        
        # Skip if ALL words are generic
        if all(w in generic_words for w in words_lower):
            return True
        
        # Skip if starts with generic words
        if words_lower[0] in generic_words:
            return True
        
        # Skip if ANY word is in generic lists
        if any(w in generic_single_words or w in generic_words for w in words_lower):
            return True
        
        # Skip if contains weak phrase words
        if any(w in weak_phrase_words for w in words_lower):
            return True
        
        return False
    
    def _should_keep_single_word(
        self,
        kw: str,
        min_length: int,
        generic_words: set[str],
        generic_single_words: set[str],
        domain_stop_words: set[str],
        single_word_exclusions: set[str]
    ) -> bool:
        """
        Check if a single-word keyword should be kept.
        
        Args:
            kw: The keyword to check
            min_length: Minimum length for single words
            generic_words: Set of generic words from config
            generic_single_words: Set of generic single words from config
            domain_stop_words: Set of domain stop words from config
            single_word_exclusions: Set of specific exclusions from config
        
        Returns:
            True if keyword should be kept, False otherwise
        """
        kw_lower = kw.lower()
        
        if len(kw) < min_length:
            return False
        if kw_lower in generic_words:
            return False
        if kw_lower in generic_single_words:
            return False
        if kw_lower in domain_stop_words:
            return False
        if kw_lower in single_word_exclusions:
            return False
        
        return True

    def _filter_and_clean_keywords(
        self,
        keywords: set[str],
        stop_words: set[str],
        filters: dict[str, set[str]],
        priority_keywords: set[str] | None = None
    ) -> list[str]:
        """
        Filter and clean extracted keywords, removing generic/incomplete phrases.

        Uses config-driven filtering rules from filtering.yaml to remove:
        - Stop phrases (noise patterns)
        - Too-short keywords
        - Generic verbs, incomplete endings, weak words
        - Domain-specific exclusions

        Preserves technical phrases without filtering.
        Priority keywords (e.g., from filename) are always included.

        Args:
            keywords: Raw keywords set to clean
            stop_words: Set of stop words to filter out
            filters: Dictionary of filtering lists from config
            priority_keywords: Keywords that should always be included (e.g., filename-derived)

        Returns:
            List of cleaned and filtered keywords
        """
        if priority_keywords is None:
            priority_keywords = set()
        # Load filter lists from config
        generic_verbs = filters['generic_verbs']
        incomplete_endings = filters['incomplete_endings']
        generic_single_words = filters['generic_single_words']
        generic_words = filters['generic_words']
        technical_phrases = filters.get('technical_phrases', set())
        stop_phrases = filters.get('stop_phrases', set())
        weak_phrase_words = set(self._filter_config.get('weak_phrase_words', []))
        weak_two_word_adverbs = set(self._filter_config.get('weak_two_word_adverbs', []))
        domain_stop_words = set(self._filter_config.get('domain_stop_words', []))
        single_word_exclusions = set(self._filter_config.get('single_word_exclusions', []))
        
        # Load filtering config
        filter_config = self._filter_config.get('keyword_filtering_config', {})
        min_length_general = filter_config.get('min_length_general', 3)
        min_length_single = filter_config.get('min_length_single_word', 6)
        # Use centralized max_total_keywords from defaults.yaml (single source of truth)
        # Not filtering.yaml max_keywords which was a duplicate causing inconsistency
        limits = self._get_extraction_limits()
        max_keywords = limits.get('max_total_keywords', 12)

        # Track phrases and single words separately
        phrase_keywords = []
        single_keywords = []

        for kw in keywords:
            kw = kw.strip()
            kw_lower = kw.lower()
            
            # Skip stop phrases entirely (noise patterns)
            if kw_lower in stop_phrases:
                continue
            
            # Skip if too short or is a stop word
            if len(kw) < min_length_general or kw in stop_words:
                continue
            
            # Preserve technical phrases without additional filtering
            if kw_lower in {tp.lower() for tp in technical_phrases}:
                phrase_keywords.append(kw)
                continue

            # Handle multi-word phrases
            if ' ' in kw:
                words = kw.split()
                if not self._should_skip_phrase(
                    words, generic_verbs, incomplete_endings, generic_words,
                    generic_single_words, weak_phrase_words, weak_two_word_adverbs
                ):
                    phrase_keywords.append(kw)
            # Handle single-word keywords
            else:
                if self._should_keep_single_word(
                    kw, min_length_single, generic_words, generic_single_words,
                    domain_stop_words, single_word_exclusions
                ):
                    single_keywords.append(kw)

        # Combine phrases and single keywords
        # NOTE: Previous deduplication was too aggressive - it removed single words like "hooks"
        # because they appeared as substrings in phrases like "configuring hooks".
        # But single words are important for search recall, so we keep both.
        # The max_keywords limit already controls total keywords.
        cleaned = phrase_keywords + single_keywords

        # Sort priority:
        # 1. Multi-word phrases (highest priority)
        # 2. Hyphenated single words (path-based keywords like "sub-agents", "tool-use")
        # 3. Regular single words (lowest priority)
        # Within each category, priority keywords (from filename) come first
        priority_lower = {pk.lower() for pk in priority_keywords}

        def sort_key(x):
            x_lower = x.lower()
            has_space = ' ' in x
            has_hyphen = '-' in x and ' ' not in x
            is_priority = x_lower in priority_lower
            return (
                not is_priority,  # Priority keywords first (False < True)
                not has_space and not has_hyphen,  # Phrases first, then hyphenated, then regular
                not has_hyphen,  # Among non-phrases, hyphenated first
                -len(x),  # Longer words first
                x  # Then alphabetically
            )

        cleaned_sorted = sorted(set(cleaned), key=sort_key)[:max_keywords]

        return cleaned_sorted

    def extract_keywords(self, track_stats: bool = False) -> Union[list[str], tuple[list[str], dict]]:
        """
        Extract meaningful keywords from content using multi-source extraction strategy.
        
        ## Extraction Strategy (7 Sources, Prioritized by Reliability)
        
        The extraction process uses 7 sources in decreasing order of trust/reliability:
        
        1. **Technical Phrases** (Highest Trust)
           - Multi-word technical terms from filtering.yaml (e.g., "context window", "agent skills")
           - Preserved without filtering - domain-specific and high precision
           - Source: Config-defined terms found in title/description/body
        
        2. **Frontmatter Keywords/Tags** (Author-Provided)
           - Explicitly provided by document authors in YAML frontmatter
           - Highest human signal, no filtering applied
           - Source: YAML frontmatter 'keywords' and 'tags' fields
        
        3. **Title & Description** (High Signal-to-Noise)
           - Meaningful words from document title (3+ chars)
           - Technical terms from first paragraph (5+ chars)
           - Source: H1 heading or frontmatter title, first non-heading paragraph
        
        4. **YAKE Automatic Extraction** (ML-Based, If Available)
           - Unsupervised keyword extraction using YAKE library
           - Extracts 1-3 word n-grams ranked by relevance
           - Only runs if yake installed and text >= 50 chars
           - Source: Body content after markdown removal
        
        5. **Heading Keywords** (Structural Importance)
           - Multi-word phrases from h1-h6 headings (max 10 phrases)
           - Single words from headings (max 8 words)
           - File tokens like "claude.md" from headings (max 4 tokens)
           - Source: All heading levels, prioritizes phrases over single words
        
        6. **Filename** (Semantic Meaning)
           - Meaningful parts of filename (3+ chars, not stop words)
           - Filters common doc terms (md, doc, guide, api, etc.)
           - Source: File stem split on hyphens/underscores
        
        7. **Body Content** (Last Resort, Frequency-Based)
           - Technical terms appearing 2+ times (5+ chars)
           - Only extracted if insufficient keywords from other sources
           - Limited to top 6 terms by frequency and length
           - Source: Body text after markdown removal
        
        ## Filtering & Cleaning
        
        After extraction, keywords are filtered using rules from filtering.yaml:
        - Remove stop phrases (noise patterns)
        - Remove generic verbs, incomplete endings, weak words
        - Remove domain-specific exclusions
        - Preserve technical phrases without filtering
        - Deduplicate: remove single words contained in phrases
        
        ## Output
        
        Returns up to 12 keywords (configurable in defaults.yaml):
        - Multi-word phrases prioritized over single words
        - Longer keywords prioritized over shorter (more specific)
        - Alphabetically sorted within priority groups
        
        ## Configuration
        
        All limits configurable in defaults.yaml keyword_extraction section:
        - max_heading_phrases, max_heading_keywords, max_file_tokens
        - max_body_keywords, max_total_keywords
        - YAKE parameters (language, max_ngram_size, etc.)

        Args:
            track_stats: If True, return statistics about extraction methods used

        Returns:
            Tuple of (keywords list, stats dict) if track_stats=True, else just keywords list
        """
        keywords: set[str] = set()

        # Get stop words from library + config (may use cached spaCy list)
        stop_words = self._get_stop_words()

        # Treat "spaCy used" as either a direct import or having a large stop-word set
        # (we avoid spawning a separate Python process per document).
        spacy_actually_used = SPACY_AVAILABLE or len(stop_words) > 200

        # Initialize statistics
        stats = {
            'yake_used': False,
            'spacy_used': spacy_actually_used,
            'yake_keywords_count': 0,
            'frontmatter_keywords_count': 0,
            'heading_keywords_count': 0,
            'title_desc_keywords_count': 0,
            'body_content_keywords_count': 0,
            'filename_keywords_count': 0,
        }

        # Get filtering lists from config
        filters = self._get_filtering_lists()

        # Extract technical phrases first (preserve multi-word technical terms)
        technical_phrases_kw = self._extract_technical_phrases()
        keywords.update(technical_phrases_kw)
        stats['technical_phrases_count'] = len(technical_phrases_kw)

        # Extract keywords from various sources
        frontmatter_kw, frontmatter_count = self._extract_frontmatter_keywords(stop_words)
        keywords.update(frontmatter_kw)
        stats['frontmatter_keywords_count'] = frontmatter_count

        title_desc_kw, title_desc_count = self._extract_title_desc_keywords(stop_words)
        keywords.update(title_desc_kw)
        stats['title_desc_keywords_count'] = title_desc_count

        yake_kw, yake_used, yake_count = self._extract_with_yake(stop_words, filters)
        keywords.update(yake_kw)
        stats['yake_used'] = yake_used
        stats['yake_keywords_count'] = yake_count

        heading_kw, heading_count = self._extract_heading_keywords(stop_words, filters)
        keywords.update(heading_kw)
        stats['heading_keywords_count'] = heading_count

        filename_kw, filename_count = self._extract_filename_keywords(stop_words)
        keywords.update(filename_kw)
        stats['filename_keywords_count'] = filename_count

        body_kw, body_count = self._extract_body_keywords(keywords, stop_words)
        keywords.update(body_kw)
        stats['body_content_keywords_count'] = body_count

        # Filter and clean keywords (filename keywords get priority in sorting)
        cleaned_keywords = self._filter_and_clean_keywords(keywords, stop_words, filters, filename_kw)

        if track_stats:
            return cleaned_keywords, stats
        return cleaned_keywords
    
    def extract_tags(self) -> list[str]:
        """
        Extract tags for categorization
        
        Sources:
        1. Frontmatter 'tags'
        2. Auto-categorize from path/domain
        """
        tags: set[str] = set()
        
        # From frontmatter
        if 'tags' in self.frontmatter:
            frontmatter_tags = self.frontmatter['tags']
            if isinstance(frontmatter_tags, list):
                tags.update(str(t).lower().strip() for t in frontmatter_tags)
            elif isinstance(frontmatter_tags, str):
                tags.update(t.lower().strip() for t in frontmatter_tags.split(','))
        
        # Auto-categorize from path (use forward slashes for cross-platform)
        # CRITICAL: Use only the relative path from canonical/ to avoid false positives
        # from directory names (e.g., ".claude/skills/" should not trigger "skills" tag)
        path_str_full = self.file_path.as_posix().lower()
        
        # Extract relative path from canonical/ onwards
        if 'canonical/' in path_str_full:
            # Get everything after 'canonical/'
            path_str = path_str_full.split('canonical/', 1)[1]
        else:
            # Fallback to filename only if canonical/ not in path
            path_str = self.file_path.name.lower()
        
        path_tags = set()
        
        # Check path patterns from config
        tag_config = self._tag_config.get('tags', {})
        for tag_name, tag_config_data in tag_config.items():
            # Skip reference tag (handled separately)
            if tag_name == 'reference':
                continue
            
            # Check path patterns if defined
            # Note: Path-based detection is now handled in extract_category
            # But we can add path-based tags here if needed
            pass
        
        # Simple path-based tags (keep for backward compatibility)
        # NOTE: 'api' path-based detection removed - now controlled by content-based
        # detection with min_mentions threshold in tag_detection.yaml to reduce over-tagging
        # if 'api' in path_str or '/api/' in path_str:
        #     path_tags.add('api')
        if 'skill' in path_str:
            path_tags.add('skills')
        if 'subagent' in path_str:
            path_tags.add('subagents')
        if 'guide' in path_str or 'tutorial' in path_str:
            path_tags.add('guides')
        if 'reference' in path_str:
            path_tags.add('reference')
        if 'research' in path_str:
            path_tags.add('research')
        if 'engineering' in path_str:
            path_tags.add('engineering')
        
        tags.update(path_tags)
        
        # Content-based tag extraction using config
        body_lower = self.body.lower()
        content_tags = []
        
        # Count occurrences for more selective tagging
        def count_mentions(terms):
            count = 0
            for term in terms:
                count += body_lower.count(term)
            return count
        
        # Use tag detection config
        for tag_name, tag_config_data in tag_config.items():
            if tag_name == 'reference':
                continue  # Handled separately
            
            terms = tag_config_data.get('terms', [])
            min_mentions = tag_config_data.get('min_mentions', 2)
            
            # Check main terms
            if count_mentions(terms) >= min_mentions:
                content_tags.append(tag_name)
            # Check additional terms if defined (for troubleshooting)
            elif 'additional_terms' in tag_config_data:
                additional_terms = tag_config_data.get('additional_terms', [])
                additional_min = tag_config_data.get('additional_min_mentions', 3)
                if count_mentions(additional_terms) >= additional_min:
                    content_tags.append(tag_name)
        
        # Add content-based tags (prioritize path-based tags)
        tags.update(content_tags)
        
        # Remove 'reference' tag if other tags exist (too generic)
        if len(tags) > 1 and 'reference' in tags:
            tags.remove('reference')
        
        # Limit total tags to 5-6 most relevant
        # Priority: frontmatter > path-based > content-based
        if len(tags) > 6:
            # Sort by priority: frontmatter first, then path-based, then content-based
            tag_priority = []
            frontmatter_tags_set = set()
            if 'tags' in self.frontmatter:
                frontmatter_tags = self.frontmatter['tags']
                if isinstance(frontmatter_tags, list):
                    frontmatter_tags_set = {str(t).lower().strip() for t in frontmatter_tags}
                elif isinstance(frontmatter_tags, str):
                    frontmatter_tags_set = {t.lower().strip() for t in frontmatter_tags.split(',')}
            
            path_tags_set = {'api', 'skills', 'guides', 'reference', 'research', 'engineering'}

            # Priority order: frontmatter > path > content
            for tag in sorted(tags):
                if tag in frontmatter_tags_set:
                    tag_priority.append((0, tag))  # Highest priority
                elif tag in path_tags_set:
                    tag_priority.append((1, tag))  # Medium priority
                else:
                    tag_priority.append((2, tag))  # Lower priority
            
            # Sort by priority and take top 6
            tag_priority.sort(key=lambda x: x[0])
            tags = {tag for _, tag in tag_priority[:6]}
        
        # Only add 'reference' if no other tags found
        if not tags:
            tags.add('reference')
        
        return sorted(tags)
    
    def extract_category(self) -> str | None:
        """
        Auto-detect category from path/domain/content
        
        Categories: skills, api, guides, research, engineering, news
        """
        # Check frontmatter
        if 'category' in self.frontmatter:
            return str(self.frontmatter['category']).lower().strip()
        
        # From path (use forward slashes for cross-platform)
        # CRITICAL: Use only the relative path from canonical/ to avoid false positives
        path_str_full = self.file_path.as_posix().lower()
        
        # Extract relative path from canonical/ onwards
        if 'canonical/' in path_str_full:
            path_str = path_str_full.split('canonical/', 1)[1]
        else:
            path_str = self.file_path.name.lower()
        
        # Use category config for path-based detection
        category_config = self._tag_config.get('categories', {})
        for category_name, category_data in category_config.items():
            path_patterns = category_data.get('path_patterns', [])
            for pattern in path_patterns:
                if pattern in path_str or f'/{pattern}/' in path_str:
                    return category_name

        # Check title for category indicators (before tag inference)
        # This ensures "Hooks reference" → "api" rather than "installation"
        title = self.extract_title()
        if title:
            title_lower = title.lower()
            if 'reference' in title_lower:
                return 'api'
            if 'guide' in title_lower or 'tutorial' in title_lower:
                return 'guides'

        # Infer category from tags (if path didn't provide one)
        tags = self.extract_tags()
        for category_name, category_data in category_config.items():
            tag_mapping = category_data.get('tag_mapping', [])
            if any(tag in tags for tag in tag_mapping):
                return category_name
        
        # Infer from title/description keywords using config
        title = self.extract_title()
        description = self.extract_description()
        content_lower = (title + ' ' + (description or '')).lower()
        
        for category_name, category_data in category_config.items():
            content_terms = category_data.get('content_terms', [])
            if any(term in content_lower for term in content_terms):
                return category_name
        
        return None
    
    def extract_domain(self) -> str | None:
        """Extract domain from URL or infer from file path.

        First tries URL-based extraction. If URL is not available,
        falls back to inferring domain from the file path structure.
        Path structure: canonical/{domain-slug}/... -> domain.com
        """
        # First try URL-based extraction
        if self.url:
            try:
                parsed = urlparse(self.url)
                domain = parsed.netloc
                # Remove www. prefix
                if domain.startswith('www.'):
                    domain = domain[4:]
                return domain
            except Exception:
                pass

        # Fallback: Infer domain from file path
        # Path structure: canonical/{domain-slug}/...
        # e.g., docs-claude-com/docs/en/... -> docs.claude.com
        try:
            path_str = str(self.file_path.as_posix()).lower()

            # Map path segments to domains
            domain_mappings = {
                'docs-claude-com': 'docs.claude.com',
                'code-claude-com': 'code.claude.com',
                'platform-claude-com': 'platform.claude.com',
                'anthropic-com': 'anthropic.com',
            }

            for path_segment, domain in domain_mappings.items():
                if path_segment in path_str:
                    return domain
        except Exception:
            pass

        return None
    
    def extract_subsections(self) -> list[dict[str, any]]:
        """
        Extract subsections (h2 and h3 headings) with their metadata.

        Subsections enable discovery of content within documents, making it possible
        to find that "plugins.md contains a Skills subsection" or similar.

        Returns:
            List of subsection dictionaries with keys:
            - heading: Heading text
            - level: Heading level (2 or 3)
            - anchor: URL anchor (e.g., "#add-skills-to-your-plugin")
            - keywords: Keywords extracted from subsection content
        """
        subsections = []

        # Find all h2 and h3 headings
        heading_pattern = re.compile(r'^(#{2,3})\s+(.+)$', re.MULTILINE)
        matches = list(heading_pattern.finditer(self.body))

        if not matches:
            return []

        # Get stop words for keyword extraction
        stop_words = self._get_stop_words()

        # Process each heading
        for i, match in enumerate(matches):
            level = len(match.group(1))  # Number of # characters
            heading_text = match.group(2).strip()

            # Only extract h2 and h3
            if level not in [2, 3]:
                continue

            # Create anchor (lowercase, hyphens for spaces, remove special chars)
            anchor = '#' + re.sub(r'[^\w\s-]', '', heading_text.lower()).strip().replace(' ', '-')
            
            # Extract keywords from heading (simple word extraction)
            heading_words = re.findall(r'\b[a-z]{3,}\b', heading_text.lower())
            heading_keywords = [w for w in heading_words if w not in stop_words and len(w) >= 3]
            
            # Get subsection content (from this heading to next same-or-higher level heading)
            start_pos = match.end()
            end_pos = len(self.body)
            
            # Find next heading at same or higher level
            for next_match in matches[i+1:]:
                next_level = len(next_match.group(1))
                if next_level <= level:
                    end_pos = next_match.start()
                    break
            
            subsection_content = self.body[start_pos:end_pos].strip()
            
            # Extract additional keywords from subsection content (first 500 chars for efficiency)
            content_sample = subsection_content[:500].lower()
            content_words = re.findall(r'\b[a-z]{4,}\b', content_sample)
            content_keywords = [w for w in content_words if w not in stop_words and len(w) >= 4]
            
            # Combine and deduplicate keywords (limit to top 5 most relevant)
            all_keywords = heading_keywords + content_keywords[:3]  # Heading keywords + top 3 from content
            unique_keywords = list(dict.fromkeys(all_keywords))[:5]  # Preserve order, limit to 5
            
            subsections.append({
                'heading': heading_text,
                'level': level,
                'anchor': anchor,
                'keywords': unique_keywords
            })
        
        return subsections
    
    def extract_all(self, track_stats: bool = False) -> dict:
        """
        Extract all metadata

        Args:
            track_stats: If True, include extraction statistics in return value

        Returns:
            Dictionary with all extracted metadata (and '_stats' key if track_stats=True)
        """
        keywords_result = self.extract_keywords(track_stats=track_stats)
        if track_stats:
            keywords, stats = keywords_result
        else:
            keywords = keywords_result

        metadata = {
            'title': self.extract_title(),
            'description': self.extract_description(),
            'keywords': keywords,
            'tags': self.extract_tags(),
            'category': self.extract_category(),
            'domain': self.extract_domain(),
            'subsections': self.extract_subsections(),
        }

        if track_stats:
            metadata['_stats'] = stats

        # Remove None values (but keep _stats)
        result = {}
        for k, v in metadata.items():
            if k == '_stats':
                result[k] = v
            elif v is not None and v != []:
                result[k] = v

        return result

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Extract metadata from markdown file',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('file_path', help='Path to markdown file')
    parser.add_argument('--url', help='Source URL (for domain extraction)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--stats', action='store_true', help='Include extraction statistics (keyword sources, NLP methods used)')

    args = parser.parse_args()
    
    # Log script start
    logger.start({
        'file_path': str(args.file_path),
        'url': args.url,
        'json': args.json
    })
    
    exit_code = 0
    try:
        file_path = Path(args.file_path)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            exit_code = 1
            raise SystemExit(1)
        
        with logger.time_operation('extract_metadata'):
            extractor = MetadataExtractor(file_path, args.url)
            metadata = extractor.extract_all(track_stats=args.stats)

        # Extract stats if tracked (for display/logging)
        extraction_stats = metadata.pop('_stats', None) if args.stats else None

        if args.json:
            import json
            output = metadata
            if extraction_stats:
                output['_extraction_stats'] = extraction_stats
            print(json.dumps(output, indent=2))
        else:
            print("📋 Extracted Metadata:")
            for key, value in metadata.items():
                if isinstance(value, list):
                    print(f"  {key}: {', '.join(str(v) for v in value)}")
                else:
                    print(f"  {key}: {value}")

            # Display extraction stats if requested
            if extraction_stats:
                print("\n📊 Extraction Statistics:")
                nlp_status = []
                if extraction_stats.get('spacy_used'):
                    nlp_status.append("spaCy")
                if extraction_stats.get('yake_used'):
                    nlp_status.append("YAKE")
                print(f"  NLP methods: {', '.join(nlp_status) if nlp_status else 'None (basic extraction)'}")

                print("  Keyword sources:")
                sources = [
                    ('technical_phrases_count', 'Technical phrases'),
                    ('frontmatter_keywords_count', 'Frontmatter'),
                    ('title_desc_keywords_count', 'Title/Description'),
                    ('yake_keywords_count', 'YAKE extraction'),
                    ('heading_keywords_count', 'Headings'),
                    ('filename_keywords_count', 'Filename/Path'),
                    ('body_content_keywords_count', 'Body content'),
                ]
                for key, label in sources:
                    count = extraction_stats.get(key, 0)
                    if count > 0:
                        print(f"    - {label}: {count}")
        
        summary = {
            'fields_extracted': len(metadata),
            'has_title': 'title' in metadata and metadata['title'],
            'has_keywords': 'keywords' in metadata and len(metadata.get('keywords', [])) > 0,
            'has_tags': 'tags' in metadata and len(metadata.get('tags', [])) > 0
        }
        
        logger.end(exit_code=exit_code, summary=summary)
        
    except SystemExit:
        raise
    except Exception as e:
        logger.log_error("Fatal error in extract_metadata", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()

