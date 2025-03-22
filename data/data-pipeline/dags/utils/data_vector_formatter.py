import pandas as pd
from langchain.schema import Document
import os
import logging
import pickle


# Set up custom logger instead of root logger
logger = logging.getLogger('data_vector_formatter_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'data_vector_formatter_logger.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Prevent log propagation to Airflow's root logger
logger.propagate = False

def format_documents_dict(data):
    try:
        pd_csv_file = pickle.loads(data)
        logger.info("Loaded data from serialized input")
        documents = []
        for _, row in pd_csv_file.iterrows():
            # Create content from relevant columns
            content = ' '.join([str(val) for val in row.values])
            
            # Store metadata for filtering and attribution
            metadata = {col: str(row[col]) for col in pd_csv_file.columns}
            
            # Create document
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)

        logger.info(f"Loaded {len(documents)} documents")
        
        serialized_data = pickle.dumps(documents)
        logger.info("Serialized documents")
        logger.info(f"Returning serialized data of length {len(serialized_data)}")
        return serialized_data
    except Exception as e:
        logger.error(f"An error occurred while document formatting: {e}")
        raise
 

if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'merged_input')
    data_path = os.path.join(data_dir, 'Documents_segments_merged.csv')
    csv_file = pd.read_csv(data_path)
    serialized_data = pickle.dumps(csv_file)
    serialized_formatted_data = format_documents_dict(serialized_data)
    formatted_data = pickle.loads(serialized_formatted_data)
    print(formatted_data["embeddings"])