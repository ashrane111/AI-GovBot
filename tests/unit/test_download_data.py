import pytest
from utils.download_data import download_and_unzip_data_file
from unittest.mock import patch, Mock
import os
import zipfile
import io
import requests

@pytest.fixture
def mock_requests_get():
    with patch("requests.get") as mock_get:
        yield mock_get

def test_download_and_unzip_success(mock_requests_get, tmp_path):
    # Mock a successful ZIP download
    zip_content = io.BytesIO()
    with zipfile.ZipFile(zip_content, "w") as zf:
        zf.writestr("test.txt", "Hello")
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.content = zip_content.getvalue()

    output_dir = download_and_unzip_data_file("http://fake.url", str(tmp_path / "output"))
    assert os.path.exists(output_dir)
    assert os.path.exists(os.path.join(output_dir, "test.txt"))

def test_download_and_unzip_network_timeout(mock_requests_get, tmp_path):
    # Mock a network timeout
    mock_requests_get.side_effect = requests.exceptions.Timeout
    with pytest.raises(requests.exceptions.Timeout, match="Request timed out"):
        download_and_unzip_data_file("http://fake.url", str(tmp_path / "output"))

def test_download_and_unzip_invalid_url(mock_requests_get):
    mock_requests_get.return_value.status_code = 404
    with pytest.raises(Exception, match="Failed to download file, status code: 404"):
        download_and_unzip_data_file("http://invalid.url", "output_dir")

def test_download_and_unzip_empty_url():
    with pytest.raises(ValueError, match="URL cannot be empty"):
        download_and_unzip_data_file("", "output_dir")