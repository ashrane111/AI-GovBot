import unittest
import os
import pickle
import pandas as pd
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_data

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.sample_data = pd.DataFrame({"Full Text": ["Sample text"], "AGORA ID": [1]})
        self.temp_file = "/tmp/test.csv"

    def tearDown(self):
        """Clean up after tests"""
        pass

    @patch('pandas.read_csv', return_value=pd.DataFrame({"Full Text": ["Sample text"], "AGORA ID": [1]}))
    def test_load_data_normal(self, mock_read_csv):
        """Test loading data from a valid CSV file"""
        with patch('utils.data_loader.load_data', return_value=pickle.dumps(self.sample_data)) as mock_func:
            result = load_data(self.temp_file)
            loaded_df = pickle.loads(result)
            self.assertIsInstance(loaded_df, pd.DataFrame)
            self.assertEqual(len(loaded_df), 1)
            self.assertEqual(loaded_df["Full Text"].iloc[0], "Sample text")
            mock_read_csv.assert_called()

    @patch('os.path.exists', return_value=False)
    def test_load_data_missing_file(self, mock_exists):
        """Test error handling for missing files"""
        with self.assertRaises(FileNotFoundError) as cm:
            load_data("nonexistent.csv")
        self.assertEqual(str(cm.exception), "File not found: nonexistent.csv")
        mock_exists.assert_called()

    @patch('pandas.read_csv', return_value=pd.DataFrame())
    def test_load_data_empty_csv(self, mock_read_csv):
        """Test loading data from an empty CSV file"""
        with patch('utils.data_loader.load_data', return_value=pickle.dumps(pd.DataFrame())) as mock_func:
            result = load_data(self.temp_file)
            loaded_df = pickle.loads(result)
            self.assertIsInstance(loaded_df, pd.DataFrame)
            self.assertEqual(len(loaded_df), 0)
            mock_read_csv.assert_called()

    @patch('utils.data_loader.load_data', side_effect=TypeError("Path must be a string"))
    def test_load_data_invalid_path(self, mock_func):
        """Test error handling for invalid path types"""
        with self.assertRaises(TypeError) as cm:
            load_data(None)
        self.assertEqual(str(cm.exception), "Path must be a string")
        with self.assertRaises(TypeError) as cm:
            load_data(123)
        self.assertEqual(str(cm.exception), "Path must be a string")

if __name__ == '__main__':
    unittest.main()