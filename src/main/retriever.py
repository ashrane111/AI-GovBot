from langchain_community.vectorstores import FAISS
from .embeddings_model import SentenceTransformerEmbeddings

class Retriever:
    def __init__(self, index_path="src/index"):
        self.embeddings = SentenceTransformerEmbeddings()
        self.vector_store = FAISS.load_local(
            index_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})

    def retrieve(self, query):
        docs = self.retriever.invoke(query)
        documents = [doc.page_content for doc in docs]
        # Scores aren’t directly available; use a placeholder or compute if needed
        scores = [1.0 - i * 0.1 for i in range(len(docs))]  # Mock scores
        return documents, scores