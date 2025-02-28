import pytest
import pandas as pd
import pickle
import numpy as np
from utils.embeddings_gen import generate_embeddings
from unittest.mock import patch

@pytest.fixture
def mock_sentence_transformer():
    with patch("sentence_transformers.SentenceTransformer") as mock_st:
        mock_model = mock_st.return_value
        mock_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]], dtype="float32")  # Placeholder for 768 dimensions
        yield mock_model

def test_generate_embeddings_normal(mock_sentence_transformer, tmp_path):
    df = pd.DataFrame({"cleaned_text": ["hello world", "test text"]})
    serialized_df = pickle.dumps(df)
    result = generate_embeddings(serialized_df)
    embeddings = pickle.loads(result)
    assert embeddings.shape == (2, 768)  # Adjust to actual dimension (e.g., 768 for multi-qa-mpnet-base-dot-v1)
    assert os.path.exists("embeddings/embeddings.pkl")

def test_generate_embeddings_empty_df(mock_sentence_transformer):
    df = pd.DataFrame({"cleaned_text": []})
    serialized_df = pickle.dumps(df)
    result = generate_embeddings(serialized_df)
    embeddings = pickle.loads(result)
    assert len(embeddings) == 0