# file to create vector index using faiss
import faiss
import numpy as np
import pickle
import os
import logging

# Set up custom logger instead of root logger
logger = logging.getLogger('create_vector_index_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'create_vector_index.log')

logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


output_dir_name = os.path.join(os.path.dirname(os.path.dirname(__file__)), "FAISS_Index") 
os.makedirs(output_dir_name, exist_ok=True)
index_path = os.path.join(output_dir_name, "legal_embeddings.index")

def create_index(data):
    try:
        embeddings = pickle.loads(data)
        logging.info("Loaded embeddings from serialized input")
        
        d = embeddings.shape[1]
        index = faiss.IndexFlatL2(d)
        index.add(embeddings)
        logging.info("Created FAISS index and added embeddings")

        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir_name)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, index_path)
        faiss.write_index(index, output_path)
        logging.info(f"Saved FAISS index to {output_path}")
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