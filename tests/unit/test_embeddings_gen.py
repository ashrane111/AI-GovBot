import pytest
import pandas as pd
import pickle
import numpy as np
import os
from unittest.mock import patch

@pytest.mark.timeout(5)  # Fail if test takes > 5 seconds
class TestEmbeddingsGen:
    """Test suite for generate_embeddings function in utils.embeddings_gen."""

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Fixture to mock SentenceTransformer for embedding generation."""
        with patch("sentence_transformers.SentenceTransformer") as mock_st:
            mock_model = mock_st.return_value
            mock_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]], dtype="float32")  # Placeholder for 768 dimensions
            yield mock_model

    @pytest.mark.parametrize("texts, expected_shape", [
        (["hello world", "test text"], (2, 768)),  # Normal case
        (["single text"], (1, 768)),  # Single text
    ])
    def test_generate_embeddings_normal(self, mock_sentence_transformer, texts, expected_shape):
        """Test generating embeddings with valid text data.
        
        Verifies that generate_embeddings produces embeddings with the expected shape and saves them to a pickle file.
        
        Args:
            mock_sentence_transformer: Mocked SentenceTransformer object.
            texts: List of text inputs to test.
            expected_shape: Expected shape of the generated embeddings (rows, columns).
        """
        df = pd.DataFrame({"cleaned_text": texts})
        serialized_df = pickle.dumps(df)
        result = generate_embeddings(serialized_df)
        embeddings = pickle.loads(result)
        assert embeddings.shape == expected_shape
        assert os.path.exists("embeddings/embeddings.pkl")

    def test_generate_embeddings_empty_df(self, mock_sentence_transformer):
        """Test generating embeddings with an empty DataFrame.
        
        Verifies that generate_embeddings handles an empty DataFrame by returning empty embeddings.
        """
        df = pd.DataFrame({"cleaned_text": []})
        serialized_df = pickle.dumps(df)
        result = generate_embeddings(serialized_df)
        embeddings = pickle.loads(result)
        assert len(embeddings) == 0
        assert os.path.exists("embeddings/embeddings.pkl")

    @pytest.mark.parametrize("invalid_data", [
        pd.DataFrame({"cleaned_text": [None, "text"]}),  # None in data
        None,  # None input
    ])
    def test_generate_embeddings_invalid_data(self, mock_sentence_transformer, invalid_data):
        """Test generating embeddings with invalid data.
        
        Verifies that generate_embeddings raises appropriate exceptions for invalid data.
        
        Args:
            mock_sentence_transformer: Mocked SentenceTransformer object.
            invalid_data: Invalid input data to test.
        """
        serialized_data = pickle.dumps(invalid_data) if invalid_data is not None else None
        with pytest.raises(ValueError, match="Invalid data format for generating embeddings"):
            generate_embeddings(serialized_data)

    @pytest.mark.timeout(10)
    def test_generate_embeddings_performance(self, mock_sentence_transformer):
        """Test performance of generating embeddings with a large dataset.
        
        Ensures generate_embeddings completes within 10 seconds for a large number of texts.
        
        Args:
            mock_sentence_transformer: Mocked SentenceTransformer object.
        """
        texts = ["hello world"] * 1000  # Large dataset
        df = pd.DataFrame({"cleaned_text": texts})
        serialized_df = pickle.dumps(df)
        result = generate_embeddings(serialized_df)
        embeddings = pickle.loads(result)
        assert len(embeddings) == 1000
        assert embeddings.shape == (1000, 768)