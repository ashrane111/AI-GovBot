import unittest
import os
import numpy as np
import pickle
import pandas as pd
import sys
from unittest.mock import patch, MagicMock, mock_open

# Add the parent directory to sys.path but don't import the module yet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))

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
        # Configure mocks BEFORE importing the function
        mock_model = MagicMock()
        mock_model.encode.return_value = self.mock_embeddings
        mock_transformer.return_value = mock_model
        
        # Mock os.path.join to return consistent paths
        mock_join.side_effect = lambda *args: '/'.join(args)
        
        # Import the function here, AFTER patching
        from utils.embeddings_gen import generate_embeddings
        
        # Calculate output_dir based on the location of embeddings_gen.py
        module_dir = os.path.dirname(generate_embeddings.__code__.co_filename)
        parent_dir = os.path.dirname(module_dir)
        output_dir = os.path.abspath(os.path.join(parent_dir, 'embeddings'))
        output_path = f"{output_dir}/embeddings.pkl"

        # Patch open to prevent file writing and capture calls
        with patch('builtins.open', mock_open()) as mock_file:
            # Call the function
            result = generate_embeddings(self.serialized_df)
            
            # Verify function behavior
            mock_transformer.assert_called_once_with("sentence-transformers/multi-qa-mpnet-base-dot-v1")
            mock_model.encode.assert_called_once_with(
                ['This is a test', 'Another test sentence'], 
                show_progress_bar=True
            )
            mock_makedirs.assert_called_once_with(output_dir, exist_ok=True)
            mock_file.assert_called_once_with(output_path, 'wb')
            
            # Verify pickle.dump call manually
            self.assertEqual(mock_pickle_dump.call_count, 1, "pickle.dump should be called exactly once")
            dump_args, dump_kwargs = mock_pickle_dump.call_args
            self.assertTrue(np.array_equal(dump_args[0], self.mock_embeddings), "The dumped embeddings should match")
            self.assertEqual(dump_args[1], mock_file(), "The file object should match")
            self.assertEqual(dump_kwargs, {}, "No unexpected keyword arguments should be passed")
            
            # Verify the result
            deserialized = pickle.loads(result)
            self.assertTrue(np.array_equal(deserialized, self.mock_embeddings))