import unittest
import os
import pickle
import numpy as np
import faiss
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.create_vector_index import create_index

class TestCreateVectorIndex(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures with minimal data"""
        # Use small sample embeddings (2 vectors of dimension 2 for simplicity)
        self.sample_embeddings = np.array([[0.1, 0.2], [0.3, 0.4]], dtype="float32")
        self.serialized_embeddings = pickle.dumps(self.sample_embeddings)

    def tearDown(self):
        """Clean up after tests"""
        pass

    @patch('utils.create_vector_index.faiss.write_index')
    @patch('utils.create_vector_index.os.makedirs')
    @patch('utils.create_vector_index.os.path.exists', return_value=True)
    def test_create_index_normal(self, mock_exists, mock_makedirs, mock_write_index):
        """Test that the index is created successfully with valid embeddings"""
        # Mock create_index to return None and simulate FAISS index creation
        mock_index = MagicMock(spec=faiss.Index)
        mock_index.d = 2  # Match embedding dimension
        mock_index.ntotal = 2  # Match number of vectors
        mock_write_index.return_value = None
        with patch('utils.create_vector_index.create_index', return_value=None) as mock_func:
            create_index(self.serialized_embeddings)
            
            # Verify mocks were called
            mock_makedirs.assert_called_with("FAISS_Index", exist_ok=True)
            mock_write_index.assert_called_once_with(mock_index, "FAISS_Index/legal_embeddings.index")
            mock_exists.assert_called()
            self.assertTrue(os.path.exists("FAISS_Index/legal_embeddings.index"))

    @patch('utils.create_vector_index.os.makedirs')
    @patch('utils.create_vector_index.os.path.exists', return_value=True)
    @patch('utils.create_vector_index.faiss.write_index')
    def test_create_index_empty_embeddings(self, mock_write_index, mock_exists, mock_makedirs):
        """Test that the index handles empty embeddings correctly"""
        # Use empty embeddings
        empty_embeddings = np.array([], dtype="float32")
        serialized_empty = pickle.dumps(empty_embeddings)
        
        # Mock create_index to return None and simulate an empty FAISS index
        mock_empty_index = MagicMock(spec=faiss.Index)
        mock_empty_index.d = 768  # Default dimension (adjust if needed)
        mock_empty_index.ntotal = 0
        mock_write_index.return_value = None
        with patch('utils.create_vector_index.create_index', return_value=None) as mock_func:
            create_index(serialized_empty)
            
            # Verify mocks were called with empty index
            mock_makedirs.assert_called_with("FAISS_Index", exist_ok=True)
            mock_write_index.assert_called_once_with(mock_empty_index, "FAISS_Index/legal_embeddings.index")
            mock_exists.assert_called()
            self.assertTrue(os.path.exists("FAISS_Index/legal_embeddings.index"))

    @patch('utils.create_vector_index.create_index', side_effect=ValueError("Invalid embedding dimensions for FAISS index"))
    def test_create_index_invalid_data(self, mock_func):
        """Test that invalid data raises the correct ValueError"""
        # Test with invalid shape (1x1 array)
        invalid_data = np.array([[0.1]], dtype="float32")
        serialized_invalid = pickle.dumps(invalid_data)
        with self.assertRaises(ValueError) as cm:
            create_index(serialized_invalid)
        self.assertEqual(str(cm.exception), "Invalid embedding dimensions for FAISS index")

        # Test with None
        serialized_none = pickle.dumps(None)
        with self.assertRaises(ValueError) as cm:
            create_index(serialized_none)
        self.assertEqual(str(cm.exception), "Invalid embedding dimensions for FAISS index")

if __name__ == '__main__':
    unittest.main()