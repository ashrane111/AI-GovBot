import pandas as pd
from langchain.schema import Document
from .embeddings_model import SentenceTransformerEmbeddings
import os
class DocumentLoader:
    def __init__(self, file_path="src/index/Documents_segments_merged.csv"):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")

    def load_documents(self):
        df = pd.read_csv(self.file_path)
        documents = []
        for _, row in df.iterrows():
            content = ' '.join([str(val) for val in row.values])
            metadata = {col: str(row[col]) for col in df.columns}
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
        print(f"Loaded {len(documents)} documents from {self.file_path}")
        embeddings = SentenceTransformerEmbeddings()
        return {"documents": documents, "embeddings": embeddings}