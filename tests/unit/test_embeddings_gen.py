import unittest
import os
import numpy as np
import pandas as pd
import pickle
from unittest.mock import patch, MagicMock, mock_open

# Add the parent directory to sys.path to import the module
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))
from utils.embeddings_gen import generate_embeddings

class TestEmbeddingsGen(unittest.TestCase):
    def setUp(self):
        """Set up common test data."""
        self.test_df = pd.DataFrame({
            'cleaned_text': ['This is a test', 'Another test sentence']
        })
        self.serialized_df = pickle.dumps(self.test_df)
        self.mock_embeddings = np.random.random((2, 128)).astype('float32')

    @patch('utils.embeddings_gen.os.makedirs')
    @patch('utils.embeddings_gen.os.path.join')
    @patch('utils.embeddings_gen.pickle.dump')
    @patch('utils.embeddings_gen.SentenceTransformer')
    def test_generate_embeddings_success(self, mock_transformer, mock_pickle_dump, mock_join, mock_makedirs):
        """Test successful embedding generation."""
        # Configure mocks
        mock_model = MagicMock()
        mock_model.encode.return_value = self.mock_embeddings
        mock_transformer.return_value = mock_model
        mock_join.side_effect = lambda *args: '/'.join(args)

        # Calculate expected paths
        base_dir = os.path.dirname(os.path.dirname(__file__))
        output_dir = os.path.join(base_dir, 'embeddings')
        output_path = os.path.join(output_dir, 'embeddings.pkl')

        # Patch open to prevent file writing
        with patch('builtins.open', mock_open()) as mock_file:
            # Call the function
            result = generate_embeddings(self.serialized_df)

            # Verify behavior
            mock_transformer.assert_called_once_with("sentence-transformers/multi-qa-mpnet-base-dot-v1")
            mock_model.encode.assert_called_once_with(
                ['This is a test', 'Another test sentence'],
                batch_size=32,
                show_progress_bar=True,
                normalize_embeddings=True
            )
            mock_makedirs.assert_any_call(os.path.join(base_dir, 'util_logs'), exist_ok=True)
            mock_makedirs.assert_any_call(output_dir, exist_ok=True)
            mock_file.assert_called_once_with(output_path, 'wb')
            mock_pickle_dump.assert_called_once_with(self.mock_embeddings, mock_file())
            
            # Verify the result
            deserialized = pickle.loads(result)
            self.assertTrue(np.array_equal(deserialized, self.mock_embeddings))

    @patch('utils.embeddings_gen.os.makedirs')
    @patch('utils.embeddings_gen.os.path.join')
    @patch('utils.embeddings_gen.pickle.dump')
    @patch('utils.embeddings_gen.SentenceTransformer')
    def test_generate_embeddings_empty_df(self, mock_transformer, mock_pickle_dump, mock_join, mock_makedirs):
        """Test embedding generation with an empty DataFrame."""
        # Configure mocks
        mock_model = MagicMock()
        mock_model.encode.return_value = np.empty((0, 128), dtype='float32')  # Empty embeddings
        mock_transformer.return_value = mock_model
        mock_join.side_effect = lambda *args: '/'.join(args)

        # Create empty DataFrame
        empty_df = pd.DataFrame({'cleaned_text': []})
        serialized_empty = pickle.dumps(empty_df)

        # Patch open
        with patch('builtins.open', mock_open()) as mock_file:
            # Call the function
            result = generate_embeddings(serialized_empty)

            # Verify behavior
            mock_model.encode.assert_called_once_with(
                [],
                batch_size=32,
                show_progress_bar=True,
                normalize_embeddings=True
            )
            # Check that the result is serialized empty embeddings
            self.assertEqual(result, pickle.dumps(np.empty((0, 128), dtype='float32')))

    @patch('utils.embeddings_gen.os.makedirs')
    @patch('utils.embeddings_gen.os.path.join')
    @patch('utils.embeddings_gen.SentenceTransformer')
    def test_generate_embeddings_failure(self, mock_transformer, mock_join, mock_makedirs):
        """Test embedding generation when an exception occurs."""
        # Configure mocks to simulate a failure
        mock_transformer.side_effect = Exception("Model loading failed")
        mock_join.side_effect = lambda *args: '/'.join(args)

        # Call the function and expect an exception
        with self.assertRaises(Exception) as context:
            generate_embeddings(self.serialized_df)
        self.assertEqual(str(context.exception), "Model loading failed")
