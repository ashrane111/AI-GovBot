# test_create_vector_index.py
import unittest
import os
import numpy as np
import faiss
import pickle
import sys
from unittest.mock import patch, mock_open, MagicMock

# Add the parent directory to sys.path to import modules correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.create_vector_index import create_index

class TestCreateVectorIndex(unittest.TestCase):
    def setUp(self):
        # Create sample embeddings
        self.test_embeddings = np.random.random((10, 128)).astype('float32')
        self.serialized_embeddings = pickle.dumps(self.test_embeddings)
        
    @patch('os.makedirs')
    @patch('faiss.write_index')
    @patch('os.path.join')
    def test_create_index(self, mock_join, mock_write_index, mock_makedirs):
        # Configure mocks
        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_makedirs.return_value = None
        
        # Call the function
        create_index(self.serialized_embeddings)
        
        # Verify the function behavior
        mock_makedirs.assert_called_once()
        mock_write_index.assert_called_once()
        
        # Get the index object that was passed to write_index
        index_arg = mock_write_index.call_args[0][0]
        
        # Verify it's a FAISS index with the right dimension
        self.assertIsInstance(index_arg, faiss.IndexFlatL2)
        self.assertEqual(index_arg.d, 128)  # Check dimension matches our test data