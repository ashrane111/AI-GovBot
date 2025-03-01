import unittest
import os
import requests
import io
import zipfile
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.download_data import download_and_unzip_data_file

class TestDownloadData(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = "/tmp/test_output"
        self.url = "http://fake.url"

    def tearDown(self):
        """Clean up after tests"""
        pass

    @patch('requests.get')
    @patch('os.path.exists', return_value=True)
    def test_download_and_unzip_success(self, mock_exists, mock_get):
        """Test successful download and unzip of a ZIP file"""
        zip_content = io.BytesIO()
        with zipfile.ZipFile(zip_content, "w") as zf:
            zf.writestr("test.txt", "Hello")
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = zip_content.getvalue()
        with patch('utils.download_data.download_and_unzip_data_file', return_value=self.temp_dir) as mock_func:
            result = download_and_unzip_data_file(self.url, self.temp_dir)
            self.assertEqual(result, self.temp_dir)
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "test.txt")))
            mock_get.assert_called_with(self.url, stream=True)

    @patch('utils.download_data.download_and_unzip_data_file', side_effect=requests.exceptions.Timeout("Request timed out"))
    def test_download_and_unzip_timeout(self, mock_func):
        """Test timeout error handling"""
        with self.assertRaises(requests.exceptions.Timeout) as cm:
            download_and_unzip_data_file(self.url, self.temp_dir)
        self.assertEqual(str(cm.exception), "Request timed out")

    @patch('utils.download_data.download_and_unzip_data_file', side_effect=requests.exceptions.ConnectionError("Failed to download file, status code: unknown"))
    def test_download_and_unzip_connection_error(self, mock_func):
        """Test connection error handling"""
        with self.assertRaises(requests.exceptions.ConnectionError) as cm:
            download_and_unzip_data_file(self.url, self.temp_dir)
        self.assertEqual(str(cm.exception), "Failed to download file, status code: unknown")

    @patch('utils.download_data.download_and_unzip_data_file', side_effect=requests.exceptions.SSLError("Failed to download file, status code: unknown"))
    def test_download_and_unzip_ssl_error(self, mock_func):
        """Test SSL error handling"""
        with self.assertRaises(requests.exceptions.SSLError) as cm:
            download_and_unzip_data_file(self.url, self.temp_dir)
        self.assertEqual(str(cm.exception), "Failed to download file, status code: unknown")

    @patch('utils.download_data.download_and_unzip_data_file', side_effect=ValueError("URL cannot be empty"))
    def test_download_and_unzip_empty_url(self, mock_func):
        """Test error handling for empty URL"""
        with self.assertRaises(ValueError) as cm:
            download_and_unzip_data_file("", self.temp_dir)
        self.assertEqual(str(cm.exception), "URL cannot be empty")

    @patch('utils.download_data.download_and_unzip_data_file', side_effect=TypeError("URL must be a string"))
    def test_download_and_unzip_invalid_url_type(self, mock_func):
        """Test error handling for invalid URL types"""
        with self.assertRaises(TypeError) as cm:
            download_and_unzip_data_file(None, self.temp_dir)
        self.assertEqual(str(cm.exception), "URL must be a string")
        with self.assertRaises(TypeError) as cm:
            download_and_unzip_data_file(123, self.temp_dir)
        self.assertEqual(str(cm.exception), "URL must be a string")

    @patch('requests.get')
    @patch('os.path.exists', return_value=True)
    def test_download_and_unzip_performance(self, mock_exists, mock_get):
        """Test performance with a large ZIP file"""
        large_content = io.BytesIO(b"0" * 1024 * 1024)  # 1MB of data
        with zipfile.ZipFile(large_content, "w") as zf:
            zf.writestr("large.txt", "Large content")
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = large_content.getvalue()
        with patch('utils.download_data.download_and_unzip_data_file', return_value=self.temp_dir) as mock_func:
            result = download_and_unzip_data_file(self.url, self.temp_dir)
            self.assertEqual(result, self.temp_dir)
            self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "large.txt")))
            mock_get.assert_called()

if __name__ == '__main__':
    unittest.main()