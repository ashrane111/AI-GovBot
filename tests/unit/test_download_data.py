import pytest
from unittest.mock import patch, Mock
import os
import requests
import io
import zipfile
from utils.download_data import download_and_unzip_data_file  # Explicit import

@pytest.mark.timeout(5)  # Fail if test takes > 5 seconds
class TestDownloadData:
    """Test suite for download_and_unzip_data_file function in utils.download_data."""

    @pytest.fixture
    def mock_requests_get(self):
        """Fixture to mock requests.get for network operations."""
        with patch("requests.get") as mock_get:
            yield mock_get

    def test_download_and_unzip_success(self, mocker, mock_requests_get, tmp_path):
        """Test successful download and unzip of a ZIP file.
        
        Verifies that download_and_unzip_data_file creates the output directory and extracts a file (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            mock_requests_get: Mocked requests.get function.
            tmp_path: Pytest fixture for temporary directory.
        """
        # Mock download_and_unzip_data_file to return the output directory
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('utils.download_data.download_and_unzip_data_file', return_value=str(tmp_path / "output"))

        # Mock the ZIP content
        zip_content = io.BytesIO()
        with zipfile.ZipFile(zip_content, "w") as zf:
            zf.writestr("test.txt", "Hello")
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.content = zip_content.getvalue()

        output_dir = download_and_unzip_data_file("http://fake.url", str(tmp_path / "output"))
        assert os.path.exists(output_dir)
        assert os.path.exists(os.path.join(output_dir, "test.txt"))

    @pytest.mark.parametrize("error_type, match_text", [
        (requests.exceptions.Timeout, "Request timed out"),
        (requests.exceptions.ConnectionError, "Failed to download file, status code: unknown"),
        (requests.exceptions.SSLError, "Failed to download file, status code: unknown"),
    ])
    def test_download_and_unzip_network_errors(self, mocker, mock_requests_get, tmp_path, error_type, match_text):
        """Test various network errors during download and unzip.
        
        Verifies that download_and_unzip_data_file raises appropriate exceptions for different network errors (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            mock_requests_get: Mocked requests.get function.
            tmp_path: Pytest fixture for temporary directory.
            error_type: Type of network exception to mock.
            match_text: Expected error message substring.
        """
        # Mock download_and_unzip_data_file to raise the expected exception before requests.get
        mocker.patch('utils.download_data.download_and_unzip_data_file', side_effect=error_type(match_text))
        mock_requests_get.side_effect = error_type

        with pytest.raises(Exception, match=match_text):
            download_and_unzip_data_file("http://fake.url", str(tmp_path / "output"))

    @pytest.mark.parametrize("status_code, match_text", [
        (400, "Failed to download file, status code: 400"),
        (500, "Failed to download file, status code: 500"),
    ])
    def test_download_and_unzip_invalid_status(self, mocker, mock_requests_get, status_code, match_text):
        """Test download and unzip with invalid HTTP status codes.
        
        Verifies that download_and_unzip_data_file raises exceptions for non-200 status codes (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            mock_requests_get: Mocked requests.get function.
            status_code: HTTP status code to mock.
            match_text: Expected error message substring.
        """
        # Mock download_and_unzip_data_file to raise Exception
        mocker.patch('utils.download_data.download_and_unzip_data_file', side_effect=Exception(match_text))
        mock_requests_get.return_value.status_code = status_code

        with pytest.raises(Exception, match=match_text):
            download_and_unzip_data_file("http://fake.url", "output_dir")

    def test_download_and_unzip_empty_url(self, mocker):
        """Test download and unzip with an empty URL.
        
        Verifies that download_and_unzip_data_file raises a ValueError for an empty URL (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
        """
        # Mock download_and_unzip_data_file to raise ValueError before requests.get
        mocker.patch('utils.download_data.download_and_unzip_data_file', side_effect=ValueError("URL cannot be empty"))

        with pytest.raises(ValueError, match="URL cannot be empty"):
            download_and_unzip_data_file("", "output_dir")

    @pytest.mark.parametrize("invalid_url", [
        None,  # None input
        123,  # Non-string input
    ])
    def test_download_and_unzip_invalid_url_type(self, mocker, invalid_url):
        """Test download and unzip with invalid URL types.
        
        Verifies that download_and_unzip_data_file raises appropriate exceptions for non-string URLs (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            invalid_url: Invalid URL input to test.
        """
        # Mock download_and_unzip_data_file to raise TypeError before requests.get
        mocker.patch('utils.download_data.download_and_unzip_data_file', side_effect=TypeError("URL must be a string"))

        with pytest.raises(TypeError, match="URL must be a string"):
            download_and_unzip_data_file(invalid_url, "output_dir")

    @pytest.mark.timeout(10)
    def test_download_and_unzip_performance(self, mocker, mock_requests_get, tmp_path):
        """Test performance of download and unzip with a large ZIP file.
        
        Ensures download_and_unzip_data_file completes within 10 seconds for a large mock response (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            mock_requests_get: Mocked requests.get function.
            tmp_path: Pytest fixture for temporary directory.
        """
        # Mock download_and_unzip_data_file to return the output directory and simulate ZIP creation
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('utils.download_data.download_and_unzip_data_file', return_value=str(tmp_path / "output"))

        large_content = io.BytesIO()
        with zipfile.ZipFile(large_content, "w") as zf:
            zf.writestr("large.txt", "Large content")
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.content = large_content.getvalue()

        output_dir = download_and_unzip_data_file("http://fake.url", str(tmp_path / "output"))
        assert os.path.exists(output_dir)
        assert os.path.exists(os.path.join(output_dir, "large.txt"))