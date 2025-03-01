# test_save_file.py
import unittest
import os
import sys
import pickle
import pandas as pd
import numpy as np
import faiss
from unittest.mock import patch, mock_open, MagicMock

# Add the parent directory to sys.path to import modules correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.save_file import SaveFile

class TestSaveFile(unittest.TestCase):
    def setUp(self):
        # Create different test data types
        self.test_df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        
        self.test_embeddings = np.random.random((10, 128)).astype('float32')
        
        # Create a FAISS index
        self.dimension = 128
        self.test_index = faiss.IndexFlatL2(self.dimension)
        self.test_index.add(self.test_embeddings)
    
    @patch('os.makedirs')
    @patch('os.path.join')
    def test_init(self, mock_join, mock_makedirs):
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Create instance
        save_file = SaveFile('test_dir', 'test_file.csv', self.test_df)
        
        # Verify instance setup
        mock_makedirs.assert_called_once()
        self.assertEqual(save_file.data, self.test_df)
    
    @patch('os.makedirs')
    @patch('os.path.join')
    def test_save_csv_file(self, mock_join, mock_makedirs):
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Create instance
        save_file = SaveFile('test_dir', 'test_file.csv', self.test_df)
        
        # Test csv saving
        with patch.object(pd.DataFrame, 'to_csv') as mock_to_csv:
            save_file.save_csv_file()
            mock_to_csv.assert_called_once()
    
    @patch('os.makedirs')
    @patch('os.path.join')
    def test_save_serialized_file(self, mock_join, mock_makedirs):
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Create instance
        save_file = SaveFile('test_dir', 'test_file.pkl', self.test_embeddings)
        
        # Test pickle saving
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('pickle.dump') as mock_dump:
                save_file.save_serialized_file()
                mock_dump.assert_called_once_with(self.test_embeddings, mock_file())
    
    @patch('os.makedirs')
    @patch('os.path.join')
    @patch('faiss.write_index')
    def test_save_faiss_index_file(self, mock_write_index, mock_join, mock_makedirs):
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Create instance
        save_file = SaveFile('test_dir', 'test_file.index', self.test_index)
        
        # Test faiss index saving
        save_file.save_faiss_index_file()
        mock_write_index.assert_called_once_with(self.test_index, save_file.output_path)