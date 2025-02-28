import pytest
import numpy as np
import pickle
import faiss
from utils.create_vector_index import create_index

def test_create_index_normal():
    embeddings = np.array([[0.1, 0.2], [0.3, 0.4]], dtype="float32")
    serialized_embeddings = pickle.dumps(embeddings)
    create_index(serialized_embeddings)
    index_path = "FAISS_Index/legal_embeddings.index"
    assert os.path.exists(index_path)
    index = faiss.read_index(index_path)
    assert index.ntotal == 2
    assert index.d == 2  # Adjust to actual dimension (e.g., 768 for embeddings)

def test_create_index_empty_embeddings():
    embeddings = np.array([], dtype="float32")
    serialized_embeddings = pickle.dumps(embeddings)
    create_index(serialized_embeddings)
    index_path = "FAISS_Index/legal_embeddings.index"
    assert os.path.exists(index_path)
    index = faiss.read_index(index_path)
    assert index.ntotal == 0