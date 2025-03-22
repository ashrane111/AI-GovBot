from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings

class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_name="sentence-transformers/all-mpnet-base-v2"):
        self.model = SentenceTransformer(model_name)
        
    def embed_documents(self, texts):
        return self.model.encode(texts)
    
    def embed_query(self, text):
        return self.model.encode([text])[0]