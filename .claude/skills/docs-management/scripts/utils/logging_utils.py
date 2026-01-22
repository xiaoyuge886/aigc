#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
logging_utils.py - Common logging and observability utilities for docs-management scripts

Provides structured logging, performance tracking, and observability features
for all scripts in the docs-management skill.

Enhanced with file-based logging for better observability:
- Log files stored in .claude/skills/docs-management/logs/ (gitignored)
- Categories: scrape, index, search, diagnostics
- JSON logging option for machine parsing
- Configurable via config/runtime.yaml (env vars override for CI/CD)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import logging
import logging.handlers
import os
import threading
import time
import functools
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Literal
from contextlib import contextmanager

from .script_utils import configure_utf8_output, format_duration, HTTP_STATUS_RATE_LIMITED
from .constants import RUN_ID_LENGTH, PERCENTILE_P50, PERCENTILE_P90, PERCENTILE_P99

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

# Log categories for file-based logging
LOG_CATEGORIES = Literal["scrape", "index", "search", "diagnostics"]

# Environment variables for correlation across processes
RUN_ID_ENV_VAR = "CLAUDE_DOCS_RUN_ID"
SOURCE_NAME_ENV_VAR = "CLAUDE_DOCS_SOURCE_NAME"

# Error classification categories for structured error logging
class ErrorCategory:
    """Standardized error categories for observability and analysis."""
    NETWORK = "network"          # Connection, timeout, DNS issues
    HTTP = "http"                # HTTP 4xx/5xx errors
    PARSE = "parse"              # JSON, YAML, XML, HTML parsing failures
    FILE_IO = "file_io"          # File read/write/permission errors
    CONFIG = "config"            # Configuration or validation errors
    RATE_LIMIT = "rate_limit"    # Rate limiting (429 responses)
    TIMEOUT = "timeout"          # Request or operation timeouts
    VALIDATION = "validation"    # Data validation failures
    UNKNOWN = "unknown"          # Uncategorized errors

def classify_error(error: Exception | None) -> str:
    """
    Classify an exception into a standard error category.

    Args:
        error: The exception to classify

    Returns:
        One of the ErrorCategory constants
    """
    if error is None:
        return ErrorCategory.UNKNOWN

    error_type = type(error).__name__
    error_str = str(error).lower()

    # Network-level errors
    if error_type in ('ConnectionError', 'ConnectionResetError', 'ConnectionRefusedError',
                      'NewConnectionError', 'MaxRetryError', 'SSLError', 'ProxyError'):
        return ErrorCategory.NETWORK

    # Timeout errors
    if error_type in ('Timeout', 'ReadTimeout', 'ConnectTimeout', 'TimeoutError'):
        return ErrorCategory.TIMEOUT

    # HTTP errors - check status code if available
    if error_type == 'HTTPError':
        if hasattr(error, 'response') and error.response is not None:
            status_code = error.response.status_code
            if status_code == HTTP_STATUS_RATE_LIMITED:
                return ErrorCategory.RATE_LIMIT
            if 400 <= status_code < 600:
                return ErrorCategory.HTTP
        return ErrorCategory.HTTP

    # Parse errors
    if error_type in ('JSONDecodeError', 'YAMLError', 'XMLSyntaxError', 'ParseError',
                      'ParserError', 'ScannerError', 'ComposerError'):
        return ErrorCategory.PARSE
    if 'json' in error_str and ('decode' in error_str or 'parse' in error_str):
        return ErrorCategory.PARSE
    if 'yaml' in error_str and ('parse' in error_str or 'scan' in error_str):
        return ErrorCategory.PARSE

    # File I/O errors
    if error_type in ('FileNotFoundError', 'PermissionError', 'IsADirectoryError',
                      'NotADirectoryError', 'IOError', 'BlockingIOError'):
        return ErrorCategory.FILE_IO
    if error_type == 'OSError' and ('file' in error_str or 'path' in error_str
                                     or 'directory' in error_str):
        return ErrorCategory.FILE_IO

    # Config/validation errors
    if error_type in ('ValueError', 'TypeError', 'KeyError', 'AttributeError'):
        if 'config' in error_str or 'setting' in error_str or 'option' in error_str:
            return ErrorCategory.CONFIG
        return ErrorCategory.VALIDATION
    if error_type in ('ValidationError', 'ConfigError', 'ConfigurationError'):
        return ErrorCategory.CONFIG

    return ErrorCategory.UNKNOWN

# Resolve paths (relative to skill root)
_SKILL_DIR = Path(__file__).resolve().parents[2]
_LOGS_DIR = _SKILL_DIR / "logs"
_CONFIG_DIR = _SKILL_DIR / "config"
_RUNTIME_CONFIG_PATH = _CONFIG_DIR / "runtime.yaml"

# Cached runtime config (loaded once)
_runtime_config: dict[str, Any] | None = None

def _load_runtime_config() -> dict[str, Any]:
    """Load runtime config from config/runtime.yaml with caching."""
    global _runtime_config
    if _runtime_config is not None:
        return _runtime_config

    _runtime_config = {}
    if _RUNTIME_CONFIG_PATH.exists():
        try:
            import yaml
            with open(_RUNTIME_CONFIG_PATH, 'r', encoding='utf-8') as f:
                _runtime_config = yaml.safe_load(f) or {}
        except Exception:
            # Silently fall back to defaults if config can't be loaded
            pass
    return _runtime_config

def _get_runtime_value(section: str, key: str, default: Any = None) -> Any:
    """Get a value from runtime config with nested key support."""
    config = _load_runtime_config()
    try:
        value = config.get(section, {})
        if isinstance(value, dict):
            return value.get(key, default)
        return default
    except (AttributeError, TypeError):
        # Config might not be a dict if YAML parsing returned unexpected type
        return default

def _get_runtime_nested(section: str, subsection: str, key: str, default: Any = None) -> Any:
    """Get a deeply nested value from runtime config."""
    config = _load_runtime_config()
    try:
        return config.get(section, {}).get(subsection, {}).get(key, default)
    except (AttributeError, TypeError):
        # Config might not be a dict if YAML parsing returned unexpected type
        return default

# Environment variables override config file (for CI/CD flexibility)
# CLAUDE_DOCS_LOG_TO_FILE: "true" to enable file logging
# CLAUDE_DOCS_LOG_LEVEL: DEBUG, INFO, WARNING, ERROR
# CLAUDE_DOCS_LOG_JSON: "true" for JSON format

def _get_config_bool(config_section: str, config_key: str, env_var: str, default: bool = False) -> bool:
    """Get boolean from env var (if set) or config file."""
    env_value = os.environ.get(env_var, "").lower()
    if env_value in ("true", "1", "yes", "on"):
        return True
    elif env_value in ("false", "0", "no", "off"):
        return False
    # Fall back to config file
    return bool(_get_runtime_value(config_section, config_key, default))

def _get_config_int(config_section: str, config_key: str, env_var: str, default: int) -> int:
    """Get integer from env var (if set) or config file."""
    env_value = os.environ.get(env_var)
    if env_value:
        try:
            return int(env_value)
        except (ValueError, TypeError):
            pass
    # Fall back to config file
    return int(_get_runtime_value(config_section, config_key, default))

def _get_log_level() -> int:
    """Get logging level from env var or config file."""
    # Check env var first
    env_level = os.environ.get("CLAUDE_DOCS_LOG_LEVEL", "").upper()
    if env_level:
        return getattr(logging, env_level, logging.INFO)
    # Fall back to config file
    config_level = _get_runtime_value("logging", "level", "INFO")
    if isinstance(config_level, str):
        return getattr(logging, config_level.upper(), logging.INFO)
    return logging.INFO

class SourceAwareFormatter(logging.Formatter):
    """Formatter that adds source name and run_id to log records.

    This formatter resolves interleaved parallel output by adding source
    identification to each log line, making it easy to follow which worker
    produced which log entry.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with source name and run_id."""
        # Add run_id from environment
        record.run_id = os.environ.get(RUN_ID_ENV_VAR, 'unknown')
        # Add source name from environment (set by parallel workers)
        record.source = os.environ.get(SOURCE_NAME_ENV_VAR, record.name)
        return super().format(record)

class LazyRotatingFileHandler(logging.Handler):
    """A handler wrapper that defers file creation until first write.

    This prevents empty 0-byte log files from being created when a logger
    is set up but never used (common in per-source logging for parallel workers).

    The actual RotatingFileHandler is only created when emit() is first called.
    """

    def __init__(
        self,
        filename: str | Path,
        maxBytes: int = 0,
        backupCount: int = 0,
        encoding: str | None = None,
    ):
        """Initialize lazy handler with deferred file creation.

        Args:
            filename: Path to the log file (created on first write)
            maxBytes: Max size before rotation (passed to RotatingFileHandler)
            backupCount: Number of backup files to keep
            encoding: File encoding (default: utf-8)
        """
        super().__init__()
        self._filename = Path(filename)
        self._maxBytes = maxBytes
        self._backupCount = backupCount
        self._encoding = encoding or 'utf-8'
        self._real_handler: logging.handlers.RotatingFileHandler | None = None
        self._initialized = False

    def _ensure_handler(self) -> logging.handlers.RotatingFileHandler:
        """Create the real file handler on first use."""
        if self._real_handler is None:
            # Ensure parent directory exists
            self._filename.parent.mkdir(parents=True, exist_ok=True)

            # Create the actual rotating file handler
            self._real_handler = logging.handlers.RotatingFileHandler(
                self._filename,
                maxBytes=self._maxBytes,
                backupCount=self._backupCount,
                encoding=self._encoding,
            )
            # Copy formatter and level from this wrapper
            if self.formatter:
                self._real_handler.setFormatter(self.formatter)
            self._real_handler.setLevel(self.level)
            self._initialized = True
        return self._real_handler

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record, creating the file handler if needed."""
        try:
            handler = self._ensure_handler()
            handler.emit(record)
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        """Close the underlying handler if it was created."""
        if self._real_handler is not None:
            self._real_handler.close()
        super().close()

    def setFormatter(self, fmt: logging.Formatter | None) -> None:
        """Set formatter on both wrapper and real handler (if exists)."""
        super().setFormatter(fmt)
        if self._real_handler is not None:
            self._real_handler.setFormatter(fmt)

    def setLevel(self, level: int) -> None:
        """Set level on both wrapper and real handler (if exists)."""
        super().setLevel(level)
        if self._real_handler is not None:
            self._real_handler.setLevel(level)

class JSONFormatter(logging.Formatter):
    """JSON formatter for machine-readable logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,  # Add PID for correlating parallel executions
        }

        # Add run_id if available in environment (for session correlation)
        run_id = os.environ.get(RUN_ID_ENV_VAR)
        if run_id:
            log_data["run_id"] = run_id

        # Add source name if available (for parallel worker correlation)
        source_name = os.environ.get(SOURCE_NAME_ENV_VAR)
        if source_name:
            log_data["source"] = source_name

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)

class ScriptLogger:
    """Provide enhanced logger with performance tracking and structured logging.

    Enhanced with file-based logging for better observability:
    - Automatic file logging to .claude/skills/docs-management/logs/
    - Log rotation with configurable size and backup count
    - JSON format option for machine parsing
    - HTTP request timing tracking
    - Operation-level diagnostics
    """

    def __init__(
        self,
        script_name: str,
        log_level: int = logging.INFO,
        log_category: str | None = None,
        enable_file_logging: bool | None = None,
        json_format: bool | None = None,
        run_id: str | None = None,
    ):
        """
        Initialize logger for a script.

        Args:
            script_name: Name of the script (usually __file__)
            log_level: Logging level (default: INFO)
            log_category: Log category for file output (scrape, index, search, diagnostics)
            enable_file_logging: Override env var to enable/disable file logging
            json_format: Override env var for JSON format
            run_id: Session correlation ID (auto-generated or inherited from env)
        """
        self.script_name = Path(script_name).stem if script_name else 'unknown'
        self.start_time = None
        self.end_time = None
        self.performance_metrics: dict[str, Any] = {}
        self.http_timings: list[dict[str, Any]] = []
        self.log_category = log_category

        # Run ID for session correlation across processes
        # Priority: explicit parameter > environment variable > generate new
        if run_id:
            self.run_id = run_id
        elif os.environ.get(RUN_ID_ENV_VAR):
            self.run_id = os.environ[RUN_ID_ENV_VAR]
        else:
            # Generate short run_id (RUN_ID_LENGTH chars from UUID for readability)
            self.run_id = uuid.uuid4().hex[:RUN_ID_LENGTH]
            # Set in environment for child processes to inherit
            os.environ[RUN_ID_ENV_VAR] = self.run_id

        # Determine settings from config file (env vars override for CI/CD)
        self._enable_file_logging = (
            enable_file_logging if enable_file_logging is not None
            else _get_config_bool("logging", "enable_file_logging", "CLAUDE_DOCS_LOG_TO_FILE", False)
        )
        self._json_format = (
            json_format if json_format is not None
            else _get_config_bool("logging", "json_format", "CLAUDE_DOCS_LOG_JSON", False)
        )
        self._write_diagnostics = _get_runtime_value("diagnostics", "write_diagnostics_files", False)
        # HTTP timing: env var CLAUDE_DOCS_HTTP_TIMING overrides config (for --with-timing flag)
        self._track_http = _get_config_bool("diagnostics", "track_http_timings", "CLAUDE_DOCS_HTTP_TIMING", True)

        # Setup logger
        self.logger = logging.getLogger(self.script_name)
        self.logger.setLevel(log_level)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            # Console handler with formatted output
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)

            # Format: [TIMESTAMP] [LEVEL] [SOURCE] [RUN_ID] message
            # Source name makes parallel output readable by showing which worker produced each line
            # Use SourceAwareFormatter to inject source and run_id from environment
            formatter = SourceAwareFormatter(
                '[%(asctime)s] [%(levelname)s] [%(source)s] [%(run_id)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # Add file handler if enabled
            if self._enable_file_logging:
                self._add_file_handler(log_level)

    def _add_file_handler(self, log_level: int) -> None:
        """Add rotating file handler for persistent logging.

        When CLAUDE_DOCS_SOURCE_NAME is set (by parallel workers), creates
        separate log files per source for easier debugging of parallel runs.
        """
        try:
            # Determine log directory based on category
            if self.log_category and self.log_category in ("scrape", "index", "search", "diagnostics"):
                log_dir = _LOGS_DIR / self.log_category
            else:
                log_dir = _LOGS_DIR / "diagnostics"

            # Ensure directory exists
            log_dir.mkdir(parents=True, exist_ok=True)

            # Create log filename with date and optional source name
            # Source name enables per-source log files for parallel worker debugging
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            source_name = os.environ.get(SOURCE_NAME_ENV_VAR)
            if source_name:
                # Sanitize source name for filename (replace spaces, slashes with underscores)
                safe_source = source_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
                log_filename = f"{self.script_name}_{safe_source}_{date_str}.log"
            else:
                log_filename = f"{self.script_name}_{date_str}.log"
            log_path = log_dir / log_filename

            # Configure rotation from config file
            max_size_mb = _get_runtime_nested("logging", "rotation", "max_size_mb", 10)
            backup_count = _get_runtime_nested("logging", "rotation", "backup_count", 5)
            max_bytes = int(max_size_mb) * 1024 * 1024  # MB to bytes

            # Create lazy rotating file handler (defers file creation until first write)
            # This prevents empty 0-byte log files from being created
            file_handler = LazyRotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)

            # Use JSON or text format
            # Include source, run_id, and process ID for correlating logs from parallel executions
            if self._json_format:
                file_handler.setFormatter(JSONFormatter())
            else:
                # Use SourceAwareFormatter for consistent source + run_id in file logs
                file_handler.setFormatter(SourceAwareFormatter(
                    '[%(asctime)s] [%(levelname)s] [%(source)s] [%(run_id)s] [%(process)d] [%(funcName)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                ))

            self.logger.addHandler(file_handler)
            self.logger.debug(f"File logging enabled (lazy): {log_path}")
        except Exception as e:
            # Don't fail if file logging can't be set up
            self.logger.warning(f"Could not enable file logging: {e}")
    
    # Delegate standard logger attributes for test compatibility
    @property
    def name(self):
        """Delegate to wrapped logger name."""
        return self.logger.name
    
    @property
    def level(self):
        """Delegate to wrapped logger level."""
        return self.logger.level
    
    @property
    def handlers(self):
        """Delegate to wrapped logger handlers."""
        return self.logger.handlers
    
    @property
    def propagate(self):
        """Delegate to wrapped logger propagate setting."""
        return self.logger.propagate
    
    # Delegate standard logger methods for test compatibility
    def addHandler(self, handler):
        """Delegate to wrapped logger addHandler."""
        return self.logger.addHandler(handler)
    
    def removeHandler(self, handler):
        """Delegate to wrapped logger removeHandler."""
        return self.logger.removeHandler(handler)
    
    def setLevel(self, level):
        """Delegate to wrapped logger setLevel."""
        return self.logger.setLevel(level)
    
    def start(self, context: dict[str, Any] | None = None, include_env_info: bool = False):
        """Log script start with optional context"""
        self.start_time = time.time()
        start_dt = datetime.now()

        try:
            self.logger.info("=" * 60)
            self.logger.info(f"🚀 Starting {self.script_name}")
            self.logger.info(f"   Start time: {start_dt.isoformat()}")
            self.logger.info(f"   Run ID: {self.run_id}")
            
            if context:
                self.logger.info("   Context:")
                for key, value in context.items():
                    self.logger.info(f"      {key}: {value}")
            
            if include_env_info:
                try:
                    import os
                    
                    python_version = sys.version.split()[0]
                    python_executable = sys.executable
                    is_venv = bool(os.environ.get('VIRTUAL_ENV') or sys.prefix != sys.base_prefix)
                    venv_path = os.environ.get('VIRTUAL_ENV') or (sys.prefix if is_venv else None)
                    
                    self.logger.info(f"   Python: {python_version} at {python_executable}")
                    if is_venv and venv_path:
                        self.logger.info(f"   Virtual Environment: {venv_path}")
                except Exception:
                    # Silently fail if environment info can't be determined
                    pass
            
            self.logger.info("=" * 60)
        except (BrokenPipeError, OSError):
            # Output stream closed (e.g., piped to head); ignore during tests/CI.
            pass
        
        self.performance_metrics['start_time'] = start_dt.isoformat()
        self.performance_metrics['start_timestamp'] = self.start_time
        self.performance_metrics['run_id'] = self.run_id
    
    def end(self, exit_code: int = 0, summary: dict[str, Any | None] = None):
        """Log script end with performance metrics"""
        self.end_time = time.time()
        end_dt = datetime.now()

        if self.start_time:
            duration = self.end_time - self.start_time
            duration_str = format_duration(duration)
        else:
            duration = 0
            duration_str = "unknown"

        try:
            self.logger.info("=" * 60)
            self.logger.info(f"✅ Completed {self.script_name}")
            self.logger.info(f"   End time: {end_dt.isoformat()}")
            self.logger.info(f"   Duration: {duration_str}")
            self.logger.info(f"   Exit code: {exit_code}")

            if summary:
                self.logger.info("   Summary:")
                for key, value in summary.items():
                    self.logger.info(f"      {key}: {value}")

            # Log performance metrics
            if self.performance_metrics:
                self.logger.info("   Performance Metrics:")
                for key, value in self.performance_metrics.items():
                    if key not in ['start_time', 'start_timestamp']:
                        self.logger.info(f"      {key}: {value}")

            self.logger.info("=" * 60)
        except (BrokenPipeError, OSError):
            # Output stream closed (e.g., piped to head); ignore during tests/CI.
            pass

        self.performance_metrics['end_time'] = end_dt.isoformat()
        self.performance_metrics['end_timestamp'] = self.end_time
        self.performance_metrics['duration_seconds'] = duration
        self.performance_metrics['exit_code'] = exit_code

        # Write diagnostics file if enabled in config
        # FIX 2025-11-26: _write_diagnostics was set but never used
        if self._write_diagnostics:
            self.write_diagnostics_file()

    # Basic logging API passthrough so callers (and tests) can use this
    # instance like a standard logging.Logger where needed.

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self.logger.critical(msg, *args, **kwargs)
    
    def track_metric(self, name: str, value: Any):
        """Track a custom performance metric"""
        self.performance_metrics[name] = value
        self.logger.debug(f"Metric: {name} = {value}")
    
    def log_operation(self, operation: str, **kwargs):
        """Log a specific operation with context"""
        context = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"🔧 {operation}" + (f" ({context})" if context else ""))
    
    def log_success(self, message: str, **kwargs):
        """Log a success message"""
        context = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"✅ {message}" + (f" ({context})" if context else ""))
    
    def log_warning(self, message: str, **kwargs):
        """Log a warning message"""
        context = ', '.join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.warning(f"⚠️  {message}" + (f" ({context})" if context else ""))
    
    def log_error(self, message: str, error: Exception | None = None,
                  category: str | None = None, **kwargs):
        """Log an error message with classification.

        Args:
            message: Error message to log
            error: Optional exception object
            category: Optional error category (auto-classified if not provided)
            **kwargs: Additional context to include in log
        """
        try:
            # Auto-classify error if category not provided
            error_category = category or classify_error(error)

            # Build context with error category
            context_parts = [f"category={error_category}"]
            context_parts.extend(f"{k}={v}" for k, v in kwargs.items())
            context = ', '.join(context_parts)

            error_str = f": {str(error)}" if error else ""
            self.logger.error(f"❌ {message}{error_str} ({context})")

            # Track error by category for metrics
            self.track_metric(f"errors_{error_category}", 1)
            self.track_metric("errors_total", 1)

            if error:
                self.logger.debug(f"Exception type: {type(error).__name__}")
        except (BrokenPipeError, OSError):
            # Output stream closed (e.g., piped to head); ignore to avoid
            # interfering with test runners that rely on sys.stderr/stdout.
            pass
    
    @contextmanager
    def time_operation(self, operation_name: str):
        """Measure duration of an operation using a context manager"""
        start = time.time()
        self.logger.info(f"⏱️  Starting: {operation_name}")
        try:
            yield
            duration = time.time() - start
            self.track_metric(f"{operation_name}_duration", duration)
            self.logger.info(f"✅ Completed: {operation_name} ({format_duration(duration)})")
        except Exception:
            duration = time.time() - start
            self.log_operation(operation_name, status='failed', duration=duration)
            raise

    @contextmanager
    def time_http_request(self, url: str, method: str = "GET"):
        """Track HTTP request timing with detailed metrics.

        Args:
            url: The URL being requested
            method: HTTP method (GET, HEAD, POST, etc.)

        Yields:
            dict: A mutable dict to store additional context (status_code, size, etc.)

        Example:
            with logger.time_http_request(url, "GET") as ctx:
                response = requests.get(url)
                ctx["status_code"] = response.status_code
                ctx["size"] = len(response.content)
        """
        start = time.time()
        context: dict[str, Any] = {"url": url, "method": method}
        try:
            yield context
            duration = time.time() - start
            context["duration_ms"] = round(duration * 1000, 2)
            context["success"] = True
            context["timestamp"] = datetime.now(timezone.utc).isoformat()

            self.http_timings.append(context)
            self.logger.debug(
                f"HTTP {method} {url[:80]}... "
                f"({context.get('status_code', '?')}) "
                f"{context['duration_ms']}ms"
            )
        except Exception as e:
            duration = time.time() - start
            context["duration_ms"] = round(duration * 1000, 2)
            context["success"] = False
            context["error"] = str(e)
            context["timestamp"] = datetime.now(timezone.utc).isoformat()

            self.http_timings.append(context)
            self.logger.debug(
                f"HTTP {method} {url[:80]}... FAILED ({duration*1000:.0f}ms): {e}"
            )
            raise

    def log_http_summary(self, show_percentiles: bool = True,
                         show_per_domain: bool = False) -> dict[str, Any]:
        """Log and return summary of HTTP request timings.

        Args:
            show_percentiles: Include p50/p90/p99 latency percentiles
            show_per_domain: Include per-domain breakdown

        Returns:
            Summary dictionary with timing statistics
        """
        if not self.http_timings:
            return {"total_requests": 0}

        total = len(self.http_timings)
        successful = sum(1 for t in self.http_timings if t.get("success"))
        failed = total - successful
        durations = [t["duration_ms"] for t in self.http_timings]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        total_duration = sum(durations)

        summary: dict[str, Any] = {
            "total_requests": total,
            "successful": successful,
            "failed": failed,
            "avg_duration_ms": round(avg_duration, 2),
            "min_duration_ms": round(min_duration, 2),
            "max_duration_ms": round(max_duration, 2),
            "total_duration_ms": round(total_duration, 2),
        }

        # Calculate percentiles
        if show_percentiles and durations:
            sorted_durations = sorted(durations)
            n = len(sorted_durations)
            p50 = sorted_durations[int(n * PERCENTILE_P50)] if n > 0 else 0
            p90 = sorted_durations[int(n * PERCENTILE_P90)] if n > 1 else sorted_durations[-1]
            p99 = sorted_durations[min(int(n * PERCENTILE_P99), n - 1)] if n > 0 else sorted_durations[-1]
            summary["p50_ms"] = round(p50, 2)
            summary["p90_ms"] = round(p90, 2)
            summary["p99_ms"] = round(p99, 2)

        # Per-domain breakdown
        if show_per_domain:
            from urllib.parse import urlparse
            domain_stats: dict[str, dict[str, Any]] = {}
            for timing in self.http_timings:
                url = timing.get("url", "")
                try:
                    domain = urlparse(url).netloc or "unknown"
                except Exception:
                    domain = "unknown"

                if domain not in domain_stats:
                    domain_stats[domain] = {"count": 0, "durations": [], "success": 0, "failed": 0}
                domain_stats[domain]["count"] += 1
                domain_stats[domain]["durations"].append(timing.get("duration_ms", 0))
                if timing.get("success"):
                    domain_stats[domain]["success"] += 1
                else:
                    domain_stats[domain]["failed"] += 1

            # Calculate domain averages
            for domain, stats in domain_stats.items():
                if stats["durations"]:
                    stats["avg_ms"] = round(sum(stats["durations"]) / len(stats["durations"]), 2)
                del stats["durations"]  # Remove raw data from summary

            summary["by_domain"] = domain_stats

        # Status code distribution
        status_codes: dict[int, int] = {}
        for timing in self.http_timings:
            code = timing.get("status_code", 0)
            if code:
                status_codes[code] = status_codes.get(code, 0) + 1
        if status_codes:
            summary["status_codes"] = status_codes

        # Log summary
        self.logger.info(f"📊 HTTP Summary: {total} requests, {successful} OK, {failed} failed")
        self.logger.info(f"   Timing: avg={avg_duration:.0f}ms, min={min_duration:.0f}ms, max={max_duration:.0f}ms, total={total_duration:.0f}ms")
        if show_percentiles and "p50_ms" in summary:
            self.logger.info(f"   Percentiles: p50={summary['p50_ms']:.0f}ms, p90={summary['p90_ms']:.0f}ms, p99={summary['p99_ms']:.0f}ms")
        if status_codes:
            codes_str = ", ".join(f"{k}:{v}" for k, v in sorted(status_codes.items()))
            self.logger.info(f"   Status codes: {codes_str}")

        self.track_metric("http_requests_total", total)
        self.track_metric("http_requests_successful", successful)
        self.track_metric("http_requests_failed", failed)
        self.track_metric("http_avg_duration_ms", summary["avg_duration_ms"])

        return summary

    def get_performance_report(self) -> dict[str, Any]:
        """Get complete performance report including HTTP timings."""
        report = {
            'script_name': self.script_name,
            'performance_metrics': self.performance_metrics.copy(),
            'start_time': self.performance_metrics.get('start_time'),
            'end_time': self.performance_metrics.get('end_time'),
            'duration_seconds': self.performance_metrics.get('duration_seconds', 0),
        }

        # Add HTTP summary if there are any timings
        if self.http_timings:
            report['http_summary'] = {
                'total_requests': len(self.http_timings),
                'successful': sum(1 for t in self.http_timings if t.get('success')),
                'failed': sum(1 for t in self.http_timings if not t.get('success')),
                'timings': self.http_timings,
            }

        return report

    def write_diagnostics_file(self, filename: str | None = None) -> Path | None:
        """Write detailed diagnostics to a JSON file for later analysis.

        Args:
            filename: Optional custom filename (default: {script}_{timestamp}_diagnostics.json)

        Returns:
            Path to the written file, or None if writing failed.
        """
        try:
            diagnostics_dir = _LOGS_DIR / "diagnostics"
            diagnostics_dir.mkdir(parents=True, exist_ok=True)

            if filename is None:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                filename = f"{self.script_name}_{timestamp}_diagnostics.json"

            filepath = diagnostics_dir / filename

            report = self.get_performance_report()
            report["generated_at"] = datetime.now(timezone.utc).isoformat()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"📄 Diagnostics written to: {filepath}")
            return filepath
        except Exception as e:
            self.logger.warning(f"Could not write diagnostics file: {e}")
            return None

def setup_script_logging(
    script_name: str,
    log_level: int = logging.INFO,
    log_category: str | None = None,
    enable_file_logging: bool | None = None,
    run_id: str | None = None,
) -> ScriptLogger:
    """
    Setup logging for a script.

    Args:
        script_name: Name of the script (usually __file__)
        log_level: Logging level (default: INFO)
        log_category: Log category for file output (scrape, index, search, diagnostics)
        enable_file_logging: Override env var to enable/disable file logging
        run_id: Session correlation ID (auto-generated or inherited from env)

    Returns:
        ScriptLogger instance
    """
    return ScriptLogger(
        script_name,
        log_level,
        log_category=log_category,
        enable_file_logging=enable_file_logging,
        run_id=run_id,
    )

# Cache for ScriptLogger instances (for singleton behavior per script name)
_script_logger_cache: dict[str, ScriptLogger] = {}
_script_logger_cache_lock = threading.Lock()

def get_or_setup_logger(
    script_name: str,
    log_level: int = logging.INFO,
    level: int = None,
    log_category: str | None = None,
    enable_file_logging: bool | None = None,
    run_id: str | None = None,
) -> ScriptLogger:
    """Helper used by scripts to obtain a ScriptLogger with fallback.

    Most scripts should call this instead of re-implementing try/except
    boilerplate around setup_script_logging.

    Args:
        script_name: Name of the script (usually __file__)
        log_level: Logging level (default: INFO) - kept for backward compatibility
        level: Logging level (alias for log_level) - for test compatibility
        log_category: Log category for file output (scrape, index, search, diagnostics)
        enable_file_logging: Override env var to enable/disable file logging
        run_id: Session correlation ID (auto-generated or inherited from env)

    Returns:
        Cached ScriptLogger instance for the script name (singleton behavior)
    """
    # Support both log_level and level parameters
    if level is not None:
        log_level = level

    # Use cache key combining script name, level, and category for singleton behavior
    cache_key = f"{Path(script_name).stem if script_name else 'unknown'}_{log_level}_{log_category or 'default'}"

    # Fast path: check without lock first
    if cache_key in _script_logger_cache:
        return _script_logger_cache[cache_key]

    # Slow path: acquire lock for thread-safe creation
    with _script_logger_cache_lock:
        # Double-check after acquiring lock (another thread may have created it)
        if cache_key in _script_logger_cache:
            return _script_logger_cache[cache_key]

        try:
            logger = setup_script_logging(
                script_name,
                log_level,
                log_category=log_category,
                enable_file_logging=enable_file_logging,
                run_id=run_id,
            )
            _script_logger_cache[cache_key] = logger
            return logger
        except Exception:
            # Fallback: basic stderr/stdout logger with minimal configuration.
            logger = logging.getLogger(Path(script_name).stem or __name__)
            logger.setLevel(log_level)
            if not logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
                logger.addHandler(handler)
            # Wrap the basic logger in ScriptLogger for API consistency.
            wrapper = ScriptLogger(script_name, log_level, run_id=run_id)
            wrapper.logger = logger
            _script_logger_cache[cache_key] = wrapper  # Cache the fallback too
            return wrapper

def log_function_call(func: Callable) -> Callable:
    """Decorator to log function calls with timing"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        
        start = time.time()
        logger.debug(f"Calling: {func_name}(args={len(args)}, kwargs={list(kwargs.keys())})")
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            logger.debug(f"Completed: {func_name} ({duration:.3f}s)")
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(f"Failed: {func_name} after {duration:.3f}s: {e}")
            raise
    
    return wrapper

# Global logger instance (can be imported by scripts)
_global_logger: ScriptLogger | None = None

def get_logger(script_name: str | None = None) -> ScriptLogger:
    """Get or create global logger instance"""
    global _global_logger
    if _global_logger is None:
        if script_name:
            _global_logger = ScriptLogger(script_name)
        else:
            # Default logger
            _global_logger = ScriptLogger('docs-management')
    return _global_logger

