# text cleaning file
import pandas as pd
import re
import pickle
import os
import logging

# Set up custom logger instead of root logger
logger = logging.getLogger('text_clean_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'text_clean.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Prevent log propagation to Airflow's root logger
logger.propagate = False

output_dir_name = "result_data"
clean_data_path = 'Documents_segments_merged_cleaned.csv'
clean_data_xlsx_path = 'Documents_segments_merged_cleaned.xlsx'

def clean_text(text):
    try:
        text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
        text = re.sub(r'[^a-zA-Z0-9.,;()\-\s]', '', text)  # Keep only relevant characters
        text = text.lower().strip()
        return text
    except Exception as e:
        logger.error(f"An error occurred while cleaning text: {e}")
        raise

def clean_full_text(data):
    try:
        pd_csv_file = pickle.loads(data)
        logger.info("Loaded data from serialized input")
        # Remove 'Tags' column
        pd_csv_file.drop(columns=['Tags'], inplace=True)
    
        
        pd_csv_file['cleaned_text'] = pd_csv_file['Full Text'].apply(clean_text)
        logger.info("Cleaned text in the DataFrame")

        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir_name)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, clean_data_path)
        output_xlsx_path = os.path.join(output_dir, clean_data_xlsx_path)
        pd_csv_file.to_csv(output_path, index=False)  # TODO: upload to gcp in real scenario instead of saving in local
        pd_csv_file.to_excel(output_xlsx_path, index=False)
        logger.info(f"Saved cleaned data to {output_path}")

        serialized_data = pickle.dumps(pd_csv_file)
        logger.info("Serialized cleaned data")
        return serialized_data
    except Exception as e:
        logger.error(f"An error occurred while cleaning full text: {e}")
        raise

def main():
    try:
        csv_file = pd.read_csv('merged_input/Documents_segments_merged.csv')
        logger.info("Loaded CSV file for cleaning")
        
        serialized_data = pickle.dumps(csv_file)
        clean_full_text(serialized_data)
        logger.info("Data cleaned successfully")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(e)

if __name__ == "__main__":
    main()