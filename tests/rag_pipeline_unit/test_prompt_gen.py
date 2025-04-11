import pytest
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from main.prompt_gen import PromptGen

def test_prompt_gen_initialization():
    """Test that PromptGen initializes with the correct system prompt."""
    prompter = PromptGen()
    
    # Check that the system prompt is correctly initialized
    assert prompter.system_prompt["role"] == "system"
    assert "H.A.R.V.E.Y" in prompter.system_prompt["content"]
    assert "Holistic AI for Regulatory Verification and Ethical Yield" in prompter.system_prompt["content"]

def test_generate_user_prompt_basic():
    """Test the basic functionality of generate_user_prompt."""
    prompter = PromptGen()
    messages = [{"role": "user", "content": "What is the AI Act?"}]
    context = "The AI Act is a European regulation..."
    
    result = prompter.generate_user_prompt(messages, context)
    
    # Check that system prompt was prepended
    assert len(result) == 2
    assert result[0]["role"] == "system"
    assert "H.A.R.V.E.Y" in result[0]["content"]
    
    # Check that user message was formatted correctly
    assert result[1]["role"] == "user"
    assert "Query: What is the AI Act?" in result[1]["content"]
    assert "Context: The AI Act is a European regulation..." in result[1]["content"]

def test_generate_user_prompt_with_conversation_history():
    """Test generate_user_prompt with a conversation history."""
    prompter = PromptGen()
    messages = [
        {"role": "user", "content": "Tell me about AI laws in California."},
        {"role": "assistant", "content": "California has several AI-related laws..."},
        {"role": "user", "content": "What about GDPR?"}
    ]
    context = "GDPR is a data protection regulation..."
    
    result = prompter.generate_user_prompt(messages, context)
    
    # Check that system prompt was prepended
    assert len(result) == 4  # system + 3 original messages
    assert result[0]["role"] == "system"
    
    # Check that only the last user message was formatted
    assert result[1]["role"] == "user"
    assert result[1]["content"] == "Tell me about AI laws in California."
    assert result[2]["role"] == "assistant"
    assert result[2]["content"] == "California has several AI-related laws..."
    assert result[3]["role"] == "user"
    assert "Query: What about GDPR?" in result[3]["content"]
    assert "Context: GDPR is a data protection regulation..." in result[3]["content"]

def test_generate_user_prompt_with_empty_context():
    """Test generate_user_prompt with empty context."""
    prompter = PromptGen()
    messages = [{"role": "user", "content": "What is the AI Act?"}]
    context = ""
    
    result = prompter.generate_user_prompt(messages, context)
    
    # Check that user message still contains query and empty context
    assert result[1]["role"] == "user"
    assert "Query: What is the AI Act?" in result[1]["content"]
    assert "Context: " in result[1]["content"]

def test_remove_system_prompt():
    """Test remove_system_prompt with a system prompt present."""
    prompter = PromptGen()
    messages = [
        {"role": "system", "content": "System instruction"},
        {"role": "user", "content": "User question"},
        {"role": "assistant", "content": "Assistant response"}
    ]
    
    result = prompter.remove_system_prompt(messages)
    
    # Check that system prompt was removed
    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "assistant"

def test_remove_system_prompt_no_system_prompt():
    """Test remove_system_prompt when no system prompt is present."""
    prompter = PromptGen()
    messages = [
        {"role": "user", "content": "User question"},
        {"role": "assistant", "content": "Assistant response"}
    ]
    
    result = prompter.remove_system_prompt(messages)
    
    # Should still return the messages starting from index 1 
    # (which doesn't exist, so empty list)
    assert len(result) == 1
    assert result[0]["role"] == "assistant"

def test_remove_system_prompt_empty_messages():
    """Test remove_system_prompt with empty messages."""
    prompter = PromptGen()
    messages = []
    
    result = prompter.remove_system_prompt(messages)
    
    # Should return an empty list
    assert len(result) == 0

def test_full_prompt_flow():
    """Test the full flow: generate prompt and then remove system prompt."""
    prompter = PromptGen()
    messages = [{"role": "user", "content": "What is GDPR?"}]
    context = "GDPR is a European regulation..."
    
    # Generate prompt with system prompt
    with_system = prompter.generate_user_prompt(messages, context)
    assert len(with_system) == 2
    assert with_system[0]["role"] == "system"
    
    # Remove system prompt
    without_system = prompter.remove_system_prompt(with_system)
    assert len(without_system) == 1
    assert without_system[0]["role"] == "user"
    assert "Query: What is GDPR?" in without_system[0]["content"]

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])