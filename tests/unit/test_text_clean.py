import unittest
import os
import pandas as pd
import pickle
from unittest.mock import patch, mock_open, MagicMock

# Add the parent directory to sys.path to import the module
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.text_clean import clean_text, clean_full_text

class TestTextClean(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame with test data, no reliance on external directories
        self.test_df = pd.DataFrame({
            'Full Text': ['Text with  extra  spaces!', 'Special $#@ characters', 'UPPERCASE text'],
            'Link to document': ['http://example.com/ test', 'http://special#@', 'http://UPPERCASE']
        })
        self.serialized_df = pickle.dumps(self.test_df)
        
        # Expected cleaned DataFrame (for reference, though not directly used in assertions)
        self.expected_cleaned = pd.DataFrame({
            'Full Text': ['Text with  extra  spaces!', 'Special $#@ characters', 'UPPERCASE text'],
            'cleaned_text': ['text with extra spaces', 'special  characters', 'uppercase text'],
            'Link to document': ['http://example.com/test', 'http://special', 'http://uppercase']  # Assuming clean_url behavior
        })

    def test_clean_text(self):
        # Test individual text cleaning function
        test_cases = [
            ('Text with  extra  spaces!', 'text with extra spaces'),
            ('Special $#@ characters', 'special  characters'),
            ('UPPERCASE text', 'uppercase text')
        ]
        
        for input_text, expected in test_cases:
            self.assertEqual(clean_text(input_text), expected)
    
    @patch('utils.text_clean.os.makedirs')
    @patch('utils.text_clean.os.path.join')
    def test_clean_full_text(self, mock_join, mock_makedirs):
        """Test clean_full_text with mocked file operations."""
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Patch DataFrame.to_csv to prevent file writing
        with patch.object(pd.DataFrame, 'to_csv'):
            # Call the function
            result = clean_full_text(self.serialized_df)
            
            # Verify behavior (assuming clean_full_text creates a directory)
            # If clean_full_text no longer uses os.makedirs after removing merged_inputs,
            # this assertion can be removed or adjusted based on actual behavior
            mock_makedirs.assert_called_once_with(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cleaned_data'),
                exist_ok=True
            )  # Adjust 'cleaned_data' to match your actual output_dir_name if different
            
            # Deserialize the result and check cleaned text
            deserialized = pickle.loads(result)
            self.assertTrue('cleaned_text' in deserialized.columns, "cleaned_text column missing")
            self.assertEqual(deserialized['cleaned_text'].tolist(), 
                             ['text with extra spaces', 'special  characters', 'uppercase text'],
                             "Cleaned text does not match expected output")
            # Optionally check cleaned URLs if clean_url is part of clean_full_text
            self.assertEqual(deserialized['Link to document'].tolist(),
                             ['http://example.com/test', 'http://special', 'http://uppercase'],
                             "Cleaned URLs do not match expected output")
