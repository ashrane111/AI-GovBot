import faiss
import pickle
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from .config_loader import config_loader  # Relative import

class EmbeddingsHandler:
    """Handles embeddings using FAISS and stores metadata locally."""

    def __init__(self):
        self.embedding_model = SentenceTransformer(config_loader.get("embedding.model"))
        self.faiss_index_path = config_loader.get("paths.faiss_index_path")
        self.meta_path = config_loader.get("paths.faiss_meta_path")

        os.makedirs(os.path.dirname(self.faiss_index_path), exist_ok=True)

        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        self.index = self._load_or_create_faiss_index()

    def _load_or_create_faiss_index(self):
        """Loads an existing FAISS index or creates a new one."""
        if os.path.exists(self.faiss_index_path):
            print("Loading existing FAISS index...")
            return faiss.read_index(self.faiss_index_path)
        else:
            print("Creating new FAISS index...")
            return faiss.IndexFlatL2(self.dimension)

    def upsert_embeddings(self, data):
        """Generates embeddings and stores them in FAISS."""
        batch_size = 100
        metadata = []

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            texts = [record["text"] for record in batch]
            embeddings = self.embedding_model.encode(texts)
            embeddings_np = np.array(embeddings).astype("float32")

            self.index.add(embeddings_np)
            metadata.extend(batch)

        faiss.write_index(self.index, self.faiss_index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(metadata, f)

        return self.index