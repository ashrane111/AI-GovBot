import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys
import re

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from main.rag_pipeline import RAGPipeline

@pytest.fixture
def mock_retriever():
    with patch('main.rag_pipeline.Retriever') as MockRetriever:
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = (
            ["Document 1 content", "Document 2 content with\nmultiple\nlines", "Document 3 content"],
            [0.1, 0.5, 1.5]  # First two below threshold, last one above
        )
        MockRetriever.return_value = mock_retriever_instance
        yield mock_retriever_instance

@pytest.fixture
def mock_generator():
    with patch('main.rag_pipeline.Generator') as MockGenerator:
        mock_generator_instance = MagicMock()
        mock_generator_instance.generate = AsyncMock(return_value={
            "content": "Generated response",
            "messages": [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "User query"},
                {"role": "assistant", "content": "Generated response"}
            ]
        })
        MockGenerator.return_value = mock_generator_instance
        yield mock_generator_instance

@pytest.fixture
def mock_mlflow_tracker():
    with patch('main.rag_pipeline.MLFlowTracker') as MockTracker:
        mock_tracker_instance = MagicMock()
        MockTracker.return_value = mock_tracker_instance
        yield mock_tracker_instance

@pytest.fixture
def mock_prompt_gen():
    with patch('main.rag_pipeline.PromptGen') as MockPromptGen:
        mock_prompter_instance = MagicMock()
        # Mock generate_user_prompt to return a predictable result
        mock_prompter_instance.generate_user_prompt.return_value = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Query: test query\nContext: filtered context"}
        ]
        # Mock remove_system_prompt
        mock_prompter_instance.remove_system_prompt.return_value = [
            {"role": "user", "content": "Query: test query"},
            {"role": "assistant", "content": "Generated response"}
        ]
        MockPromptGen.return_value = mock_prompter_instance
        yield mock_prompter_instance

@pytest.fixture
def mock_config():
    with patch('main.rag_pipeline.config_loader') as mock_config:
        mock_config.get.return_value = 1.2  # Default threshold
        yield mock_config

@pytest.mark.asyncio
async def test_rag_pipeline_initialization(mock_retriever, mock_generator, mock_mlflow_tracker, mock_prompt_gen, mock_config):
    """Test that RAGPipeline initializes correctly."""
    pipeline = RAGPipeline()
    
    # Check that components were initialized
    assert pipeline.retriever == mock_retriever
    assert pipeline.generator == mock_generator
    assert pipeline.tracker == mock_mlflow_tracker
    assert pipeline.prompter == mock_prompt_gen
    
    # Check that config value was loaded
    assert pipeline.SCORE_THRESHOLD == 1.2

@pytest.mark.asyncio
async def test_run_successful(mock_retriever, mock_generator, mock_mlflow_tracker, mock_prompt_gen, mock_config):
    """Test the run method with normal operation."""
    pipeline = RAGPipeline()
    
    # Create test query
    query_messages = [{"role": "user", "content": "test query"}]
    
    # Run the pipeline
    result, doc_ids = await pipeline.run(query_messages)
    
    # Check that retriever was called
    mock_retriever.retrieve.assert_called_once_with("test query")
    
    # Check that generator was called with prompted messages
    mock_generator.generate.assert_awaited_once()
    
    # Check that metrics were logged
    mock_mlflow_tracker.log_metrics.assert_called_once()
    
    # Check the returned result
    assert result["content"] == "Generated response"
    assert len(result["messages"]) == 2
    
    # Check document IDs
    assert len(doc_ids) == 3
    
@pytest.mark.asyncio
async def test_run_with_empty_docs(mock_retriever, mock_generator, mock_mlflow_tracker, mock_prompt_gen, mock_config):
    """Test the run method with empty retrieved documents."""
    # Override mock retriever to return empty results
    mock_retriever.retrieve.return_value = ([], [])
    
    pipeline = RAGPipeline()
    query_messages = [{"role": "user", "content": "test query"}]
    
    # Run the pipeline
    result, doc_ids = await pipeline.run(query_messages)
    
    # Context should be empty but pipeline should still run
    mock_prompt_gen.generate_user_prompt.assert_called_once()
    mock_generator.generate.assert_awaited_once()
    
    # No document IDs
    assert doc_ids == []

@pytest.mark.asyncio
async def test_run_with_generator_error(mock_retriever, mock_generator, mock_mlflow_tracker, mock_prompt_gen, mock_config):
    """Test the run method when generator raises an exception."""
    # Make the generator raise an exception
    mock_generator.generate.side_effect = Exception("Test error")
    
    # Also provide a fallback return value for when the exception is caught
    mock_generator.generate.return_value = {
        "content": "Fallback: Unable to generate response.",
        "messages": [{"role": "assistant", "content": "Fallback: Unable to generate response."}]
    }
    
    pipeline = RAGPipeline()
    query_messages = [{"role": "user", "content": "test query"}]
    
    # Run the pipeline
    result, doc_ids = await pipeline.run(query_messages)
    
    # Generator should still be called
    mock_generator.generate.assert_awaited_once()
    
    # Metrics should still be logged
    mock_mlflow_tracker.log_metrics.assert_called_once()

def test_generate_context(mock_retriever, mock_generator, mock_mlflow_tracker, mock_prompt_gen, mock_config):
    """Test the __generate_context private method."""
    pipeline = RAGPipeline()
    
    # Test documents and scores
    docs = ["Document 1", "Document 2", "Document 3"]
    scores = [0.1, 1.5, 0.8]  # Second doc should be filtered out
    
    # Call the private method directly using name mangling
    context = pipeline._RAGPipeline__generate_context(docs, scores)
    
    # Check that filtered docs contain ranks and correct docs
    assert "Rank 1: Document 1" in context
    assert "Rank 3: Document 3" in context
    assert "Document 2" not in context

def test_get_context_doc(mock_retriever, mock_generator, mock_mlflow_tracker, mock_prompt_gen, mock_config):
    """Test the __get_context_doc private method."""
    pipeline = RAGPipeline()
    
    # Test with messy document
    messy_doc = """
    This is a document
    
    with multiple

    empty lines   
    and extra spaces    
    """
    
    # Call the private method directly using name mangling
    cleaned_doc = pipeline._RAGPipeline__get_context_doc(messy_doc)
    
    # Should remove empty lines and extra spaces
    assert cleaned_doc == "This is a document\nwith multiple\nempty lines\nand extra spaces"

def test_get_context_doc_with_already_clean_doc(mock_retriever, mock_generator, mock_mlflow_tracker, mock_prompt_gen, mock_config):
    """Test __get_context_doc with an already clean document."""
    pipeline = RAGPipeline()
    
    clean_doc = "This is already clean."
    cleaned_doc = pipeline._RAGPipeline__get_context_doc(clean_doc)
    
    assert cleaned_doc == clean_doc

def test_generate_context_all_docs_filtered(mock_retriever, mock_generator, mock_mlflow_tracker, mock_prompt_gen, mock_config):
    """Test __generate_context when all docs are filtered out."""
    pipeline = RAGPipeline()
    
    # All scores above threshold
    docs = ["Document 1", "Document 2"]
    scores = [1.5, 2.0]
    
    context = pipeline._RAGPipeline__generate_context(docs, scores)
    
    # Should be empty
    assert context == ""

@pytest.mark.asyncio
async def test_run_with_conversation_history(mock_retriever, mock_generator, mock_mlflow_tracker, mock_prompt_gen, mock_config):
    """Test the run method with a conversation history."""
    pipeline = RAGPipeline()
    
    # Create a conversation history
    query_messages = [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "followup question"}
    ]
    
    # Run the pipeline
    await pipeline.run(query_messages)
    
    # Check that entire conversation history was passed to prompter
    mock_prompt_gen.generate_user_prompt.assert_called_once()
    args, _ = mock_prompt_gen.generate_user_prompt.call_args
    assert len(args[0]) == 3  # Should have all 3 messages
    
    # Check that retriever was called with only the last query
    mock_retriever.retrieve.assert_called_once_with("followup question")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])