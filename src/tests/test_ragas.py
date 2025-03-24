# import pytest
# import os
# import sys
# import asyncio

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from main.rag_pipeline import RAGPipeline
# from rag_evaluator import RAGEvaluator

# @pytest.mark.asyncio
# async def test_ragas_evaluation():
#     # Initialize the pipeline
#     pipeline = RAGPipeline()

#     # Initialize the evaluator
#     evaluator = RAGEvaluator(pipeline)
#     results = await evaluator.evaluate_generation()

#     # Summarize results
#     results_dict = evaluator.summarize_results(results)

#     # Add assertions to validate the results
#     assert results_dict is not None
#     assert "avg_faithfulness" in results_dict
#     assert "avg_relevance" in results_dict
#     assert "avg_generation_time" in results_dict

#     # Example assertion for faithfulness score
#     assert results_dict["avg_faithfulness"] >= 0.5

#     # Example assertion for answer relevancy score
#     assert results_dict["avg_relevance"] >= 0.5

# if __name__ == "__main__":
#     pytest.main([__file__])