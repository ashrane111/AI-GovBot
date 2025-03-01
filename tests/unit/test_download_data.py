# test_download_data.py
import unittest
import os
import io
import sys
import zipfile
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import modules correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.download_data import download_and_unzip_data_file

class TestDownloadData(unittest.TestCase):
    @patch('os.makedirs')
    @patch('requests.get')
    @patch('zipfile.ZipFile')
    @patch('os.path.join')
    def test_download_and_unzip_data_file_success(self, mock_join, mock_zipfile, mock_get, mock_makedirs):
        # Configure mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'fake zip content'
        mock_get.return_value = mock_response
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Create a mock for the zipfile context manager
        mock_zipfile_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zipfile_instance
        
        # Call the function
        result = download_and_unzip_data_file('http://example.com/test.zip', 'test_output')
        
        # Verify the function behavior
        mock_get.assert_called_once_with('http://example.com/test.zip', stream=True)
        mock_makedirs.assert_called()
        mock_zipfile.assert_called()
        mock_zipfile_instance.extractall.assert_called_once()
    
    @patch('os.makedirs')
    @patch('requests.get')
    @patch('os.path.join')
    def test_download_and_unzip_data_file_failure(self, mock_join, mock_get, mock_makedirs):
        # Configure mocks
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Call the function and expect an exception
        with self.assertRaises(Exception):
            download_and_unzip_data_file('http://example.com/test.zip', 'test_output')