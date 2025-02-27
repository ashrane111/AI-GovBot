# file to generate embeddings using sentence transformer
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os
# from save_file import SaveFile

output_dir_name = "embeddings"
embeddings_file_path = "embeddings.pkl"


## TODO: DVC - with gcloud

def generate_embeddings(data, transformer_model="sentence-transformers/multi-qa-mpnet-base-dot-v1"):
    pd_csv_file = pickle.loads(data)
    model = SentenceTransformer(transformer_model)
    embeddings = model.encode(pd_csv_file['cleaned_text'].tolist(), show_progress_bar=True)
    embeddings = np.array(embeddings, dtype='float32')

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir_name)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, embeddings_file_path)
    with open(output_path, 'wb') as f:
        pickle.dump(embeddings, f)

    # save_data = SaveFile(output_dir, embeddings_file_path, embeddings)
    # save_data.save_serialized_file()

    serialized_data = pickle.dumps(embeddings)
    return serialized_data

def main():
    csv_file = pd.read_csv('merged_input/Documents_segments_merged.csv')
    # Call the method to perform the data extraction and merging
    generate_embeddings(csv_file)

if __name__ == "__main__":
    main()