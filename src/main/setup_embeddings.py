import os
import pandas as pd
from langchain.schema import Document
from config_loader import config_loader

class DocumentLoader:
    """Handles document loading and processing from CSV files."""

    def __init__(self):
        """Initialize document loader with dynamically set file path."""
        self.data_path = config_loader.get("paths.data_path")

        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"❌ Error: File '{self.data_path}' not found!")

    def load_documents(self):
        """Reads CSV file and converts rows into structured document objects."""
        df = pd.read_csv(self.data_path)

        documents = []
        for _, row in df.iterrows():
            # Convert row data into a string
            content = ' '.join([str(val) for val in row.values])
            
            # Store metadata for filtering and attribution
            metadata = {col: str(row[col]) for col in df.columns}
            
            # Create document
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)

        print(f"📂 Successfully loaded {len(documents)} documents from {self.data_path}")

        return documents
