import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import os
import json
from rag_evaluator import RAGEvaluator
from datasets import Dataset

# Sample test data for mocking
SAMPLE_TEST_DATA = [
    {
        "question": "What is AI?",
        "expected_output": "AI is artificial intelligence."
    }
]

@pytest.fixture
def mock_pipeline():
    """Fixture to mock the RAGPipeline."""
    pipeline = Mock()
    pipeline.run = AsyncMock(return_value={"content": ("AI is artificial intelligence.", "doc1")})
    pipeline.tracker = Mock()
    pipeline.tracker.log_metrics = Mock()
    return pipeline

@pytest.fixture
def evaluator(mock_pipeline):
    """Fixture to initialize RAGEvaluator with a mocked pipeline."""
    return RAGEvaluator(mock_pipeline)

@pytest.fixture
def temp_test_file(tmp_path):
    """Fixture to create a temporary rag_test.json file."""
    test_data_path = tmp_path / "data"
    test_data_path.mkdir()
    file_path = test_data_path / "rag_test.json"
    with open(file_path, 'w') as f:
        json.dump(SAMPLE_TEST_DATA, f)
    return file_path

def test_init(evaluator, mock_pipeline):
    """Test the initialization of RAGEvaluator."""
    assert evaluator.pipeline == mock_pipeline

@patch("os.path.dirname", return_value="/fake/path")
@patch("os.path.join", side_effect=lambda *args: "/".join(args))
def test_load_test_data(mock_join, mock_dirname, evaluator, temp_test_file):
    """Test loading test data from rag_test.json."""
    with patch("rag_evaluator.os.path.dirname", return_value=str(temp_test_file.parent.parent)):
        test_data = evaluator.load_test_data()
        assert len(test_data) == 1  # Should load only 1 entry as per code
        assert test_data[0]["question"] == "What is AI?"
        assert test_data[0]["expected_output"] == "AI is artificial intelligence."

@pytest.mark.asyncio
async def test_evaluate_generation_success(evaluator, mock_pipeline):
    """Test evaluate_generation with a successful run."""
    # Mock test data loading
    with patch.object(evaluator, "load_test_data", return_value=SAMPLE_TEST_DATA):
        # Mock ragas evaluation
        mock_ragas_result = {
            "faithfulness": [0.95],
            "answer_relevancy": [0.90]
        }
        with patch("rag_evaluator.evaluate", return_value=mock_ragas_result):
            results = await evaluator.evaluate_generation()
            
            # Assertions
            assert len(results) == 1
            result = results[0]
            assert result["query"] == "What is AI?"
            assert result["generated_response"] == "AI is artificial intelligence."
            assert result["ground_truth"] == "AI is artificial intelligence."
            assert result["faithfulness"] == 0.95
            assert result["relevance"] == 0.90
            assert "generation_time" in result
            assert result["generation_time"] > 0

@pytest.mark.asyncio
async def test_evaluate_generation_ragas_failure(evaluator, mock_pipeline):
    """Test evaluate_generation when ragas evaluation fails."""
    with patch.object(evaluator, "load_test_data", return_value=SAMPLE_TEST_DATA):
        # Simulate ragas evaluation failure
        with patch("rag_evaluator.evaluate", side_effect=Exception("RAGAS error")):
            results = await evaluator.evaluate_generation()
            
            # Assertions
            assert len(results) == 1
            result = results[0]
            assert result["faithfulness"] == 0.0
            assert result["relevance"] == 0.0
            mock_pipeline.tracker.log_metrics.assert_called()

def test_summarize_results(evaluator):
    """Test summarize_results method."""
    sample_results = [
        {
            "query": "What is AI?",
            "generated_response": "AI is artificial intelligence.",
            "ground_truth": "AI is artificial intelligence.",
            "faithfulness": 0.95,
            "relevance": 0.90,
            "generation_time": 1.5
        }
    ]
    
    with patch("rag_evaluator.mlflow.log_metric") as mock_log_metric:
        results_dict = evaluator.summarize_results(sample_results)
        
        # Assertions
        assert results_dict["avg_faithfulness"] == 0.95
        assert results_dict["avg_relevance"] == 0.90
        assert results_dict["avg_generation_time"] == 1.5
        
        # Check MLflow logging
        mock_log_metric.assert_any_call("avg_faithfulness", 0.95)
        mock_log_metric.assert_any_call("avg_relevance", 0.90)
        mock_log_metric.assert_any_call("avg_generation_time", 1.5)

@pytest.mark.asyncio
async def test_generate_results_integration():
    """Integration test for the generate_results function."""
    from main.rag_pipeline import RAGPipeline
    
    # Mock RAGPipeline and its run method
    with patch("main.rag_pipeline.RAGPipeline") as MockPipeline:
        mock_pipeline_instance = MockPipeline.return_value
        mock_pipeline_instance.run = AsyncMock(return_value={"content": ("AI is artificial intelligence.", "doc1")})
        mock_pipeline_instance.tracker = Mock()
        mock_pipeline_instance.tracker.log_metrics = Mock()
        
        # Mock test data and ragas evaluation
        with patch("rag_evaluator.RAGEvaluator.load_test_data", return_value=SAMPLE_TEST_DATA):
            with patch("rag_evaluator.evaluate", return_value={"faithfulness": [0.95], "answer_relevancy": [0.90]}):
                from test_ragas import generate_results  # Replace 'your_script' with actual script name
                results_dict = await generate_results()
                
                # Assertions
                assert results_dict["avg_faithfulness"] == 0.95
                assert results_dict["avg_relevance"] == 0.90
                assert results_dict["avg_generation_time"] > 0

if __name__ == "__main__":
    pytest.main()