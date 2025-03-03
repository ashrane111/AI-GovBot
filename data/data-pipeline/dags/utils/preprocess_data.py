import pandas as pd
import os
import logging
import pickle

# Set up custom logger instead of root logger
logger = logging.getLogger('data_validation_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'data_validation.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Prevent log propagation to Airflow's root logger
logger.propagate = False

def format_date(pd_csv_file):
    pd_csv_file['Most recent activity date'] = pd.to_datetime(pd_csv_file['Most recent activity date'], errors='coerce')
    pd_csv_file['Proposed date'] = pd.to_datetime(pd_csv_file['Proposed date'], errors='coerce')
    # pd_csv_file = pd_csv_file.dropna(subset=['Proposed date'])
    pd_csv_file.loc[pd_csv_file['Most recent activity date'] < pd_csv_file['Proposed date'], 'Most recent activity date'] = pd_csv_file['Proposed date']
    return pd_csv_file

def summarize_text(text, length=300):
    return text[:length] if isinstance(text, str) else ""

def preprocess_data(data):
    try:
        pd_csv_file = pickle.loads(data)
        logger.info("Loaded data from serialized input")

        documents_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'merged_input/agora')
        authority_df = pd.read_csv(f"{documents_dir}/authorities.csv")
        logger.info("Accessed authorities")
        authorized_authorities = set(authority_df["Name"].dropna())

        pd_csv_file = pd_csv_file[pd_csv_file['Authority'].isin(authorized_authorities)]

        pd_csv_file = pd_csv_file.dropna(subset=['Full Text'])
        
        pd_csv_file = format_date(pd_csv_file)
        pd_csv_file['Casual name'].fillna("N/A", inplace=True)
        pd_csv_file['Short summary'].fillna("N/A", inplace=True)
        pd_csv_file['Long summary'].fillna(pd_csv_file['Full Text'].apply(lambda x: summarize_text(x, 500)), inplace=True)
        pd_csv_file = pd_csv_file.dropna(subset=['Long summary'])

        serialized_data = pickle.dumps(pd_csv_file)
        logger.info("Serialized validated data")   
        return serialized_data
    except Exception as e:
        logger.error(f"An error ocurred while validating and processing data: {e}")
        raise


def main():
    try:
        # Load the CSV file
        csv_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'merged_input/Documents_segments_merged.csv')
        pd_csv_file = pd.read_csv(csv_file_path)
        logger.info("Loaded CSV file for validation and cleaning")

        # Serialize the data
        serialized_data = pickle.dumps(pd_csv_file)

        # Validate and clean the data
        validated_data = preprocess_data(serialized_data)
        logger.info("Data validated and cleaned successfully")

        # Save the validated data back to a CSV file
        validated_df = pickle.loads(validated_data)
        validated_csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'merged_input/Documents_segments_validated.csv')
        validated_df.to_csv(validated_csv_path, index=False)
        logger.info(f"Validated data saved to {validated_csv_path}")

    except Exception as e:
        logger.error(f"An error occurred in the main function: {e}")
        print(e)

if __name__ == "__main__":
    main()