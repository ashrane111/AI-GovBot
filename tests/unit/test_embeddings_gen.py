import unittest
import os
import pickle
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.embeddings_gen import generate_embeddings

class TestEmbeddingsGen(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.sample_texts = pd.DataFrame({"cleaned_text": ["hello world", "test text"]})

    def tearDown(self):
        """Clean up after tests"""
        pass

    @patch('sentence_transformers.SentenceTransformer')
    def test_generate_embeddings_normal(self, mock_st):
        """Test generating embeddings for valid text data"""
        mock_model = mock_st.return_value
        mock_model.encode.return_value = np.zeros((2, 768), dtype=np.float32)
        with patch('utils.embeddings_gen.generate_embeddings', return_value=pickle.dumps(np.zeros((2, 768), dtype=np.float32))) as mock_func:
            serialized_df = pickle.dumps(self.sample_texts)
            result = generate_embeddings(serialized_df)
            embeddings = pickle.loads(result)
            self.assertEqual(embeddings.shape, (2, 768))
            mock_model.encode.assert_called()

    @patch('sentence_transformers.SentenceTransformer')
    def test_generate_embeddings_empty_df(self, mock_st):
        """Test generating embeddings for an empty DataFrame"""
        mock_model = mock_st.return_value
        mock_model.encode.return_value = np.array([], dtype=np.float32)
        with patch('utils.embeddings_gen.generate_embeddings', return_value=pickle.dumps(np.array([], dtype=np.float32))) as mock_func:
            empty_df = pd.DataFrame({"cleaned_text": []})
            serialized_df = pickle.dumps(empty_df)
            result = generate_embeddings(serialized_df)
            embeddings = pickle.loads(result)
            self.assertEqual(len(embeddings), 0)
            mock_model.encode.assert_not_called()

    @patch('utils.embeddings_gen.generate_embeddings', side_effect=ValueError("Invalid data format for generating embeddings"))
    def test_generate_embeddings_invalid_data(self, mock_func):
        """Test error handling for invalid data"""
        with self.assertRaises(ValueError) as cm:
            generate_embeddings(pickle.dumps(pd.DataFrame({"cleaned_text": [None, "text"]})))
        self.assertEqual(str(cm.exception), "Invalid data format for generating embeddings")
        with self.assertRaises(ValueError) as cm:
            generate_embeddings(None)
        self.assertEqual(str(cm.exception), "Invalid data format for generating embeddings")

    @patch('sentence_transformers.SentenceTransformer')
    def test_generate_embeddings_performance(self, mock_st):
        """Test performance with a large dataset"""
        mock_model = mock_st.return_value
        mock_model.encode.return_value = np.zeros((1000, 768), dtype=np.float32)
        with patch('utils.embeddings_gen.generate_embeddings', return_value=pickle.dumps(np.zeros((1000, 768), dtype=np.float32))) as mock_func:
            large_texts = pd.DataFrame({"cleaned_text": ["hello world"] * 1000})
            serialized_df = pickle.dumps(large_texts)
            result = generate_embeddings(serialized_df)
            embeddings = pickle.loads(result)
            self.assertEqual(embeddings.shape, (1000, 768))
            mock_model.encode.assert_called()

if __name__ == '__main__':
    unittest.main()