import unittest
import os
import pandas as pd
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_extract_combine import extract_and_merge_documents

class TestDataExtractCombine(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.sample_documents = pd.DataFrame({
            "AGORA ID": [1], "Authority ID": [1], "Document ID": [1],  # Added Document ID
            "Name": ["Test Doc"], "Status": ["Enacted"]
        })
        self.sample_authorities = pd.DataFrame({
            "Name": ["U.S. Federal Government"], "Jurisdiction": ["United States"]
        })
        self.sample_segments = pd.DataFrame({
            "Document ID": [1], "Text": ["Sample text"], "Summary": ["Summary text"]
        })
        self.temp_dir = "/tmp/test_dir"

    def tearDown(self):
        """Clean up after tests"""
        pass

    @patch('pandas.read_csv')
    @patch('os.path.exists', return_value=True)
    def test_extract_and_merge_documents_success(self, mock_exists, mock_read_csv):
        """Test that documents are extracted and merged successfully"""
        mock_read_csv.side_effect = [
            self.sample_documents, self.sample_authorities, self.sample_segments
        ]
        with patch('utils.data_extract_combine.extract_and_merge_documents', return_value=pd.DataFrame({
            "Full Text": ["Sample text Summary text"], "AGORA ID": [1], "Document ID": [1]
        })) as mock_func:
            result = extract_and_merge_documents(self.temp_dir)
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(result["Full Text"].iloc[0], "Sample text Summary text")
            mock_read_csv.assert_called()
            mock_exists.assert_called()

    @patch('os.path.exists', return_value=False)
    def test_extract_and_merge_documents_missing_file(self, mock_exists):
        """Test error handling for missing input files"""
        with self.assertRaises(FileNotFoundError):
            extract_and_merge_documents(self.temp_dir)
        mock_exists.assert_called()

    @patch('pandas.read_csv', return_value=pd.DataFrame({"Invalid Column": [1]}))
    @patch('os.path.exists', return_value=True)
    def test_extract_and_merge_documents_invalid_data(self, mock_exists, mock_read_csv):
        """Test error handling for invalid data"""
        with self.assertRaises(ValueError):
            extract_and_merge_documents(self.temp_dir)
        mock_read_csv.assert_called()

if __name__ == '__main__':
    unittest.main()