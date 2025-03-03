import unittest
import os
import numpy as np
import pandas as pd
import pickle
from unittest.mock import patch, MagicMock, mock_open

# Add the parent directory to sys.path for importing the module
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/data-pipeline/dags')))

class TestEmbeddingsGen(unittest.TestCase):
    def setUp(self):
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

        # Import the function after patching
        from utils.embeddings_gen import generate_embeddings

        # Calculate base_dir based on embeddings_gen.py's location
        module_dir = os.path.dirname(generate_embeddings.__code__.co_filename)
        base_dir = os.path.dirname(module_dir)  # Should be /home/runner/work/AI-GovBot/AI-GovBot/data/data-pipeline/dags

        # Expected paths
        util_logs_dir = os.path.join(base_dir, 'util_logs')
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

            mock_makedirs.assert_called_once()
            mock_file.assert_called_once_with(output_path, 'wb')
            # Manually verify the arguments passed to pickle.dump
            self.assertEqual(mock_pickle_dump.call_count, 1, "pickle.dump should be called exactly once")
            call_args = mock_pickle_dump.call_args[0]  # Get the positional arguments
            self.assertTrue(np.array_equal(call_args[0], self.mock_embeddings), "The embeddings argument does not match")
            self.assertEqual(call_args[1], mock_file(), "The file object argument does not match")

            # Verify the result
            deserialized = pickle.loads(result)
            self.assertTrue(np.array_equal(deserialized, self.mock_embeddings))