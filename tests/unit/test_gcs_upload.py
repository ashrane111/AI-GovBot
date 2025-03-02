import unittest
import os
import sys
import logging
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.gcs_upload import upload_to_gcs, upload_merged_data_to_gcs

class TestGCSUpload(unittest.TestCase):
    def setUp(self):
        self.bucket_name = "test-bucket"
        self.source_file_name = "test.csv"
        self.destination_blob_name = "dest/test.csv"
        self.logger = logging.getLogger('gcs_upload_logger')
        self.logger.handlers = []
        self.logger.addHandler(logging.NullHandler())

    @patch('utils.gcs_upload.storage.Client')
    @patch('utils.gcs_upload.logger')
    def test_upload_to_gcs_success(self, mock_logger, mock_storage_client):
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_storage_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        upload_to_gcs(self.bucket_name, self.source_file_name, self.destination_blob_name)
        
        mock_storage_client.assert_called_once()
        mock_bucket.blob.assert_called_once_with(self.destination_blob_name)
        mock_blob.upload_from_filename.assert_called_once_with(self.source_file_name)
        mock_logger.info.assert_any_call(f"Attempting to upload {self.source_file_name} to GCS bucket {self.bucket_name}")

    @patch('utils.gcs_upload.storage.Client')
    @patch('utils.gcs_upload.logger')
    def test_upload_to_gcs_failure(self, mock_logger, mock_storage_client):
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_storage_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.upload_from_filename.side_effect = Exception("GCS error")
        
        with self.assertRaises(Exception):
            upload_to_gcs(self.bucket_name, self.source_file_name, self.destination_blob_name)
        
        mock_logger.error.assert_called_once_with(f"Error uploading {self.source_file_name} to GCS: GCS error")

    @patch('utils.gcs_upload.os.path.join')
    @patch('utils.gcs_upload.upload_to_gcs')
    @patch('utils.gcs_upload.logger')
    def test_upload_merged_data_to_gcs_success(self, mock_logger, mock_upload_to_gcs, mock_join):
        mock_join.side_effect = lambda *args: '/'.join(args)
        data = "dummy_data"
        
        from utils.gcs_upload import upload_merged_data_to_gcs
        
        module_dir = os.path.dirname(upload_merged_data_to_gcs.__code__.co_filename)
        parent_dir = os.path.dirname(module_dir)
        expected_source = os.path.join(parent_dir, "merged_input/Documents_segments_merged.csv")
        
        upload_merged_data_to_gcs(data)
        
        mock_upload_to_gcs.assert_called_once_with(
            "datasets-mlops-25",
            expected_source,
            "result_data/Documents_segments_merged.csv"
        )
        mock_logger.info.assert_any_call("Merged data uploaded to GCS successfully")

    @patch('utils.gcs_upload.os.path.join')
    @patch('utils.gcs_upload.upload_to_gcs')
    @patch('utils.gcs_upload.logger')
    def test_upload_merged_data_to_gcs_failure(self, mock_logger, mock_upload_to_gcs, mock_join):
        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_upload_to_gcs.side_effect = FileNotFoundError("File not found")
        data = "dummy_data"
        
        with self.assertRaises(FileNotFoundError):
            upload_merged_data_to_gcs(data)
        
        mock_logger.error.assert_called_once_with("Error uploading merged data to GCS: File not found")