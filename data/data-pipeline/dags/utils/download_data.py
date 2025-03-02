import os
import requests
import zipfile
import io
import logging

# Set up custom logger instead of root logger
logger = logging.getLogger('download_data_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'download_data.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Prevent log propagation to Airflow's root logger
logger.propagate = False

# Define the function to download the zip file
def download_and_unzip_data_file(download_url, output_dir_name):
    try:
        # Ensure the directory exists
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir_name)
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Downloading from {download_url}")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        
        zip_file_bytes = io.BytesIO(response.content)
        logger.info("Download complete, extracting files...")

        with zipfile.ZipFile(zip_file_bytes, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        logger.info(f"File extracted successfully to {output_dir}")
        return output_dir
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download file: {e}")
        raise Exception(f"Failed to download file: {e}")
    except zipfile.BadZipFile as e:
        logger.error(f"Failed to unzip file: {e}")
        raise Exception(f"Failed to unzip file: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise Exception(f"An error occurred: {e}")

# Main function for standalone testing
def main():
    test_url = 'https://zenodo.org/records/14877811/files/agora.zip'  # Replace with a valid URL
    test_path = 'merged_input'  # Replace with a valid path
    try:
        logger.info("Starting download and extraction process")
        download_and_unzip_data_file(test_url, test_path)
        logger.info("Download and extraction process completed successfully")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(e)

if __name__ == "__main__":
    main()
