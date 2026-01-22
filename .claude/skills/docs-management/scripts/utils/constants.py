"""Shared constants for docs-management scripts.

This module provides centralized constants to avoid magic numbers
and ensure consistency across the codebase.
"""

from typing import Final

# =============================================================================
# Run ID Configuration
# =============================================================================
# Length of the generated run ID (hex characters from UUID4)
# Used for session correlation across processes
RUN_ID_LENGTH: Final[int] = 8

# =============================================================================
# Percentile Thresholds
# =============================================================================
# Standard percentile thresholds for performance metrics
PERCENTILE_P50: Final[float] = 0.50
PERCENTILE_P90: Final[float] = 0.90
PERCENTILE_P99: Final[float] = 0.99

# =============================================================================
# Time Conversion
# =============================================================================
# Milliseconds per second (for duration conversions)
MS_PER_SECOND: Final[int] = 1000

# Seconds per minute
SECONDS_PER_MINUTE: Final[int] = 60

# Seconds per hour
SECONDS_PER_HOUR: Final[int] = 3600
