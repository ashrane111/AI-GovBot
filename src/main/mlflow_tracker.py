import mlflow
from main.config_loader import config_loader

class MLFlowTracker:
    def __init__(self):
        mlflow.set_tracking_uri(config_loader.get("mlflow.tracking_uri"))
        mlflow.set_experiment(config_loader.get("mlflow.experiment_name"))

    def log_metrics(self, query, response, retrieved_docs, scores, retrieval_time, generation_time):
        with mlflow.start_run():
            mlflow.log_param("query", query)
            mlflow.log_param("retrieved_documents", len(retrieved_docs))
            mlflow.log_metric("response_length", len(response['content']))
            mlflow.log_metric("retrieval_time", retrieval_time)
            mlflow.log_metric("generation_time", generation_time)
            for idx, (doc, score) in enumerate(zip(retrieved_docs, scores)):
                mlflow.log_param(f"retrieved_doc_{idx}", doc[:100])  # Limit to 100 chars
                mlflow.log_metric(f"retrieval_score_{idx}", score)