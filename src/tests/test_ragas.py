from rag_evaluator import RAGEvaluator
import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main.rag_pipeline import RAGPipeline
async def generate_results():
    # Initialize the pipeline
    pipeline = RAGPipeline()

    # Initialize the evaluator
    evaluator = RAGEvaluator(pipeline)
    results = await evaluator.evaluate_generation()

    # Summarize results
    results_dict = evaluator.summarize_results(results)

    return results_dict

# Example usage
if __name__ == "__main__":
    # Initialize the pipeline
    # pipeline = RAGPipeline()

    # # Initialize the evaluator
    # evaluator = RAGEvaluator(pipeline)
    # results = asyncio.run(evaluator.evaluate_generation())

    # # Summarize results
    # evaluator.summarize_results(results)
    asyncio.run(generate_results())