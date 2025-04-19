import os
import json
import time
import mlflow
from dotenv import load_dotenv
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset  # Import Dataset to convert dict to Dataset


load_dotenv()


class RAGEvaluator:
    def __init__(self, pipeline):
        """
        Initialize the evaluator with the RAG pipeline.
        
        Args:
            pipeline (RAGPipeline): Your RAG pipeline instance.
        """
        self.pipeline = pipeline

    def load_test_data(self):
        """
        Load the test dataset from the specified JSON file and limit to the first 1 entry.
        
        Returns:
            list: Test data entries (first 1).
        """
        test_data_path = os.path.join(os.path.dirname(__file__), "data", "rag_test.json")
        with open(test_data_path, 'r') as f:
            test_data = json.load(f)
        
        # Limit to first 1 entry as per your setup
        return test_data


    async def evaluate_generation(self):
        """
        Evaluate the generation quality of the RAG pipeline on the first 1 test entry.
        
        Returns:
            list: Evaluation results for each query.
        """
        # Load the first 1 test data entry
        test_data = self.load_test_data()
        results = []

        for item in test_data:
            query = item["question"]
            ground_truth = item["expected_output"]
            query_message = [{"role": "user", "content": query}]

            # Run the pipeline (await the async function)
            start_time = time.time()
            answer, doc_id = await self.pipeline.run(query_message)  # Remove try-except to see the full error
            generated_response = answer["content"]
            generation_time = time.time() - start_time

            # Log basic metrics with MLFlowTracker
            self.pipeline.tracker.log_metrics(
                query=query,
                response=answer,
                retrieved_docs=[],
                scores=[],
                retrieval_time=0,
                generation_time=generation_time
            )

            # RAGAS evaluation (faithfulness and relevancy)
            ragas_dataset_dict = {
                "question": [query],
                "contexts": [[ground_truth]],
                "answer": [generated_response]
            }
            try:
                print(f"Running RAGAS evaluation for query: {query}")
                # Convert the dictionary to a Dataset object
                ragas_dataset = Dataset.from_dict(ragas_dataset_dict)
                ragas_result = evaluate(ragas_dataset, metrics=[faithfulness, answer_relevancy])
                print(f"RAGAS result: {ragas_result}")
            except Exception as e:
                print(f"RAGAS evaluation failed for query '{query}': {e}")
                ragas_result = {"faithfulness": 0.0, "answer_relevancy": 0.0}

            ragas_faithful = float(ragas_result["faithfulness"][0])
            ragas_answer_relevancy = float(ragas_result["answer_relevancy"][0])

            # Compile results
            result = {
                "query": query,
                "generated_response": generated_response,
                "ground_truth": ground_truth,
                "faithfulness": ragas_faithful,
                "relevance": ragas_answer_relevancy,
                "generation_time": generation_time
            }
            results.append(result)

            time.sleep(2)  # Add delay to avoid rate limits

        return results

    def summarize_results(self, results):
        """
        Summarize the evaluation results with average scores.
        
        Args:
            results (list): List of evaluation results.
        """

        # Convert generator to list for averaging
        faithfulness_scores = [float(r["faithfulness"]) for r in results]
        relevance_scores = [float(r["relevance"]) for r in results]
        generation_times = [float(r["generation_time"]) for r in results]

        avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        avg_generation_time = sum(generation_times) / len(generation_times)

        print("\n=== Evaluation Summary (First 1 Entry) ===")
        print(f"Average Faithfulness: {avg_faithfulness:.2f}")
        print(f"Average Relevance: {avg_relevance:.2f}")
        print(f"Average Generation Time: {avg_generation_time:.2f} seconds")

        # Log averages to MLflow
        mlflow.log_metric("avg_faithfulness", avg_faithfulness)
        mlflow.log_metric("avg_relevance", avg_relevance)
        mlflow.log_metric("avg_generation_time", avg_generation_time)

        results_dict = {
            "avg_faithfulness": avg_faithfulness,
            "avg_relevance": avg_relevance,
            "avg_generation_time": avg_generation_time
        }

        return results_dict

