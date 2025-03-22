from langchain_community.vectorstores import FAISS
from main.embeddings_model import SentenceTransformerEmbeddings
from main.config_loader import config_loader

class Retriever:
    def __init__(self):
        self.embeddings = SentenceTransformerEmbeddings()
        index_dir = config_loader.get("paths.index_dir")
        self.vector_store = FAISS.load_local(
            index_dir,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})

    def retrieve(self, query):
        # Use similarity_search_with_score for actual scores
        docs_and_scores = self.vector_store.similarity_search_with_score(query, k=5)
        documents = [doc.page_content for doc, score in docs_and_scores]
        scores = [score for doc, score in docs_and_scores]  # Distance scores (lower is better)
        return documents, scores