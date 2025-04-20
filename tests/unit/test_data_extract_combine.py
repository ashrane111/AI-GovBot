# test_data_extract_combine.py
import unittest
import os
import pandas as pd
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import modules correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))

from utils.data_extract_combine import extract_and_merge_documents, make_input_dir

class TestDataExtractCombine(unittest.TestCase):
    def setUp(self):
        # Sample data for testing
        self.documents_data = pd.DataFrame({
            'AGORA ID': [1, 2],
            'Official name': ['Doc1', 'Doc2'],
            'Casual name': ['D1', 'D2'],
            'Link to document': ['link1', 'link2'],
            'Authority': ['Auth1', 'Auth2'],
            'Collections': ['Col1', 'Col2'],
            'Most recent activity': ['Act1', 'Act2'],
            'Most recent activity date': ['2023-01-01', '2023-02-01'],
            'Proposed date': ['2022-01-01', '2022-02-01'],
            'Primarily applies to the government': [True, False],
            'Primarily applies to the private sector': [False, True],
            'Short summary': ['Short1', 'Short2'],
            'Long summary': ['Long1', 'Long2'],
            'Tags': ['Tag1', 'Tag2']
        })
        
        self.segments_data = pd.DataFrame({
            'Document ID': [1, 1, 2],
            'Text': ['Text1', 'Text2', 'Text3'],
            'Summary': ['Sum1', 'Sum2', 'Sum3']
        })

        self.authorities_data = pd.DataFrame({
            'Name': ['Auth1', 'Auth2'],
            'Jurisdiction': ['US', 'Other']
        })
    
    @patch('os.makedirs')
    def test_make_input_dir(self, mock_makedirs):
        # Test creating the directory
        make_input_dir()
        mock_makedirs.assert_called_once_with('merged_input')
        
        # Test handling existing directory
        mock_makedirs.side_effect = FileExistsError()
        make_input_dir()  # Should not raise an exception
    
    @patch('pandas.read_csv')
    @patch('pandas.DataFrame.to_csv')
    @patch('pandas.DataFrame.to_excel')
    @patch('os.path.join')
    @patch('os.makedirs')
    def test_extract_and_merge_documents(self, mock_makedirs, mock_join, mock_to_excel, 
                                         mock_to_csv, mock_read_csv):
        # Configure the mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_read_csv.side_effect = [self.documents_data, self.segments_data, self.authorities_data]
        
        # Call the function
        extract_and_merge_documents(temp_dir="test_dir")
        
        # Verify correct calls were made
        self.assertEqual(mock_read_csv.call_count, 3)
        mock_to_csv.assert_called_once()
        mock_to_excel.assert_called_once()