# test_text_clean.py
import unittest
import os
import pandas as pd
import pickle
import sys
from unittest.mock import patch, mock_open, MagicMock

# Add the parent directory to sys.path to import modules correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.text_clean import clean_text, clean_full_text

class TestTextClean(unittest.TestCase):
    def setUp(self):
        # Sample data for testing
        self.test_df = pd.DataFrame({
            'Full Text': ['Text with  extra  spaces!', 'Special $#@ characters', 'UPPERCASE text']
        })
        self.serialized_df = pickle.dumps(self.test_df)
        
        # Expected cleaned text
        self.expected_cleaned = pd.DataFrame({
            'Full Text': ['Text with  extra  spaces!', 'Special $#@ characters', 'UPPERCASE text'],
            'cleaned_text': ['text with extra spaces', 'special  characters', 'uppercase text']
        })
    
    def test_clean_text(self):
        # Test individual text cleaning
        test_cases = [
            ('Text with  extra  spaces!', 'text with extra spaces'),
            ('Special $#@ characters', 'special  characters'),
            ('UPPERCASE text', 'uppercase text')
        ]
        
        for input_text, expected in test_cases:
            self.assertEqual(clean_text(input_text), expected)
    
    @patch('os.makedirs')
    @patch('os.path.join')
    def test_clean_full_text(self, mock_join, mock_makedirs):
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Patch DataFrame.to_csv to prevent file writing
        with patch.object(pd.DataFrame, 'to_csv'):
            # Call the function
            result = clean_full_text(self.serialized_df)
            
            # Verify function behavior
            mock_makedirs.assert_called_once()
            
            # Verify the result
            deserialized = pickle.loads(result)
            self.assertTrue('cleaned_text' in deserialized.columns)
            self.assertEqual(deserialized['cleaned_text'][0], 'text with extra spaces')
            self.assertEqual(deserialized['cleaned_text'][1], 'special  characters')
            self.assertEqual(deserialized['cleaned_text'][2], 'uppercase text')