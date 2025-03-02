import unittest
import os
import sys
import pandas as pd
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.data_schema_generation import generate_data_statistics

class TestDataStatsGeneration(unittest.TestCase):
    def setUp(self):
        self.input_csv = "test_input.csv"
        self.output_stats_path = "output/stats.txt"
        self.output_schema_path = "output/schema.pbtxt"
        self.test_df = pd.DataFrame({'col1': [1, 2], 'col2': ['a', 'b']})

    @patch('utils.data_schema_generation.os.path.exists')
    @patch('utils.data_schema_generation.os.makedirs')
    @patch('utils.data_schema_generation.pd.read_csv')
    @patch('utils.data_schema_generation.tfdv.generate_statistics_from_dataframe')
    @patch('utils.data_schema_generation.tfdv.write_stats_text')
    @patch('utils.data_schema_generation.tfdv.infer_schema')
    @patch('utils.data_schema_generation.tfdv.write_schema_text')
    def test_generate_data_statistics_success(self, mock_write_schema, mock_infer_schema, 
                                              mock_write_stats, mock_generate_stats, 
                                              mock_read_csv, mock_makedirs, mock_exists):
        # Configure mocks
        mock_exists.return_value = True
        mock_read_csv.return_value = self.test_df
        mock_stats = MagicMock()
        mock_generate_stats.return_value = mock_stats
        mock_schema = MagicMock()
        mock_infer_schema.return_value = mock_schema
        
        # Call the function
        stats_path, schema_path = generate_data_statistics(self.input_csv, self.output_stats_path, self.output_schema_path)
        
        # Verify behavior
        mock_read_csv.assert_called_once_with(self.input_csv)
        mock_generate_stats.assert_called_once_with(self.test_df)
        mock_write_stats.assert_called_once_with(mock_stats, self.output_stats_path)
        mock_infer_schema.assert_called_once_with(mock_stats)
        mock_write_schema.assert_called_once_with(mock_schema, self.output_schema_path)
        self.assertEqual(stats_path, self.output_stats_path)
        self.assertEqual(schema_path, self.output_schema_path)

    @patch('utils.data_schema_generation.os.path.exists')
    def test_generate_data_statistics_file_not_found(self, mock_exists):
        # Configure mocks
        mock_exists.return_value = False
        
        # Expect an exception
        with self.assertRaises(FileNotFoundError) as context:
            generate_data_statistics(self.input_csv, self.output_stats_path, self.output_schema_path)
        self.assertIn(f"Input CSV not found: {self.input_csv}", str(context.exception))

    @patch('utils.data_schema_generation.os.path.exists')
    @patch('utils.data_schema_generation.os.makedirs')
    @patch('utils.data_schema_generation.pd.read_csv')
    @patch('utils.data_schema_generation.tfdv.generate_statistics_from_dataframe')
    def test_generate_data_statistics_empty_csv(self, mock_generate_stats, mock_read_csv, mock_makedirs, mock_exists):
        # Configure mocks
        mock_exists.return_value = True
        empty_df = pd.DataFrame()
        mock_read_csv.return_value = empty_df
        mock_stats = MagicMock()
        mock_generate_stats.return_value = mock_stats
        
        # Call the function (should still work with empty data)
        stats_path, schema_path = generate_data_statistics(self.input_csv, self.output_stats_path, self.output_schema_path)
        
        # Verify behavior
        mock_generate_stats.assert_called_once_with(empty_df)
        self.assertEqual(stats_path, self.output_stats_path)
        self.assertEqual(schema_path, self.output_schema_path)
