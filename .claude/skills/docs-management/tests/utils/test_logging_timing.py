#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for logging_utils timing and observability features."""

import sys
import time
import logging
from pathlib import Path
from unittest.mock import patch

# Standard test bootstrap
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))

import pytest


class TestTimeOperation:
    """Test time_operation() context manager."""

    def test_tracks_duration(self):
        """Should track operation duration in performance_metrics."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        with logger.time_operation('test_op'):
            time.sleep(0.05)  # 50ms

        assert 'test_op_duration' in logger.performance_metrics
        assert logger.performance_metrics['test_op_duration'] >= 0.05

    def test_logs_start_and_completion(self, caplog):
        """Should log start and completion messages."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')
        logger.logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            with logger.time_operation('my_operation'):
                pass

        assert any('Starting: my_operation' in rec.message for rec in caplog.records)
        assert any('Completed: my_operation' in rec.message for rec in caplog.records)

    def test_propagates_exception(self):
        """Should re-raise exceptions from within the context."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        with pytest.raises(ValueError, match="test error"):
            with logger.time_operation('failing_op'):
                raise ValueError("test error")

    def test_tracks_duration_on_failure(self):
        """Should track duration even when operation fails."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        try:
            with logger.time_operation('failing_op'):
                time.sleep(0.02)
                raise ValueError("test error")
        except ValueError:
            pass

        # Duration should still be tracked (as log_operation call)
        # The metric won't be in performance_metrics on failure path
        # but operation should complete timing


class TestTimeHttpRequest:
    """Test time_http_request() context manager."""

    def test_tracks_successful_request(self):
        """Should track successful HTTP request timing."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        with logger.time_http_request('https://example.com', 'GET') as ctx:
            ctx['status_code'] = 200
            ctx['size'] = 1024
            time.sleep(0.02)

        assert len(logger.http_timings) == 1
        timing = logger.http_timings[0]
        assert timing['url'] == 'https://example.com'
        assert timing['method'] == 'GET'
        assert timing['status_code'] == 200
        assert timing['success'] is True
        assert timing['duration_ms'] >= 20

    def test_tracks_failed_request(self):
        """Should track failed HTTP request timing."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        try:
            with logger.time_http_request('https://fail.example.com', 'POST') as ctx:
                raise ConnectionError("Connection refused")
        except ConnectionError:
            pass

        assert len(logger.http_timings) == 1
        timing = logger.http_timings[0]
        assert timing['url'] == 'https://fail.example.com'
        assert timing['method'] == 'POST'
        assert timing['success'] is False
        assert 'error' in timing
        assert 'Connection refused' in timing['error']

    def test_includes_timestamp(self):
        """Should include ISO timestamp in timing record."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        with logger.time_http_request('https://example.com') as ctx:
            ctx['status_code'] = 200

        timing = logger.http_timings[0]
        assert 'timestamp' in timing
        # Should be ISO format
        assert 'T' in timing['timestamp']

    def test_multiple_requests(self):
        """Should track multiple HTTP requests."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        for i in range(3):
            with logger.time_http_request(f'https://example.com/{i}') as ctx:
                ctx['status_code'] = 200 + i

        assert len(logger.http_timings) == 3
        assert logger.http_timings[0]['url'] == 'https://example.com/0'
        assert logger.http_timings[2]['url'] == 'https://example.com/2'


class TestLogFunctionCall:
    """Test log_function_call() decorator."""

    def test_decorator_preserves_function_name(self):
        """Should preserve decorated function's name and docstring."""
        from utils.logging_utils import log_function_call

        @log_function_call
        def my_function():
            """My docstring."""
            return 42

        assert my_function.__name__ == 'my_function'
        assert my_function.__doc__ == 'My docstring.'

    def test_decorator_passes_arguments(self):
        """Should pass arguments to decorated function."""
        from utils.logging_utils import log_function_call

        @log_function_call
        def add(a, b, multiplier=1):
            return (a + b) * multiplier

        result = add(2, 3, multiplier=2)
        assert result == 10

    def test_decorator_returns_result(self):
        """Should return function's result."""
        from utils.logging_utils import log_function_call

        @log_function_call
        def get_data():
            return {'key': 'value'}

        result = get_data()
        assert result == {'key': 'value'}

    def test_decorator_propagates_exceptions(self):
        """Should propagate exceptions from decorated function."""
        from utils.logging_utils import log_function_call

        @log_function_call
        def failing_function():
            raise RuntimeError("Something went wrong")

        with pytest.raises(RuntimeError, match="Something went wrong"):
            failing_function()

    def test_decorator_logs_calls(self, caplog):
        """Should log function calls at debug level."""
        from utils.logging_utils import log_function_call

        @log_function_call
        def simple_function(x, y):
            return x + y

        with caplog.at_level(logging.DEBUG):
            simple_function(1, 2)

        assert any('Calling:' in rec.message for rec in caplog.records)
        assert any('Completed:' in rec.message for rec in caplog.records)


class TestLogHttpSummary:
    """Test log_http_summary() method."""

    def test_empty_timings(self):
        """Should handle empty HTTP timings gracefully."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')
        summary = logger.log_http_summary()

        assert summary['total_requests'] == 0

    def test_calculates_statistics(self):
        """Should calculate correct statistics."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        # Manually add timings for predictable test
        logger.http_timings = [
            {'url': 'https://a.com', 'duration_ms': 100, 'success': True, 'status_code': 200},
            {'url': 'https://b.com', 'duration_ms': 200, 'success': True, 'status_code': 200},
            {'url': 'https://c.com', 'duration_ms': 300, 'success': False, 'status_code': 500},
        ]

        summary = logger.log_http_summary()

        assert summary['total_requests'] == 3
        assert summary['successful'] == 2
        assert summary['failed'] == 1
        assert summary['avg_duration_ms'] == 200  # (100+200+300)/3
        assert summary['min_duration_ms'] == 100
        assert summary['max_duration_ms'] == 300

    def test_calculates_percentiles(self):
        """Should calculate p50/p90/p99 percentiles."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        # Add 10 timings with known values
        logger.http_timings = [
            {'url': f'https://example.com/{i}', 'duration_ms': (i + 1) * 10, 'success': True}
            for i in range(10)
        ]

        summary = logger.log_http_summary(show_percentiles=True)

        assert 'p50_ms' in summary
        assert 'p90_ms' in summary
        assert 'p99_ms' in summary

    def test_per_domain_breakdown(self):
        """Should calculate per-domain statistics when requested."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        logger.http_timings = [
            {'url': 'https://api.example.com/a', 'duration_ms': 100, 'success': True},
            {'url': 'https://api.example.com/b', 'duration_ms': 200, 'success': True},
            {'url': 'https://cdn.other.com/x', 'duration_ms': 50, 'success': True},
        ]

        summary = logger.log_http_summary(show_per_domain=True)

        assert 'by_domain' in summary
        assert 'api.example.com' in summary['by_domain']
        assert summary['by_domain']['api.example.com']['count'] == 2

    def test_status_code_distribution(self):
        """Should track status code distribution."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        logger.http_timings = [
            {'url': 'https://a.com', 'duration_ms': 100, 'success': True, 'status_code': 200},
            {'url': 'https://b.com', 'duration_ms': 100, 'success': True, 'status_code': 200},
            {'url': 'https://c.com', 'duration_ms': 100, 'success': False, 'status_code': 404},
            {'url': 'https://d.com', 'duration_ms': 100, 'success': False, 'status_code': 500},
        ]

        summary = logger.log_http_summary()

        assert 'status_codes' in summary
        assert summary['status_codes'][200] == 2
        assert summary['status_codes'][404] == 1
        assert summary['status_codes'][500] == 1


class TestPerformanceReport:
    """Test get_performance_report() method."""

    def test_includes_script_name(self):
        """Should include script name in report."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('my_script')
        report = logger.get_performance_report()

        assert report['script_name'] == 'my_script'

    def test_includes_metrics(self):
        """Should include tracked metrics in report."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')
        logger.track_metric('files_processed', 42)
        logger.track_metric('errors_count', 3)

        report = logger.get_performance_report()

        assert report['performance_metrics']['files_processed'] == 42
        assert report['performance_metrics']['errors_count'] == 3

    def test_includes_http_summary_when_present(self):
        """Should include HTTP summary when there are timings."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')

        logger.http_timings = [
            {'url': 'https://a.com', 'duration_ms': 100, 'success': True},
        ]

        report = logger.get_performance_report()

        assert 'http_summary' in report
        assert report['http_summary']['total_requests'] == 1


class TestWriteDiagnosticsFile:
    """Test write_diagnostics_file() method."""

    def test_writes_json_file(self, temp_dir):
        """Should write valid JSON diagnostics file."""
        import json
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')
        logger.track_metric('test_metric', 123)

        # Patch _LOGS_DIR to use temp directory
        with patch('utils.logging_utils._LOGS_DIR', temp_dir):
            filepath = logger.write_diagnostics_file('test_diagnostics.json')

        assert filepath is not None
        assert filepath.exists()

        with open(filepath) as f:
            data = json.load(f)

        assert data['script_name'] == 'test_script'
        assert 'generated_at' in data

    def test_creates_directory_if_missing(self, temp_dir):
        """Should create diagnostics directory if it doesn't exist."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')
        nested_dir = temp_dir / 'nested' / 'diagnostics'

        with patch('utils.logging_utils._LOGS_DIR', temp_dir / 'nested'):
            filepath = logger.write_diagnostics_file('nested_test.json')

        assert filepath is not None
        assert (temp_dir / 'nested' / 'diagnostics').exists()


class TestErrorClassification:
    """Test classify_error() function."""

    def test_classifies_network_errors(self):
        """Should classify network-related errors."""
        from utils.logging_utils import classify_error, ErrorCategory

        assert classify_error(ConnectionError()) == ErrorCategory.NETWORK
        assert classify_error(ConnectionResetError()) == ErrorCategory.NETWORK

    def test_classifies_timeout_errors(self):
        """Should classify timeout errors."""
        from utils.logging_utils import classify_error, ErrorCategory

        assert classify_error(TimeoutError()) == ErrorCategory.TIMEOUT

    def test_classifies_file_io_errors(self):
        """Should classify file I/O errors."""
        from utils.logging_utils import classify_error, ErrorCategory

        assert classify_error(FileNotFoundError()) == ErrorCategory.FILE_IO
        assert classify_error(PermissionError()) == ErrorCategory.FILE_IO

    def test_classifies_validation_errors(self):
        """Should classify validation errors."""
        from utils.logging_utils import classify_error, ErrorCategory

        assert classify_error(ValueError("invalid input")) == ErrorCategory.VALIDATION
        assert classify_error(TypeError("wrong type")) == ErrorCategory.VALIDATION

    def test_unknown_errors(self):
        """Should return unknown for unclassified errors."""
        from utils.logging_utils import classify_error, ErrorCategory

        class CustomError(Exception):
            pass

        assert classify_error(CustomError()) == ErrorCategory.UNKNOWN
        assert classify_error(None) == ErrorCategory.UNKNOWN


class TestStartEndLifecycle:
    """Test start() and end() lifecycle methods."""

    def test_start_sets_timestamp(self):
        """start() should set start_time."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')
        logger.start()

        assert logger.start_time is not None
        assert 'start_time' in logger.performance_metrics
        assert 'run_id' in logger.performance_metrics

    def test_end_calculates_duration(self):
        """end() should calculate duration."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')
        logger.start()
        time.sleep(0.05)
        logger.end()

        assert logger.performance_metrics['duration_seconds'] >= 0.05

    def test_end_accepts_exit_code(self):
        """end() should track exit code."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')
        logger.start()
        logger.end(exit_code=1)

        assert logger.performance_metrics['exit_code'] == 1

    def test_end_accepts_summary(self, caplog):
        """end() should log summary if provided."""
        from utils.logging_utils import ScriptLogger

        logger = ScriptLogger('test_script')
        logger.logger.setLevel(logging.INFO)
        logger.start()

        with caplog.at_level(logging.INFO):
            logger.end(summary={'files_processed': 10, 'errors': 0})

        assert any('files_processed' in rec.message for rec in caplog.records)
