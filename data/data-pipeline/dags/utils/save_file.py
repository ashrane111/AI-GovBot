# file made with a class to save data to reduce duplication
import os
import pickle
import faiss
import logging

# Set up custom logger instead of root logger
logger = logging.getLogger('save_file_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'save_file.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Prevent log propagation to Airflow's root logger
logger.propagate = False

class SaveFile:
    def __init__(self, dir_name, file_name, data):
        try:
            self.data = data
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), dir_name)
            os.makedirs(self.output_dir, exist_ok=True)
            self.output_path = os.path.join(self.output_dir, file_name)
            logger.info(f"Initialized SaveFile for {file_name} in directory {dir_name}")
        except Exception as e:
            logger.error(f"Error initializing SaveFile: {e}")
            raise

    def save_csv_file(self):
        try:
            self.data.to_csv(self.output_path, index=False)
            logger.info(f"Successfully saved CSV file to {self.output_path}")
        except Exception as e:
            logger.error(f"Error saving CSV file to {self.output_path}: {e}")
            raise

    def save_serialized_file(self):
        try:
            with open(self.output_path, 'wb') as f:
                pickle.dump(self.data, f)
            logger.info(f"Successfully saved serialized file to {self.output_path}")
        except Exception as e:
            logger.error(f"Error saving serialized file to {self.output_path}: {e}")
            raise

    def save_faiss_index_file(self):
        try:
            faiss.write_index(self.data, self.output_path)
            logger.info(f"Successfully saved FAISS index to {self.output_path}")
        except Exception as e:
            logger.error(f"Error saving FAISS index to {self.output_path}: {e}")
            raise



