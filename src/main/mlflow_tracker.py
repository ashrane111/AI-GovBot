import mlflow
from .config_loader import config_loader  # Relative import

class MLFlowTracker:
    """Tracks RAG Pipeline metrics using MLflow."""

    def __init__(self):
        """Initialize MLflow tracking."""
        mlflow.set_tracking_uri(config_loader.get("mlflow.tracking_uri"))
        mlflow.set_experiment(config_loader.get("mlflow.experiment_name"))

    def log_metrics(self, query, response, retrieved_docs, scores):
        """Logs query, response length, and retrieval performance."""
        with mlflow.start_run():
            mlflow.log_param("query", query)
            mlflow.log_param("retrieved_documents", len(retrieved_docs))
            mlflow.log_metric("response_length", len(response['content']))
            
            for idx, (doc, score) in enumerate(zip(retrieved_docs, scores)):
                mlflow.log_param(f"retrieved_doc_{idx}", doc)
                mlflow.log_metric(f"retrieval_score_{idx}", score)

            print("MLflow: Query & response logged successfully.")