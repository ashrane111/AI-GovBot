import pytest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from main.retriever import Retriever

@pytest.fixture
def mock_config():
    with patch('main.retriever.config_loader') as mock_config:
        mock_config.get.side_effect = lambda key, default=None: {
            "paths.index_dir": "/mock/index/path",
            "retriever_args.n_docs": 3
        }.get(key, default)
        yield mock_config

@pytest.fixture
def mock_embeddings():
    with patch('main.retriever.SentenceTransformerEmbeddings') as MockEmbeddings:
        mock_embeddings_instance = MagicMock()
        MockEmbeddings.return_value = mock_embeddings_instance
        yield mock_embeddings_instance

@pytest.fixture
def mock_faiss():
    with patch('main.retriever.FAISS') as MockFAISS:
        # Create mock FAISS instance
        mock_vector_store = MagicMock()
        MockFAISS.load_local.return_value = mock_vector_store
        
        # Set up the mock return values for similarity search
        doc1 = MagicMock()
        doc1.page_content = "Document 1 content"
        doc2 = MagicMock()
        doc2.page_content = "Document 2 content"
        doc3 = MagicMock()
        doc3.page_content = "Document 3 content"
        
        mock_vector_store.similarity_search_with_score.return_value = [
            (doc1, 0.2),
            (doc2, 0.5),
            (doc3, 0.8)
        ]
        
        yield mock_vector_store

def test_retriever_init(mock_config, mock_embeddings, mock_faiss):
    """Test the initialization of the Retriever class."""
    retriever = Retriever()
    
    # Assert FAISS was initialized correctly
    from main.retriever import FAISS
    FAISS.load_local.assert_called_once_with(
        "/mock/index/path",
        mock_embeddings,
        allow_dangerous_deserialization=True
    )

def test_retrieve_method(mock_config, mock_embeddings, mock_faiss):
    """Test the retrieve method returns correct documents and scores."""
    retriever = Retriever()
    
    # Call the retrieve method
    query = "test query"
    documents, scores = retriever.retrieve(query)
    
    # Assert the similarity_search_with_score was called correctly
    mock_faiss.similarity_search_with_score.assert_called_once_with(query, k=3)
    
    # Assert the returned values are correct
    assert len(documents) == 3
    assert len(scores) == 3
    assert documents == ["Document 1 content", "Document 2 content", "Document 3 content"]
    assert scores == [0.2, 0.5, 0.8]

def test_retrieve_with_custom_k(mock_config, mock_embeddings, mock_faiss):
    """Test retrieval with a custom k value from config."""
    # Update the mock config to return a different n_docs value
    from main.retriever import config_loader
    config_loader.get.side_effect = lambda key, default=None: {
        "paths.index_dir": "/mock/index/path",
        "retriever_args.n_docs": 5  # Custom value
    }.get(key, default)
    
    retriever = Retriever()
    query = "test query"
    retriever.retrieve(query)
    
    # Verify k parameter was correctly passed
    mock_faiss.similarity_search_with_score.assert_called_once_with(query, k=5)

@patch('main.retriever.FAISS.load_local')
def test_retriever_handles_empty_results(mock_load_local, mock_config, mock_embeddings):
    """Test the retriever handles empty results correctly."""
    # Set up mock to return empty results
    mock_vector_store = MagicMock()
    mock_load_local.return_value = mock_vector_store
    mock_vector_store.similarity_search_with_score.return_value = []
    
    # Initialize retriever with the mocked vector store
    retriever = Retriever()
    
    # Call retrieve and check results
    documents, scores = retriever.retrieve("test query")
    
    assert documents == []
    assert scores == []

if __name__ == "__main__":
    pytest.main(["-v", __file__])