import unittest
import os
import sys
import logging
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.gcs_upload import upload_to_gcs, upload_merged_data_to_gcs, compute_sha256

class TestGCSUpload(unittest.TestCase):
    def setUp(self):
        self.bucket_name = "test-bucket"
        self.source_file_name = "test.csv"
        self.destination_blob_name = "dest/test.csv"
        self.logger = logging.getLogger('gcs_upload_logger')
        self.logger.handlers = []
        self.logger.addHandler(logging.NullHandler())

    @patch('utils.gcs_upload.compute_sha256')
    @patch('utils.gcs_upload.storage.Client')
    @patch('utils.gcs_upload.logger')
    def test_upload_to_gcs_success(self, mock_logger, mock_storage_client, mock_compute_sha256):
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        # Set up existing metadata
        mock_blob.metadata = None
        mock_storage_client.return_value.get_bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_compute_sha256.return_value = "mocked_sha256_digest"
        
        upload_to_gcs(self.bucket_name, self.source_file_name, self.destination_blob_name)
        
        mock_storage_client.assert_called_once()
        mock_bucket.blob.assert_called_once_with(self.destination_blob_name)
        mock_blob.upload_from_filename.assert_called_once_with(self.source_file_name)
        mock_compute_sha256.assert_called_once_with(self.source_file_name)
        mock_logger.info.assert_any_call(f"Attempting to upload {self.source_file_name} to GCS bucket {self.bucket_name}")
        mock_logger.info.assert_any_call("Computed SHA256: mocked_sha256_digest")
        
        # Verify that metadata was updated correctly
        self.assertEqual(mock_blob.metadata, {'sha256': 'mocked_sha256_digest'})
        mock_blob.patch.assert_called_once()

    @patch('utils.gcs_upload.compute_sha256')
    @patch('utils.gcs_upload.storage.Client')
    @patch('utils.gcs_upload.logger')
    def test_upload_to_gcs_failure(self, mock_logger, mock_storage_client, mock_compute_sha256):
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_storage_client.return_value.get_bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.upload_from_filename.side_effect = Exception("GCS error")
        
        with self.assertRaises(Exception):
            upload_to_gcs(self.bucket_name, self.source_file_name, self.destination_blob_name)
        
        mock_logger.error.assert_called_once_with(f"Error uploading {self.source_file_name} to GCS: GCS error")

    @patch('utils.gcs_upload.os.path.join')
    @patch('utils.gcs_upload.upload_to_gcs')
    @patch('utils.gcs_upload.logger')
    def test_upload_merged_data_to_gcs_success(self, mock_logger, mock_upload_to_gcs, mock_join):
        # Make mock_join return a consistent value
        mock_join.return_value = "/mocked/path/to/file"
        
        upload_merged_data_to_gcs("datasets-mlops-25")
        
        # Check calls count
        self.assertEqual(mock_upload_to_gcs.call_count, 2)
        
        # Order might matter, so don't use assert_has_calls
        # Instead check individual calls
        mock_upload_to_gcs.assert_any_call(
            "datasets-mlops-25", 
            "/mocked/path/to/file", 
            "faiss_index/index.faiss"
        )
        mock_upload_to_gcs.assert_any_call(
            "datasets-mlops-25", 
            "/mocked/path/to/file", 
            "faiss_index/index.pkl"
        )
        
        mock_logger.info.assert_any_call(".faiss uploaded to GCS successfully")
        mock_logger.info.assert_any_call(".pkl data uploaded to GCS successfully")

    @patch('utils.gcs_upload.os.path.join')
    @patch('utils.gcs_upload.upload_to_gcs')
    @patch('utils.gcs_upload.logger')
    def test_upload_merged_data_to_gcs_failure(self, mock_logger, mock_upload_to_gcs, mock_join):
        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_upload_to_gcs.side_effect = FileNotFoundError("File not found")
        
        with self.assertRaises(FileNotFoundError):
            upload_merged_data_to_gcs("datasets-mlops-25")
        
        mock_logger.error.assert_called_once_with("Error uploading merged data to GCS: File not found")
    
    @patch('utils.gcs_upload.compute_sha256')
    @patch('utils.gcs_upload.storage.Client')
    @patch('utils.gcs_upload.logger')
    def test_upload_to_gcs_called_twice(self, mock_logger, mock_storage_client, mock_compute_sha256):
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_storage_client.return_value.get_bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_compute_sha256.return_value = "mocked_sha256_digest"
        
        # Call the function twice
        upload_to_gcs(self.bucket_name, self.source_file_name, self.destination_blob_name)
        upload_to_gcs(self.bucket_name, self.source_file_name, self.destination_blob_name)
        
        # Assert that the method was called twice
        self.assertEqual(mock_blob.upload_from_filename.call_count, 2)
        mock_blob.upload_from_filename.assert_has_calls([
            call(self.source_file_name),
            call(self.source_file_name)
        ])
        
        # Assert compute_sha256 was called twice
        self.assertEqual(mock_compute_sha256.call_count, 2)
        
        mock_logger.info.assert_any_call(f"Attempting to upload {self.source_file_name} to GCS bucket {self.bucket_name}")

if __name__ == '__main__':
    unittest.main()