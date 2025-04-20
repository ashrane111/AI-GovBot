import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from main.generator import Generator

@pytest.fixture
def mock_llm_client():
    """Mock the LLM client factory and return a mock client."""
    with patch('main.generator.create_llm_client') as mock_create_client:
        mock_client = AsyncMock()
        mock_create_client.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_config():
    """Mock the config loader."""
    with patch('main.generator.config_loader') as mock_config:
        mock_config.get.return_value = "mock_provider"
        yield mock_config

@pytest.mark.asyncio
async def test_generator_initialization(mock_llm_client, mock_config):
    """Test that Generator initializes correctly."""
    generator = Generator()
    
    # Check that create_llm_client was called with the right provider
    from main.generator import create_llm_client
    create_llm_client.assert_called_once_with("mock_provider")
    
    # Check that the client was set correctly
    assert generator.client == mock_llm_client

@pytest.mark.asyncio
async def test_generate_successful_response(mock_llm_client, mock_config):
    """Test successful response generation."""
    # Set up the mock client to return a test response
    mock_llm_client.generate_completion.return_value = "This is a test response"
    
    # Create a generator and test query
    generator = Generator()
    query_message = [{"role": "user", "content": "Test query"}]
    
    # Call the generate method
    result = await generator.generate(query_message)
    
    # Check that the client was called correctly
    mock_llm_client.generate_completion.assert_called_once_with(query_message)
    
    # Check the returned result
    assert result["content"] == "This is a test response"
    assert len(result["messages"]) == 2
    assert result["messages"][0]["role"] == "user"
    assert result["messages"][1]["role"] == "assistant"
    assert result["messages"][1]["content"] == "This is a test response"

@pytest.mark.asyncio
async def test_generate_handles_error(mock_llm_client, mock_config):
    """Test error handling in the generate method."""
    # Set up the mock client to raise an exception
    mock_llm_client.generate_completion.side_effect = Exception("Test error")
    
    # Create a generator and test query
    generator = Generator()
    query_message = [{"role": "user", "content": "Test query"}]
    
    # Call the generate method
    result = await generator.generate(query_message)
    
    # Check that the client was called
    mock_llm_client.generate_completion.assert_called_once()
    
    # Check that a fallback response was returned
    assert "Fallback" in result["content"]
    assert len(result["messages"]) == 2
    assert result["messages"][1]["role"] == "assistant"
    assert "Fallback" in result["messages"][1]["content"]

@pytest.mark.asyncio
async def test_generate_preserves_message_history(mock_llm_client, mock_config):
    """Test that generate preserves existing message history."""
    # Set up the mock client to return a test response
    mock_llm_client.generate_completion.return_value = "This is a test response"
    
    # Create a generator and test query with history
    generator = Generator()
    query_message = [
        {"role": "system", "content": "You are an AI assistant"},
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "First answer"},
        {"role": "user", "content": "Follow-up question"}
    ]
    
    # Call the generate method
    result = await generator.generate(query_message)
    
    # Check that the message history was preserved
    assert len(result["messages"]) == 5  # Original 4 + new assistant message
    assert result["messages"][0]["role"] == "system"
    assert result["messages"][1]["role"] == "user"
    assert result["messages"][2]["role"] == "assistant"
    assert result["messages"][3]["role"] == "user"
    assert result["messages"][4]["role"] == "assistant"
    assert result["messages"][4]["content"] == "This is a test response"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])