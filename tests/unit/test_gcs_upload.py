import unittest
import os
import sys
import logging
from unittest.mock import patch, MagicMock, mock_open

# Add the parent directory to sys.path to import modules correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.gcs_upload import upload_to_gcs, upload_merged_data_to_gcs

class TestGCSUpload(unittest.TestCase):
    def setUp(self):
        # Sample data
        self.bucket_name = "test-bucket"
        self.source_file_name = "test.csv"
        self.destination_blob_name = "destination/test.csv"
        # Mock logger to avoid real logging
        self.logger = logging.getLogger('gcs_upload_logger')
        self.logger.handlers = []  # Clear handlers
        self.logger.addHandler(logging.NullHandler())

    @patch('utils.gcs_upload.storage.Client')
    @patch('utils.gcs_upload.logger')
    def test_upload_to_gcs_success(self, mock_logger, mock_storage_client):
        # Configure mocks
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_storage_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Call the function
        upload_to_gcs(self.bucket_name, self.source_file_name, self.destination_blob_name)
        
        # Verify behavior
        mock_storage_client.assert_called_once()
        mock_bucket.blob.assert_called_once_with(self.destination_blob_name)
        mock_blob.upload_from_filename.assert_called_once_with(self.source_file_name)
        mock_logger.info.assert_any_call(f"Attempting to upload {self.source_file_name} to GCS bucket {self.bucket_name}")
        mock_logger.info.assert_any_call(f"File {self.source_file_name} uploaded to {self.destination_blob_name}")

    @patch('utils.gcs_upload.storage.Client')
    @patch('utils.gcs_upload.logger')
    def test_upload_to_gcs_file_not_found(self, mock_logger, mock_storage_client):
        # Configure mocks to simulate FileNotFoundError
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_storage_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.upload_from_filename.side_effect = FileNotFoundError("File not found")
        
        # Expect an exception
        with self.assertRaises(FileNotFoundError):
            upload_to_gcs(self.bucket_name, self.source_file_name, self.destination_blob_name)
        
        # Verify logging
        mock_logger.error.assert_called_once_with(f"Error uploading {self.source_file_name} to GCS: File not found")

    @patch('utils.gcs_upload.os.path.join')
    @patch('utils.gcs_upload.upload_to_gcs')
    @patch('utils.gcs_upload.logger')
    def test_upload_merged_data_to_gcs_success(self, mock_logger, mock_upload_to_gcs, mock_join):
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        data = "dummy_data"  # Not used directly, but passed
        
        # Call the function
        upload_merged_data_to_gcs(data)
        
        # Verify behavior
        expected_source = f"{os.path.dirname(os.path.dirname(__file__))}/result_data/Documents_segments_merged_cleaned.csv"
        mock_upload_to_gcs.assert_called_once_with(
            "datasets-mlops-25",
            expected_source,
            "result_data/Documents_segments_merged_cleaned.csv"
        )
        mock_logger.info.assert_any_call("Preparing to upload merged data to GCS")
        mock_logger.info.assert_any_call("Merged data uploaded to GCS successfully")

    @patch('utils.gcs_upload.os.path.join')
    @patch('utils.gcs_upload.upload_to_gcs')
    @patch('utils.gcs_upload.logger')
    def test_upload_merged_data_to_gcs_failure(self, mock_logger, mock_upload_to_gcs, mock_join):
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_upload_to_gcs.side_effect = Exception("Upload failed")
        data = "dummy_data"
        
        # Expect an exception
        with self.assertRaises(Exception):
            upload_merged_data_to_gcs(data)
        
        # Verify logging
        mock_logger.error.assert_called_once_with("Error uploading merged data to GCS: Upload failed")
