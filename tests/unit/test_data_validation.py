import unittest
import os
import sys
import pandas as pd
import pickle
import logging
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import modules correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.data_validation import format_date, summarize_text, preprocess_data

class TestDataValidation(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame
        self.test_df = pd.DataFrame({
            'Authority': ['Auth1', 'Auth2'],
            'Full Text': ['Text1', 'Text2'],
            'Most recent activity date': ['2023-01-01', '2022-01-01'],
            'Proposed date': ['2022-12-01', '2022-02-01'],
            'Casual name': ['C1', None],
            'Short summary': ['S1', None],
            'Long summary': [None, 'L2']
        })
        self.serialized_df = pickle.dumps(self.test_df)
        # Mock logger
        self.logger = logging.getLogger('data_validation_logger')
        self.logger.handlers = []
        self.logger.addHandler(logging.NullHandler())

    def test_format_date_success(self):
        # Call the function
        result_df = format_date(self.test_df.copy())
        
        # Verify behavior
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result_df['Most recent activity date']))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result_df['Proposed date']))
        self.assertEqual(result_df['Most recent activity date'].iloc[1], pd.Timestamp('2022-02-01'))  # Adjusted to Proposed date
        self.assertFalse(result_df['Proposed date'].isna().any())  # NaN dropped

    def test_format_date_invalid_dates(self):
        invalid_df = pd.DataFrame({
            'Most recent activity date': ['invalid_date'],
            'Proposed date': ['also_invalid']
        })
        result_df = format_date(invalid_df)
        self.assertTrue(result_df.empty)  # All rows dropped due to invalid dates

    def test_summarize_text_success(self):
        text = "This is a long text that needs to be summarized."
        result = summarize_text(text, length=10)
        self.assertEqual(result, "This is a ")
        self.assertEqual(summarize_text(None), "")
        self.assertEqual(summarize_text("short"), "short")

    @patch('utils.data_validation.pd.read_csv')
    @patch('utils.data_validation.os.path.join')
    @patch('utils.data_validation.logger')
    def test_preprocess_data_success(self, mock_logger, mock_join, mock_read_csv):
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        auth_df = pd.DataFrame({'Name': ['Auth1', 'Auth2']})
        mock_read_csv.return_value = auth_df
        
        # Call the function
        result = preprocess_data(self.serialized_df)
        
        # Verify behavior
        deserialized = pickle.loads(result)
        self.assertEqual(len(deserialized), 2)  # All rows valid
        self.assertEqual(deserialized['Casual name'].iloc[1], "N/A")
        self.assertEqual(deserialized['Short summary'].iloc[1], "N/A")
        self.assertEqual(deserialized['Long summary'].iloc[0], "Text1"[:500])
        mock_logger.info.assert_any_call("Loaded data from serialized input")
        mock_logger.info.assert_any_call("Serialized validated data")

    @patch('utils.data_validation.pd.read_csv')
    @patch('utils.data_validation.os.path.join')
    @patch('utils.data_validation.logger')
    def test_preprocess_data_missing_authorities(self, mock_logger, mock_join, mock_read_csv):
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_read_csv.side_effect = FileNotFoundError("authorities.csv not found")
        
        # Expect an exception
        with self.assertRaises(FileNotFoundError):
            preprocess_data(self.serialized_df)
        
        # Verify logging
        mock_logger.error.assert_called_once_with("An error ocurred while validating and processing data: authorities.csv not found")

    @patch('utils.data_validation.pd.read_csv')
    @patch('utils.data_validation.os.path.join')
    @patch('utils.data_validation.logger')
    def test_preprocess_data_empty_input(self, mock_logger, mock_join, mock_read_csv):
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        auth_df = pd.DataFrame({'Name': ['Auth1']})
        mock_read_csv.return_value = auth_df
        empty_df = pd.DataFrame(columns=['Authority', 'Full Text'])
        serialized_empty = pickle.dumps(empty_df)
        
        # Call the function
        result = preprocess_data(serialized_empty)
        
        # Verify behavior
        deserialized = pickle.loads(result)
        self.assertTrue(deserialized.empty)