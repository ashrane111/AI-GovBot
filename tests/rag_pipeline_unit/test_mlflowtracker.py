import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from main.mlflow_tracker import MLFlowTracker

@pytest.fixture
def mock_mlflow():
    """Mock the mlflow module."""
    with patch('main.mlflow_tracker.mlflow') as mock_mlflow:
        # Create mock for context manager
        mock_run = MagicMock()
        mock_mlflow.start_run.return_value.__enter__.return_value = mock_run
        mock_mlflow.start_run.return_value.__exit__.return_value = None
        
        yield mock_mlflow

@pytest.fixture
def mock_config():
    """Mock the config loader."""
    with patch('main.mlflow_tracker.config_loader') as mock_config:
        mock_config.get.side_effect = lambda key, default=None: {
            "mlflow.tracking_uri": "http://localhost:5000",
            "mlflow.experiment_name": "test_experiment"
        }.get(key, default)
        
        yield mock_config

def test_mlflow_tracker_initialization(mock_mlflow, mock_config):
    """Test that MLFlowTracker initializes correctly."""
    tracker = MLFlowTracker()
    
    # Check that MLflow was set up correctly
    mock_mlflow.set_tracking_uri.assert_called_once_with("http://localhost:5000")
    mock_mlflow.set_experiment.assert_called_once_with("test_experiment")

def test_log_metrics(mock_mlflow, mock_config):
    """Test the log_metrics method."""
    # Set up test data
    query = "What is the AI law in California?"
    response = {"content": "California has several AI laws including..."}
    retrieved_docs = ["Document 1 content", "Document 2 content"]
    scores = [0.2, 0.5]
    retrieval_time = 0.1
    generation_time = 0.5
    
    # Create tracker and call log_metrics
    tracker = MLFlowTracker()
    tracker.log_metrics(query, response, retrieved_docs, scores, retrieval_time, generation_time)
    
    # Check that start_run was called
    mock_mlflow.start_run.assert_called_once()
    
    # Check that log_param and log_metric were called with correct values
    mock_mlflow.log_param.assert_any_call("query", query)
    mock_mlflow.log_param.assert_any_call("retrieved_documents", 2)
    mock_mlflow.log_metric.assert_any_call("response_length", len(response['content']))
    mock_mlflow.log_metric.assert_any_call("retrieval_time", retrieval_time)
    mock_mlflow.log_metric.assert_any_call("generation_time", generation_time)
    
    # Check document logging
    mock_mlflow.log_param.assert_any_call("retrieved_doc_0", "Document 1 content")
    mock_mlflow.log_param.assert_any_call("retrieved_doc_1", "Document 2 content")
    mock_mlflow.log_metric.assert_any_call("retrieval_score_0", 0.2)
    mock_mlflow.log_metric.assert_any_call("retrieval_score_1", 0.5)

def test_log_metrics_with_long_document(mock_mlflow, mock_config):
    """Test that log_metrics correctly truncates long documents."""
    # Set up test data with long document
    query = "Test query"
    response = {"content": "Test response"}
    long_doc = "A" * 200  # Document with 200 characters
    retrieved_docs = [long_doc]
    scores = [0.3]
    retrieval_time = 0.1
    generation_time = 0.2
    
    # Create tracker and call log_metrics
    tracker = MLFlowTracker()
    tracker.log_metrics(query, response, retrieved_docs, scores, retrieval_time, generation_time)
    
    # Check that the document was truncated to 100 characters
    truncated_doc = long_doc[:100]
    mock_mlflow.log_param.assert_any_call("retrieved_doc_0", truncated_doc)

def test_log_metrics_with_empty_inputs(mock_mlflow, mock_config):
    """Test log_metrics with empty inputs."""
    # Set up test data with empty inputs
    query = ""
    response = {"content": ""}
    retrieved_docs = []
    scores = []
    retrieval_time = 0.0
    generation_time = 0.0
    
    # Create tracker and call log_metrics
    tracker = MLFlowTracker()
    tracker.log_metrics(query, response, retrieved_docs, scores, retrieval_time, generation_time)
    
    # Check that log_param and log_metric were called with correct values
    mock_mlflow.log_param.assert_any_call("query", "")
    mock_mlflow.log_param.assert_any_call("retrieved_documents", 0)
    mock_mlflow.log_metric.assert_any_call("response_length", 0)
    mock_mlflow.log_metric.assert_any_call("retrieval_time", 0.0)
    mock_mlflow.log_metric.assert_any_call("generation_time", 0.0)
    
    # Ensure no document-specific logs were made
    for call in mock_mlflow.log_param.mock_calls:
        assert not call[1][0].startswith("retrieved_doc_")
    
    for call in mock_mlflow.log_metric.mock_calls:
        assert not call[1][0].startswith("retrieval_score_")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])