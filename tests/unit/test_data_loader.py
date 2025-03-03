# test_data_loader.py
import unittest
import pandas as pd
import pickle
import sys
import os
from unittest.mock import patch, mock_open

# Add the parent directory to sys.path to import modules correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.data_loader import load_data

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        # Create a sample DataFrame
        self.test_df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        
    @patch('pandas.read_csv')
    def test_load_data(self, mock_read_csv):
        # Configure mock
        mock_read_csv.return_value = self.test_df
        
        # Call the function
        result = load_data('test_path.csv')
        
        # Verify the function called read_csv
        mock_read_csv.assert_called_once_with('test_path.csv')
        
        # Verify the result is serialized data
        deserialized = pickle.loads(result)
        pd.testing.assert_frame_equal(deserialized, self.test_df)