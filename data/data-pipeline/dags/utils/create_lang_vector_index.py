# file to create vector index using faiss
import numpy as np
import pickle
import os
import sys
import logging
from langchain_community.vectorstores import FAISS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from sentence_transformer_encoder import SentenceTransformerEmbeddings


# Set up custom logger instead of root logger
logger = logging.getLogger('create_lang_vector_index_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'create_lang_vector_index_logger.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Prevent log propagation to Airflow's root logger
logger.propagate = False


output_dir_name = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faiss_index") 
os.makedirs(output_dir_name, exist_ok=True)

def create_lang_index(data, embeddings_model = "sentence-transformers/all-mpnet-base-v2"):
    try:
        documents = pickle.loads(data)
        logging.info("Loaded data to vectorize")
        logger.info("Starting to load embeddings")
        embeddings = SentenceTransformerEmbeddings(embeddings_model)
        logger.info("loaded embeddings")
        vector_store = FAISS.from_documents(documents, embedding=embeddings)
        vector_store.save_local(output_dir_name)
        logging.info(f"Saved FAISS index to {output_dir_name}")
    except Exception as e:
        logging.error(f"An error occurred while creating the index: {e}")
        raise

def main():
    try:
        print("Creating embeddings...")
    except Exception as e:
        logging.error(e)
        print(e)

if __name__ == "__main__":
    main()