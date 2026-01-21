"""
Tests for http_utils module.
"""
from unittest.mock import patch, MagicMock


import pytest
import responses
from requests.exceptions import Timeout, HTTPError, ConnectionError
from scripts.utils.http_utils import (
    fetch_with_retry,
    RETRY_STATUS_CODES,
)


class TestFetchWithRetry:
    """Test suite for fetch_with_retry function."""

    @responses.activate
    def test_successful_fetch(self):
        """Test successful HTTP fetch on first attempt."""
        url = "https://example.com/test"
        expected_content = "<html>Test content</html>"

        responses.add(
            responses.GET,
            url,
            body=expected_content,
            status=200,
            content_type="text/html"
        )

        response = fetch_with_retry(url)

        assert response.status_code == 200
        assert response.text == expected_content
        assert len(responses.calls) == 1

    @responses.activate
    def test_retry_on_500_error(self):
        """Test retry behavior on 500 Internal Server Error."""
        url = "https://example.com/test"

        # First two attempts fail with 500, third succeeds
        responses.add(responses.GET, url, status=500)
        responses.add(responses.GET, url, status=500)
        responses.add(responses.GET, url, body="Success", status=200)

        response = fetch_with_retry(url, max_retries=3)

        assert response.status_code == 200
        assert response.text == "Success"
        assert len(responses.calls) == 3

    @responses.activate
    def test_retry_on_503_error(self):
        """Test retry behavior on 503 Service Unavailable."""
        url = "https://example.com/test"

        # First attempt fails with 503, second succeeds
        responses.add(responses.GET, url, status=503)
        responses.add(responses.GET, url, body="Success", status=200)

        response = fetch_with_retry(url, max_retries=2)

        assert response.status_code == 200
        assert len(responses.calls) == 2

    @responses.activate
    def test_no_retry_on_404(self):
        """Test that 404 errors are not retried."""
        url = "https://example.com/not-found"

        responses.add(responses.GET, url, status=404)

        with pytest.raises(HTTPError):
            fetch_with_retry(url, max_retries=3)

        # Should only make one attempt
        assert len(responses.calls) == 1

    @responses.activate
    def test_no_retry_on_403(self):
        """Test that 403 Forbidden errors are not retried."""
        url = "https://example.com/forbidden"

        responses.add(responses.GET, url, status=403)

        with pytest.raises(HTTPError):
            fetch_with_retry(url, max_retries=3)

        assert len(responses.calls) == 1

    @responses.activate
    def test_rate_limit_with_retry_after(self):
        """Test 429 rate limit handling with Retry-After header."""
        url = "https://example.com/test"

        # First attempt gets rate limited with Retry-After
        responses.add(
            responses.GET,
            url,
            status=429,
            headers={"Retry-After": "2"}
        )
        responses.add(responses.GET, url, body="Success", status=200)

        with patch('time.sleep') as mock_sleep:
            response = fetch_with_retry(url, max_retries=2)

            assert response.status_code == 200
            # Should sleep for at least the Retry-After duration
            mock_sleep.assert_called()
            assert mock_sleep.call_args[0][0] >= 2

    @responses.activate
    def test_exponential_backoff(self):
        """Test exponential backoff timing between retries."""
        url = "https://example.com/test"

        # All attempts fail to test backoff
        for _ in range(4):
            responses.add(responses.GET, url, status=500)

        with patch('time.sleep') as mock_sleep:
            with pytest.raises(HTTPError):
                fetch_with_retry(url, max_retries=3, initial_delay=1.0)

            # Should have 3 sleep calls (after each failed attempt except last)
            assert mock_sleep.call_count == 3

            # Verify exponential backoff: 1s, 2s, 4s
            calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert calls[0] == pytest.approx(1.0, rel=0.1)
            assert calls[1] == pytest.approx(2.0, rel=0.1)
            assert calls[2] == pytest.approx(4.0, rel=0.1)

    @responses.activate
    def test_max_retries_exceeded(self):
        """Test that HTTPError is raised after max retries exceeded."""
        url = "https://example.com/test"

        # All attempts fail
        for _ in range(5):
            responses.add(responses.GET, url, status=500)

        with pytest.raises(HTTPError) as exc_info:
            fetch_with_retry(url, max_retries=3)

        assert "Max retries exceeded" in str(exc_info.value)
        assert len(responses.calls) == 4  # initial + 3 retries

    @responses.activate
    def test_timeout_retry(self):
        """Test retry on timeout errors."""
        url = "https://example.com/test"

        # Simulate timeout by using responses callback
        def timeout_callback(request):
            raise Timeout("Request timed out")

        responses.add_callback(
            responses.GET,
            url,
            callback=timeout_callback
        )
        responses.add(responses.GET, url, body="Success", status=200)

        response = fetch_with_retry(url, max_retries=2, timeout=1.0)

        assert response.status_code == 200
        assert len(responses.calls) == 2

    @responses.activate
    def test_connection_error_retry(self):
        """Test retry on connection errors."""
        url = "https://example.com/test"

        def connection_error_callback(request):
            raise ConnectionError("Connection failed")

        responses.add_callback(
            responses.GET,
            url,
            callback=connection_error_callback
        )
        responses.add(responses.GET, url, body="Success", status=200)

        response = fetch_with_retry(url, max_retries=2)

        assert response.status_code == 200

    @responses.activate
    def test_custom_timeout(self):
        """Test custom timeout parameter."""
        url = "https://example.com/test"

        responses.add(responses.GET, url, body="Success", status=200)

        with patch('requests.Session.get') as mock_get:
            mock_get.return_value = MagicMock(status_code=200, text="Success")

            fetch_with_retry(url, timeout=5.0)

            # Verify timeout was passed
            assert mock_get.call_args[1]['timeout'] == 5.0

    @responses.activate
    def test_custom_headers(self):
        """Test custom headers are sent with request."""
        url = "https://example.com/test"
        custom_headers = {
            "User-Agent": "Custom-Agent/1.0",
            "Accept": "application/json"
        }

        responses.add(responses.GET, url, body="Success", status=200)

        response = fetch_with_retry(url, headers=custom_headers)

        # Verify headers were sent
        request_headers = responses.calls[0].request.headers
        assert request_headers["User-Agent"] == "Custom-Agent/1.0"
        assert request_headers["Accept"] == "application/json"

    @responses.activate
    def test_default_retry_status_codes(self):
        """Test that default retry status codes are respected."""
        url = "https://example.com/test"

        # Test each retryable status code
        for status_code in RETRY_STATUS_CODES:
            responses.reset()
            responses.add(responses.GET, url, status=status_code)
            responses.add(responses.GET, url, body="Success", status=200)

            response = fetch_with_retry(url, max_retries=2)
            assert response.status_code == 200
            assert len(responses.calls) == 2

    @responses.activate
    def test_jitter_in_backoff(self):
        """Test that jitter is applied to backoff delays."""
        url = "https://example.com/test"

        for _ in range(3):
            responses.add(responses.GET, url, status=500)

        with patch('time.sleep') as mock_sleep:
            with pytest.raises(HTTPError):
                fetch_with_retry(url, max_retries=2, initial_delay=1.0)

            # Verify delays have some variation (jitter)
            calls = [call[0][0] for call in mock_sleep.call_args_list]

            # First delay should be around 1.0 ± jitter
            assert 0.9 <= calls[0] <= 1.1

            # Second delay should be around 2.0 ± jitter
            assert 1.8 <= calls[1] <= 2.2

    @responses.activate
    def test_verify_ssl_parameter(self):
        """Test that SSL verification can be disabled."""
        url = "https://example.com/test"

        responses.add(responses.GET, url, body="Success", status=200)

        with patch('requests.Session.get') as mock_get:
            mock_get.return_value = MagicMock(status_code=200, text="Success")

            fetch_with_retry(url, verify=False)

            # Verify SSL verification was disabled
            assert mock_get.call_args[1]['verify'] is False


class TestFileIORetry:
    """Test suite for file I/O retry functions."""

    def test_read_file_with_retry_success(self, tmp_path):
        """Test read_file_with_retry with successful read on first attempt."""
        from scripts.utils.http_utils import read_file_with_retry
        
        test_file = tmp_path / "test.md"
        test_content = "# Test Content\n\nThis is a test file."
        test_file.write_text(test_content, encoding='utf-8')
        
        content = read_file_with_retry(test_file)
        
        assert content == test_content

    def test_read_file_with_retry_file_not_found(self, tmp_path):
        """Test read_file_with_retry raises FileNotFoundError for missing files."""
        from scripts.utils.http_utils import read_file_with_retry
        
        missing_file = tmp_path / "missing.md"
        
        with pytest.raises(FileNotFoundError):
            read_file_with_retry(missing_file)

    def test_read_file_with_retry_permission_error(self, tmp_path):
        """Test read_file_with_retry retries on permission errors."""
        from scripts.utils.http_utils import read_file_with_retry
        from pathlib import Path
        
        test_file = tmp_path / "test.md"
        test_content = "# Test"
        test_file.write_text(test_content, encoding='utf-8')
        
        # Mock read_text to raise PermissionError first, then succeed
        original_read_text = Path.read_text
        call_count = [0]
        
        def mock_read_text(self, encoding=None, errors=None):
            call_count[0] += 1
            if call_count[0] == 1:
                raise PermissionError("Access is denied")
            return original_read_text(self, encoding=encoding, errors=errors)
        
        with patch.object(Path, 'read_text', mock_read_text):
            with patch('time.sleep') as mock_sleep:
                content = read_file_with_retry(test_file, max_retries=2, initial_delay=0.01)
                
                assert content == test_content
                assert call_count[0] == 2  # Should have retried once
                assert mock_sleep.call_count == 1  # Should have slept once

    def test_read_file_with_retry_max_retries_exceeded(self, tmp_path):
        """Test read_file_with_retry raises OSError after max retries."""
        from scripts.utils.http_utils import read_file_with_retry
        from pathlib import Path
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test", encoding='utf-8')
        
        # Mock read_text to always raise PermissionError
        def mock_read_text(self, encoding=None, errors=None):
            raise PermissionError("Access is denied")
        
        with patch.object(Path, 'read_text', mock_read_text):
            with pytest.raises(OSError) as exc_info:
                read_file_with_retry(test_file, max_retries=2, initial_delay=0.01)
            
            assert "Max retries exceeded" in str(exc_info.value)

    def test_write_file_with_retry_success(self, tmp_path):
        """Test write_file_with_retry with successful write on first attempt."""
        from scripts.utils.http_utils import write_file_with_retry
        
        test_file = tmp_path / "test.md"
        test_content = "# Test Content\n\nThis is a test file."
        
        write_file_with_retry(test_file, test_content)
        
        assert test_file.exists()
        assert test_file.read_text(encoding='utf-8') == test_content

    def test_write_file_with_retry_permission_error(self, tmp_path):
        """Test write_file_with_retry retries on permission errors."""
        from scripts.utils.http_utils import write_file_with_retry
        from pathlib import Path
        
        test_file = tmp_path / "test.md"
        test_content = "# Test"
        
        # Mock write_text to raise PermissionError first, then succeed
        original_write_text = Path.write_text
        call_count = [0]
        
        def mock_write_text(self, data, encoding=None, errors=None, newline=None):
            call_count[0] += 1
            if call_count[0] == 1:
                raise PermissionError("Access is denied")
            return original_write_text(self, data, encoding=encoding, errors=errors, newline=newline)
        
        with patch.object(Path, 'write_text', mock_write_text):
            with patch('time.sleep') as mock_sleep:
                write_file_with_retry(test_file, test_content, max_retries=2, initial_delay=0.01)
                
                assert test_file.exists()
                assert test_file.read_text(encoding='utf-8') == test_content
                assert call_count[0] == 2  # Should have retried once
                assert mock_sleep.call_count == 1  # Should have slept once

    def test_write_file_with_retry_max_retries_exceeded(self, tmp_path):
        """Test write_file_with_retry raises OSError after max retries."""
        from scripts.utils.http_utils import write_file_with_retry
        from pathlib import Path
        
        test_file = tmp_path / "test.md"
        test_content = "# Test"
        
        # Mock write_text to always raise PermissionError
        def mock_write_text(self, data, encoding=None, errors=None, newline=None):
            raise PermissionError("Access is denied")
        
        with patch.object(Path, 'write_text', mock_write_text):
            with pytest.raises(OSError) as exc_info:
                write_file_with_retry(test_file, test_content, max_retries=2, initial_delay=0.01)
            
            assert "Max retries exceeded" in str(exc_info.value)

    def test_read_file_with_retry_exponential_backoff(self, tmp_path):
        """Test read_file_with_retry uses exponential backoff."""
        from scripts.utils.http_utils import read_file_with_retry
        from pathlib import Path
        
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test", encoding='utf-8')
        
        # Mock read_text to fail twice, then succeed
        original_read_text = Path.read_text
        call_count = [0]
        
        def mock_read_text(self, encoding=None, errors=None):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise PermissionError("Access is denied")
            return original_read_text(self, encoding=encoding, errors=errors)
        
        with patch.object(Path, 'read_text', mock_read_text):
            with patch('time.sleep') as mock_sleep:
                read_file_with_retry(test_file, max_retries=3, initial_delay=0.1, backoff_factor=2.0)
                
                # Should have slept twice with exponential backoff: 0.1s, 0.2s
                assert mock_sleep.call_count == 2
                calls = [call[0][0] for call in mock_sleep.call_args_list]
                assert calls[0] == pytest.approx(0.1, rel=0.1)
                assert calls[1] == pytest.approx(0.2, rel=0.1)
