import unittest
import os
import numpy as np
import pickle
import pandas as pd
import sys
from unittest.mock import patch, MagicMock, mock_open

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.embeddings_gen import generate_embeddings

class TestEmbeddingsGen(unittest.TestCase):
    def setUp(self):
        self.test_df = pd.DataFrame({
            'cleaned_text': ['This is a test', 'Another test sentence']
        })
        self.serialized_df = pickle.dumps(self.test_df)
        self.mock_embeddings = np.random.random((2, 128)).astype('float32')
    
    @patch('os.makedirs')
    @patch('os.path.join')
    @patch('pickle.dump')
    @patch('sentence_transformers.SentenceTransformer')
    def test_generate_embeddings(self, mock_transformer, mock_pickle_dump, mock_join, mock_makedirs):
        mock_model = MagicMock()
        mock_model.encode.return_value = self.mock_embeddings
        mock_transformer.return_value = mock_model
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        output_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'embeddings'))
        output_path = f"{output_dir}/embeddings.pkl"
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = generate_embeddings(self.serialized_df)
            
            mock_transformer.assert_called_once_with("sentence-transformers/multi-qa-mpnet-base-dot-v1")
            # Flexible check for encode call
            call_args, call_kwargs = mock_model.encode.call_args
            self.assertEqual(call_args[0], ['This is a test', 'Another test sentence'])
            self.assertTrue(call_kwargs['show_progress_bar'])
            mock_makedirs.assert_called_once_with(output_dir, exist_ok=True)
            mock_file.assert_called_once_with(output_path, 'wb')
            mock_pickle_dump.assert_called_once_with(self.mock_embeddings, mock_file())
            
            deserialized = pickle.loads(result)
            self.assertTrue(np.array_equal(deserialized, self.mock_embeddings))