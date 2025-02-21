# file made with a class to save data to reduce duplication
import os
import pickle
import faiss

#Had import errors, for airflow, have to decide how to resolve to use this.

class SaveFile:
    def __init__(self, dir_name, file_name, data):
        self.data = data
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), dir_name)
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_path = os.path.join(self.output_dir, file_name)

    def save_csv_file(self):
        self.data.to_csv(self.output_path, index=False)


    def save_serialized_file(self):
        with open(self.output_path, 'wb') as f:
            pickle.dump(self.data, f)

    def save_faiss_index_file(self):
        faiss.write_index(self.data, self.output_path)


    
