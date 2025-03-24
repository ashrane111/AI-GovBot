import pytest
from pathlib import Path
import sys

# Add src/ to sys.path for imports
root_path = Path(__file__).parent.parent.absolute()
sys.path.append(str(root_path))

from main.retriever import Retriever

# Use 1.2 to match RAGPipeline's default, or 1.0 for original test intent
RETRIEVAL_DISTANCE_THRESHOLD = 1.2

@pytest.fixture
def retriever():
    """Fixture to initialize the Retriever."""
    return Retriever()

def test_retrieval_scores(retriever):
    """Test retrieval scores for predefined queries to ensure relevance."""
    test_queries = {
        "ai_laws": "What are the legal implications of AI in governance?",
        "data_privacy": "How does data privacy affect AI governance?",
        "bias_regulation": "What regulations address AI bias in law?"
    }
    failed_scenarios = []
    for scenario, query in test_queries.items():
        retrieved_docs, retrieval_scores = retriever.retrieve(query)
        for i, score in enumerate(retrieval_scores, 1):
            if score > RETRIEVAL_DISTANCE_THRESHOLD:
                failed_scenarios.append(
                    f"{scenario} - Document {i}: distance score {score:.3f} exceeds threshold {RETRIEVAL_DISTANCE_THRESHOLD}"
                )
    assert not failed_scenarios, (
        f"The following scenarios had retrieval scores exceeding the distance threshold {RETRIEVAL_DISTANCE_THRESHOLD}:\n"
        + "\n".join(failed_scenarios)
    )

if __name__ == "__main__":
    pytest.main([__file__])