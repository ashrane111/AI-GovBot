# file to load data from csv file and serialize it
import pandas as pd
import pickle
import os
import logging

# Set up custom logger instead of root logger
logger = logging.getLogger('data_loader_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'data_loader.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Prevent log propagation to Airflow's root logger
logger.propagate = False

def load_data(file_path):
    try:
        logger.info(f"Attempting to load data from {file_path}")
        data = pd.read_csv(file_path)
        logger.info(f"Loaded data from {file_path}")
        serialized_data = pickle.dumps(data)
        logger.info(f"Serialized data from {file_path}")
        return serialized_data
    except Exception as e:
        logger.error(f"An error occurred while loading data from {file_path}: {e}")
        raise

def main():
    input_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'merged_input')
    csv_file_path = os.path.join(input_dir, 'Documents_segments_merged.csv')
    try:
        serialized_data = load_data(csv_file_path)
        logger.info(f"Data loaded and serialized successfully from {csv_file_path}")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(e)

if __name__ == "__main__":
    main()