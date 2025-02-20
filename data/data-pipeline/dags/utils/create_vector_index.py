# file to create vector index using faiss
import faiss
import numpy as np
import pickle
import os
# from save_file import SaveFile

output_dir_name = "FAISS_Index"
index_path="legal_embeddings.index"

def create_index(data):
    embeddings = pickle.loads(data)
    d = embeddings.shape[1]
    index = faiss.IndexFlatL2(d) 
    index.add(embeddings)

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir_name)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, index_path)
    faiss.write_index(index, output_path)
    
    # save_data = SaveFile(output_dir, index_path, index)
    # save_data.save_faiss_index_file()
    

def main():
    print("Creating embeddings...")

if __name__ == "__main__":
    main()