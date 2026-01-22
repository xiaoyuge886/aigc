#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search_constants.py - Search scoring constants for doc_resolver.py

Centralized constants for search relevance scoring. Tuning these values
affects search result ranking across all documentation queries.

These dataclasses provide frozen, immutable configuration that can be imported
and used across multiple files for consistent scoring behavior.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TitleScores:
    """Scores for keyword matches in document titles."""
    exact_match: int = 6          # Substring match in title
    word_boundary_match: int = 4  # Word boundary match in title


@dataclass(frozen=True)
class DescriptionScores:
    """Scores for keyword matches in document descriptions."""
    exact_match: int = 2          # Substring match in description
    word_boundary_match: int = 1  # Word boundary match in description


@dataclass(frozen=True)
class KeywordScores:
    """Scores for matches against document keywords."""
    variant_match: int = 5        # Match via keyword variants
    token_match: int = 3          # Match via keyword tokens
    substring_match: int = 2      # Substring match in keyword value


@dataclass(frozen=True)
class TagScores:
    """Scores for matches against document tags."""
    exact_match: int = 4          # Exact tag match
    variant_match: int = 3        # Variant match in tags


@dataclass(frozen=True)
class IdentifierScores:
    """Scores for matches in doc_id and path identifiers."""
    identifier_match: int = 6     # Match in doc_id tokens
    path_url_match: int = 1       # Match in path or URL


@dataclass(frozen=True)
class GenericPenalties:
    """Penalty multipliers for generic/broad search terms.

    Generic terms like 'configuration', 'setup', 'guide' are too broad
    and cause ranking collapse when mixed with specific terms.
    """
    only_generic: float = 0.1     # Only generic terms matched (severe penalty)
    high_ratio: float = 0.4       # >= 50% generic terms
    medium_ratio: float = 0.7     # >= 30% generic terms
    # Thresholds for ratio calculation
    high_threshold: float = 0.5   # Threshold for high_ratio penalty
    medium_threshold: float = 0.3 # Threshold for medium_ratio penalty


@dataclass(frozen=True)
class CoverageMultipliers:
    """Multipliers based on query term coverage.

    Boosts docs that match ALL query terms over docs that match only SOME.
    """
    all_in_title: float = 2.0     # ALL terms in title/description
    all_terms: float = 1.5        # All terms matched across metadata
    most_terms: float = 1.2       # >= 67% terms matched
    partial: float = 1.0          # Partial match (no boost)
    # Threshold for "most" coverage
    most_threshold: float = 0.67


@dataclass(frozen=True)
class SubsectionScores:
    """Scores and bonuses for subsection matching.

    Subsections (h2/h3 headings) provide fine-grained discovery.
    Bonuses are tiered by match quality (substantive > main_content > default).
    """
    # All keywords in heading
    all_kw_in_heading: int = 10
    # Bonuses when all keywords match heading
    bonus_all_substantive: int = 20   # Has substantive match
    bonus_all_main_content: int = 8   # Has main content match
    bonus_all_default: int = 5        # Default bonus

    # Single keyword in heading
    single_kw_in_heading: int = 4
    # Bonuses when single keyword matches heading
    bonus_single_substantive: int = 15
    bonus_single_main_content: int = 6
    bonus_single_default: int = 3

    # All keywords in subsection keywords
    all_kw_in_keywords: int = 8
    # Bonuses when all keywords match subsection keywords
    bonus_kw_all_substantive: int = 18
    bonus_kw_all_main_content: int = 7
    bonus_kw_all_default: int = 4

    # Single keyword in subsection keywords
    single_kw_in_keywords: int = 3
    # Bonuses when single keyword matches subsection keywords
    bonus_kw_single_substantive: int = 12
    bonus_kw_single_main_content: int = 5
    bonus_kw_single_default: int = 2


@dataclass(frozen=True)
class PositionalScores:
    """Scores for positional tiebreaking.

    Earlier keyword position = higher bonus.
    Bonus is small to avoid affecting main ranking, but enough to break ties.
    Formula: max_bonus / (position + 1)
    """
    max_bonus: float = 0.5


# Singleton instances for import
TITLE = TitleScores()
DESCRIPTION = DescriptionScores()
KEYWORD = KeywordScores()
TAG = TagScores()
IDENTIFIER = IdentifierScores()
PENALTIES = GenericPenalties()
COVERAGE = CoverageMultipliers()
SUBSECTION = SubsectionScores()
POSITIONAL = PositionalScores()
