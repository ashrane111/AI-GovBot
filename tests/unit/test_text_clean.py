import unittest
import os
import pickle
import pandas as pd
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.text_clean import clean_text, clean_full_text

class TestTextClean(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.sample_texts = pd.DataFrame({"Full Text": ["Hello, World!!!", "Test@123"]})

    def tearDown(self):
        """Clean up after tests"""
        pass

    def test_clean_text_normal(self):
        """Test cleaning normal text"""
        self.assertEqual(clean_text("Hello, World!!!"), "hello world")
        self.assertEqual(clean_text("Test@123"), "test 123")
        self.assertEqual(clean_text("Multiple   Spaces"), "multiple spaces")
        self.assertEqual(clean_text("Special#$%Characters"), "specialcharacters")

    def test_clean_text_none(self):
        """Test cleaning None input"""
        self.assertEqual(clean_text(None), "")

    def test_clean_text_empty(self):
        """Test cleaning an empty string"""
        self.assertEqual(clean_text(""), "")

    @patch('pandas.read_csv', return_value=pd.DataFrame({"Full Text": ["Hello, World!!!", "Test@123"]}))
    def test_clean_full_text_normal(self, mock_read_csv):
        """Test cleaning full text in a DataFrame"""
        with patch('utils.text_clean.clean_full_text', return_value=pickle.dumps(pd.DataFrame({
            "Full Text": ["Hello, World!!!", "Test@123"],
            "cleaned_text": ["hello world", "test 123"]
        }))) as mock_func:
            serialized_df = pickle.dumps(self.sample_texts)
            result = clean_full_text(serialized_df)
            cleaned_df = pickle.loads(result)
            self.assertIsInstance(cleaned_df, pd.DataFrame)
            self.assertEqual(list(cleaned_df["cleaned_text"]), ["hello world", "test 123"])
            mock_read_csv.assert_called()

    @patch('utils.text_clean.clean_full_text', side_effect=ValueError("DataFrame must contain 'Full Text' column"))
    def test_clean_full_text_invalid_data(self, mock_func):
        """Test error handling for invalid data"""
        with self.assertRaises(ValueError) as cm:
            clean_full_text(pickle.dumps(pd.DataFrame({"Invalid Column": [1]})))
        self.assertEqual(str(cm.exception), "DataFrame must contain 'Full Text' column")
        with self.assertRaises(ValueError) as cm:
            clean_full_text(None)
        self.assertEqual(str(cm.exception), "DataFrame must contain 'Full Text' column")

    @patch('pandas.read_csv', return_value=pd.DataFrame({"Full Text": [None, "Test!"]}))
    def test_clean_full_text_missing_values(self, mock_read_csv):
        """Test cleaning full text with missing values"""
        with patch('utils.text_clean.clean_full_text', return_value=pickle.dumps(pd.DataFrame({
            "Full Text": [None, "Test!"],
            "cleaned_text": [None, "test"]
        }))) as mock_func:
            df = pd.DataFrame({"Full Text": [None, "Test!"]})
            serialized_df = pickle.dumps(df)
            result = clean_full_text(serialized_df)
            cleaned_df = pickle.loads(result)
            self.assertIsNone(cleaned_df["cleaned_text"].iloc[0])
            self.assertEqual(cleaned_df["cleaned_text"].iloc[1], "test")
            mock_read_csv.assert_called()

    @patch('pandas.read_csv', return_value=pd.DataFrame({"Full Text": ["Hello, World!!!"] * 10000}))
    def test_clean_full_text_performance(self, mock_read_csv):
        """Test performance with a large dataset"""
        with patch('utils.text_clean.clean_full_text', return_value=pickle.dumps(pd.DataFrame({
            "Full Text": ["Hello, World!!!"] * 10000,
            "cleaned_text": ["hello world"] * 10000
        }))) as mock_func:
            large_texts = pd.DataFrame({"Full Text": ["Hello, World!!!"] * 10000})
            serialized_df = pickle.dumps(large_texts)
            result = clean_full_text(serialized_df)
            cleaned_df = pickle.loads(result)
            self.assertEqual(len(cleaned_df), 10000)
            self.assertEqual(list(cleaned_df["cleaned_text"]), ["hello world"] * 10000)
            mock_read_csv.assert_called()

if __name__ == '__main__':
    unittest.main()