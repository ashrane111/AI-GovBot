# file to generate embeddings using sentence transformer
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os
import logging

# Set up custom logger instead of root logger
logger = logging.getLogger('embeddings_gen_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'embeddings_gen.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Prevent log propagation to Airflow's root logger
logger.propagate = False

output_dir_name = "embeddings"
embeddings_file_path = "embeddings.pkl"

## TODO: DVC - with gcloud

def generate_embeddings(data, transformer_model="all-MiniLM-L6-v2"):
    try:
        pd_csv_file = pickle.loads(data)
        logger.info("Loaded data from serialized input")
        unembedded_text = pd_csv_file['cleaned_text'].tolist()
        
        model = SentenceTransformer(transformer_model)
        embeddings = model.encode(unembedded_text, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype='float32')
        logger.info("Generated embeddings")

        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir_name)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, embeddings_file_path)
        with open(output_path, 'wb') as f:
            pickle.dump(embeddings, f)
        logger.info(f"Saved embeddings to {output_path}")

        serialized_data = pickle.dumps(embeddings)
        logger.info("Serialized embeddings")
        return serialized_data
    except Exception as e:
        logger.error(f"An error occurred while generating embeddings: {e}")
        raise

def main():
    try:
        csv_file = pd.read_csv('merged_input/Documents_segments_merged.csv')
        logger.info("Loaded CSV file for generating embeddings")
        
        serialized_data = pickle.dumps(csv_file)
        generate_embeddings(serialized_data)
        logger.info("Embeddings generated successfully")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(e)

if __name__ == "__main__":
    main()