
# # tests/unit/test_rag_pipeline.py
# import pytest
# import unittest.mock as mock
# from unittest.mock import MagicMock, patch, AsyncMock
# import os
# import mlflow
# import asyncio
# import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

# from main.retriever import Retriever
# from main.generator import Generator
# from main.rag_pipeline import RAGPipeline
# from main.prompt_gen import PromptGen
# from main.mlflow_tracker import MLFlowTracker
# from main.config_loader import ConfigLoader

# @pytest.fixture
# def mock_config():
#     with patch('main.config_loader.ConfigLoader') as mock_config:
#         mock_config.get.side_effect = lambda key, default=None: {
#             "retriever_args.score_threshold": 1.2,
#             "retriever_args.n_docs": 2,
#             "paths.index_dir": "test_index",
#             "llm.client": "ollama_local"
#         }.get(key, default)
#         yield mock_config

# @pytest.fixture
# def mock_retriever():
#     retriever = mock.create_autospec(Retriever)
#     retriever.retrieve.return_value = (
#         ["doc1", "doc2"],  # Sample documents
#         [0.8, 1.5]         # Sample scores
#     )
#     return retriever

# @pytest.fixture
# def mock_generator():
#     generator = mock.create_autospec(Generator)
#     generator.generate = AsyncMock(return_value={
#         "content": "Test response",
#         "messages": [{"role": "assistant", "content": "Test response"}]
#     })
#     return generator

# @pytest.fixture
# def mock_mlflow():
#     with patch('main.mlflow_tracker.mlflow') as mock_mlflow:
#         yield mock_mlflow

# @pytest.mark.asyncio
# async def test_full_rag_pipeline(mock_config, mock_retriever, mock_generator, mock_mlflow):
#     # Arrange
#     pipeline = RAGPipeline()
#     pipeline.retriever = mock_retriever
#     pipeline.generator = mock_generator
#     test_query = [{"role": "user", "content": "Test query"}]
    
#     # Act
#     result = await pipeline.run(test_query)
    
#     # Assert
#     # Test Retriever interaction
#     mock_retriever.retrieve.assert_called_once_with("Test query")
    
#     # Test Generator interaction
#     mock_generator.generate.assert_awaited_once()
    
#     # Test response formatting
#     assert "content" in result
#     assert "messages" in result
#     assert len(result["messages"]) == 1
    
#     # Test MLflow logging
#     mock_mlflow.start_run.assert_called_once()
#     mock_mlflow.log_param.assert_any_call("query", "Test query")
#     mock_mlflow.log_metric.assert_any_call("response_length", 12)

# def test_retriever_component(mock_config):
#     # Arrange
#     with patch('langchain_community.vectorstores.FAISS.load_local') as mock_faiss:
#         mock_faiss.return_value = MagicMock()
#         retriever = Retriever()
        
#         # Act
#         docs, scores = retriever.retrieve("What is Rhode island protection act?")
        
#         # Assert
#         assert len(docs) == 3
#         assert len(scores) == 3
#         assert isinstance(scores[0], float)

# @pytest.mark.asyncio
# async def test_generator_component(mock_config):
#     # Arrange
#     generator = Generator()
#     generator.client = AsyncMock()
#     generator.client.generate_completion.return_value = "Test response"
#     test_messages = [{"role": "user", "content": "Test query"}]
    
#     # Act
#     result = await generator.generate(test_messages)
    
#     # Assert
#     assert "content" in result
#     assert result["content"] == "Test response"
#     assert len(result["messages"]) == 2
#     assert result["messages"][-1]["role"] == "assistant"

# def test_prompt_generation():
#     # Arrange
#     prompter = PromptGen()
#     test_messages = [{"role": "user", "content": "Test query"}]
    
#     # Act
#     prompted = prompter.generate_user_prompt(test_messages, "Test context")
#     cleaned = prompter.remove_system_prompt(prompted)
    
#     # Assert
#     assert len(prompted) == 2
#     assert "system" in prompted[0]["role"]
#     assert "context" in prompted[-1]["content"]
#     assert len(cleaned) == 1

# def test_mlflow_tracking(mock_mlflow):
#     # Arrange
#     tracker = MLFlowTracker()
#     test_response = {"content": "Test response"}
    
#     # Act
#     tracker.log_metrics(
#         query="Test query",
#         response=test_response,
#         retrieved_docs=["doc1", "doc2"],
#         scores=[0.8, 1.5],
#         retrieval_time=0.1,
#         generation_time=0.5
#     )
    
#     # Assert
#     mock_mlflow.log_param.assert_any_call("query", "Test query")
#     mock_mlflow.log_metric.assert_any_call("retrieval_time", 0.1)
#     mock_mlflow.log_param.assert_any_call("retrieved_doc_0", "doc1"[:100])

# @pytest.mark.asyncio
# async def test_error_handling_in_generator(mock_config):
#     # Arrange
#     generator = Generator()
#     generator.client = AsyncMock()
#     generator.client.generate_completion.side_effect = Exception("Test error")
#     test_messages = [{"role": "user", "content": "Test query"}]
    
#     # Act
#     result = await generator.generate(test_messages)
    
#     # Assert
#     assert "Fallback" in result["content"]
#     assert len(result["messages"]) == 2


# if __name__ == "_main_":
#     import sys
#     import pytest
#     pytest.main([__file__] + sys.argv[1:])
