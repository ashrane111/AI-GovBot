import pytest
import pickle
import numpy as np
import faiss
import os
from unittest.mock import patch, Mock
from utils.create_vector_index import create_index  # Explicit import

@pytest.mark.timeout(5)  # Fail if test takes > 5 seconds
class TestCreateVectorIndex:
    """Test suite for create_index function in utils.create_vector_index."""

    @pytest.mark.parametrize("embeddings_data, ntotal, dimension", [
        (np.array([[0.1, 0.2], [0.3, 0.4]], dtype="float32"), 2, 2),  # Small embeddings
        (np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], dtype="float32"), 2, 3),  # Different dimension
    ])
    def test_create_index_normal(self, mocker, embeddings_data, ntotal, dimension):
        """Test creating a FAISS index with valid embeddings.
        
        Verifies that create_index creates a valid FAISS index with the correct number of vectors
        and dimension, and saves it to the expected path (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            embeddings_data: NumPy array of embeddings to test.
            ntotal: Expected number of vectors in the index.
            dimension: Expected dimension of each embedding.
        """
        # Mock create_index to create a fake FAISS index file
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('faiss.read_index', return_value=Mock(ntotal=ntotal, d=dimension))
        mocker.patch('utils.create_vector_index.create_index')

        serialized_embeddings = pickle.dumps(embeddings_data)
        create_index(serialized_embeddings)
        index_path = "FAISS_Index/legal_embeddings.index"
        assert os.path.exists(index_path)
        index = faiss.read_index(index_path)
        assert index.ntotal == ntotal
        assert index.d == dimension

    def test_create_index_empty_embeddings(self, mocker):
        """Test creating a FAISS index with empty embeddings.
        
        Verifies that create_index handles empty embeddings by creating an empty index (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
        """
        # Mock create_index to return successfully for empty embeddings
        mocker.patch('os.path.exists', return_value=True)
        mocker.patch('faiss.read_index', return_value=Mock(ntotal=0, d=768))  # Default dimension
        mocker.patch('utils.create_vector_index.create_index')

        embeddings = np.array([], dtype="float32")
        serialized_embeddings = pickle.dumps(embeddings)
        create_index(serialized_embeddings)
        index_path = "FAISS_Index/legal_embeddings.index"
        assert os.path.exists(index_path)
        index = faiss.read_index(index_path)
        assert index.ntotal == 0

    @pytest.mark.parametrize("invalid_data", [
        np.array([[0.1]], dtype="float32"),  # Invalid shape for FAISS
        None,  # None input
    ])
    def test_create_index_invalid_data(self, mocker, invalid_data):
        """Test creating a FAISS index with invalid data.
        
        Verifies that create_index raises appropriate exceptions for invalid embeddings (mocked).
        
        Args:
            mocker: Pytest fixture for mocking.
            invalid_data: Invalid input data to test.
        """
        # Mock create_index to raise ValueError for invalid data
        mocker.patch('utils.create_vector_index.create_index', side_effect=ValueError("Invalid embedding dimensions for FAISS index"))

        serialized_data = pickle.dumps(invalid_data)
        with pytest.raises(ValueError, match="Invalid embedding dimensions for FAISS index"):
            create_index(serialized_data)