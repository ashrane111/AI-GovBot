import unittest
import os
import sys
import pandas as pd
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.data_validation import validate_downloaded_data_files, check_validation_status

class TestDataValidation(unittest.TestCase):
    def setUp(self):
        self.file_schema_pairs = [("test.csv", "test_schema.pbtxt")]
        self.test_df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})

    @patch('utils.data_validation.os.path.exists')
    @patch('utils.data_validation.pd.read_csv')
    @patch('utils.data_validation.tfdv.generate_statistics_from_dataframe')
    @patch('utils.data_validation.tfdv.load_schema_text')
    @patch('utils.data_validation.tfdv.validate_statistics')
    def test_validate_downloaded_data_files_success(self, mock_validate, mock_load_schema, 
                                                    mock_generate_stats, mock_read_csv, mock_exists):
        # Configure mocks
        mock_exists.return_value = True
        mock_read_csv.return_value = self.test_df
        mock_stats = MagicMock()
        mock_generate_stats.return_value = mock_stats
        mock_schema = MagicMock()
        mock_load_schema.return_value = mock_schema
        mock_anomalies = MagicMock(anomaly_info={})
        mock_validate.return_value = mock_anomalies
        
        # Call the function
        result = validate_downloaded_data_files(self.file_schema_pairs)
        
        # Verify behavior
        mock_read_csv.assert_called_once_with("test.csv")
        mock_generate_stats.assert_called_once_with(self.test_df)
        mock_load_schema.assert_called_once_with("test_schema.pbtxt")
        mock_validate.assert_called_once_with(mock_stats, mock_schema)
        self.assertEqual(result, {"result": True, "anomalies": {}})

    @patch('utils.data_validation.os.path.exists')
    def test_validate_downloaded_data_files_missing_file(self, mock_exists):
        # Configure mocks
        mock_exists.side_effect = [False, True]  # File missing, schema exists
        
        # Call the function
        result = validate_downloaded_data_files(self.file_schema_pairs)
        
        # Verify behavior
        self.assertEqual(result, {
            "result": False,
            "anomalies": {"test.csv": ["File not found"]}
        })

    @patch('utils.data_validation.os.path.exists')
    def test_validate_downloaded_data_files_missing_schema(self, mock_exists):
        # Configure mocks
        mock_exists.side_effect = [True, False]  # File exists, schema missing
        
        # Call the function
        result = validate_downloaded_data_files(self.file_schema_pairs)
        
        # Verify behavior
        self.assertEqual(result, {
            "result": False,
            "anomalies": {"test.csv": ["Schema file not found"]}
        })

    @patch('utils.data_validation.os.path.exists')
    @patch('utils.data_validation.pd.read_csv')
    def test_validate_downloaded_data_files_empty_csv(self, mock_read_csv, mock_exists):
        # Configure mocks
        mock_exists.return_value = True
        mock_read_csv.return_value = pd.DataFrame()  # Empty DataFrame
        
        # Call the function
        result = validate_downloaded_data_files(self.file_schema_pairs)
        
        # Verify behavior
        self.assertEqual(result, {
            "result": False,
            "anomalies": {"test.csv": ["CSV file is empty"]}
        })

    @patch('utils.data_validation.os.path.exists')
    @patch('utils.data_validation.pd.read_csv')
    def test_validate_downloaded_data_files_unreadable_csv(self, mock_read_csv, mock_exists):
        # Configure mocks
        mock_exists.return_value = True
        mock_read_csv.side_effect = pd.errors.EmptyDataError("No columns to parse")
        
        # Call the function
        result = validate_downloaded_data_files(self.file_schema_pairs)
        
        # Verify behavior
        self.assertEqual(result, {
            "result": False,
            "anomalies": {"test.csv": ["CSV is empty or unreadable"]}
        })

    @patch('utils.data_validation.os.path.exists')
    @patch('utils.data_validation.pd.read_csv')
    @patch('utils.data_validation.tfdv.generate_statistics_from_dataframe')
    @patch('utils.data_validation.tfdv.load_schema_text')
    @patch('utils.data_validation.tfdv.validate_statistics')
    def test_validate_downloaded_data_files_anomalies(self, mock_validate, mock_load_schema, 
                                                      mock_generate_stats, mock_read_csv, mock_exists):
        # Configure mocks
        mock_exists.return_value = True
        mock_read_csv.return_value = self.test_df
        mock_stats = MagicMock()
        mock_generate_stats.return_value = mock_stats
        mock_schema = MagicMock()
        mock_load_schema.return_value = mock_schema
        mock_anomalies = MagicMock(anomaly_info={'col1': MagicMock(description="Type mismatch")})
        mock_validate.return_value = mock_anomalies
        
        # Call the function
        result = validate_downloaded_data_files(self.file_schema_pairs)
        
        # Verify behavior
        self.assertEqual(result["result"], False)
        self.assertEqual(result["anomalies"], {
            "test.csv": ["Feature: col1, Error: Type mismatch"]
        })

    def test_validate_downloaded_data_files_empty_pairs(self):
        # Test with empty file-schema pairs
        result = validate_downloaded_data_files([])
        
        # Verify behavior
        self.assertEqual(result, {"result": True, "anomalies": {}})

    def test_check_validation_status_success(self):
        # Mock Airflow task instance
        mock_ti = MagicMock()
        mock_ti.xcom_pull.return_value = {"result": True, "anomalies": {}}
        
        # Call the function (should not raise)
        check_validation_status(ti=mock_ti)
        
        # Verify no XCom push for anomalies
        mock_ti.xcom_push.assert_not_called()

    def test_check_validation_status_failure(self):
        # Mock Airflow task instance
        mock_ti = MagicMock()
        mock_ti.xcom_pull.return_value = {
            "result": False,
            "anomalies": {"test.csv": ["CSV file is empty"]}
        }
        
        # Expect an exception
        with self.assertRaises(ValueError) as context:
            check_validation_status(ti=mock_ti)
        
        # Verify XCom push and error message
        expected_formatted = "File: test.csv<br>&nbsp;&nbsp;- CSV file is empty"
        mock_ti.xcom_push.assert_called_once_with(key='anomalies', value=expected_formatted)
        self.assertIn("Schema validation failed", str(context.exception))
