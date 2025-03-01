# test_embeddings_gen.py
import unittest
import os
import numpy as np
import pickle
import sys
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd

# Add the parent directory to sys.path to import modules correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.embeddings_gen import generate_embeddings

class TestEmbeddingsGen(unittest.TestCase):
    def setUp(self):
        # Create a sample DataFrame
        self.test_df = pd.DataFrame({
            'cleaned_text': ['This is a test', 'Another test sentence']
        })
        self.serialized_df = pickle.dumps(self.test_df)
        
        # Mock embeddings
        self.mock_embeddings = np.random.random((2, 128)).astype('float32')
    
    @patch('os.makedirs')
    @patch('os.path.join')
    @patch('pickle.dump')
    @patch('sentence_transformers.SentenceTransformer')
    def test_generate_embeddings(self, mock_transformer, mock_pickle_dump, mock_join, mock_makedirs):
        # Configure mocks
        mock_model = MagicMock()
        mock_model.encode.return_value = self.mock_embeddings
        mock_transformer.return_value = mock_model
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Patch open to prevent file writing
        with patch('builtins.open', mock_open()):
            # Call the function
            result = generate_embeddings(self.serialized_df)
            
            # Verify function behavior
            mock_transformer.assert_called_once()
            mock_model.encode.assert_called_once_with(['This is a test', 'Another test sentence'], show_progress_bar=True)
            mock_makedirs.assert_called_once()
            mock_pickle_dump.assert_called_once()
            
            # Verify the result
            deserialized = pickle.loads(result)
            self.assertTrue(np.array_equal(deserialized, self.mock_embeddings))