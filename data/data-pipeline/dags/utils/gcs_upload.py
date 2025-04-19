from google.cloud import storage
import os
import logging

# Set up custom logger instead of root logger
logger = logging.getLogger('gcs_upload_logger')
logger.setLevel(logging.INFO)

# Create directory for logs if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'gcs_upload.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# Prevent log propagation to Airflow's root logger
logger.propagate = False

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name, create_if_missing=True):
    """Uploads a file to the bucket."""
    try:
        logger.info(f"Attempting to upload {source_file_name} to GCS bucket {bucket_name}")
        storage_client = storage.Client()
        # bucket = storage_client.bucket(bucket_name)

        try:
            bucket = storage_client.get_bucket(bucket_name)
            logger.info(f"Bucket {bucket_name} exists")
        except Exception as e:
            if create_if_missing:
                logger.info(f"Bucket {bucket_name} does not exist. Creating it...")
                bucket = storage_client.create_bucket(bucket_name)
                logger.info(f"Bucket {bucket_name} created")
            else:
                logger.error(f"Bucket {bucket_name} does not exist: {e}")
                raise

        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)
        logger.info(f"File {source_file_name} uploaded to {destination_blob_name}")
    except Exception as e:
        logger.error(f"Error uploading {source_file_name} to GCS: {e}")
        raise

def upload_merged_data_to_gcs():
    """Uploads the merged data to GCS."""
    try:
        bucket_name = "datasets-mlops-25" 



        source_file_name = os.path.join(os.path.dirname(os.path.dirname(__file__)),  "faiss_index/index.faiss")
        destination_blob_name = "faiss_index/index.faiss"

        logger.info(f"Preparing to upload .faiss to GCS")
        upload_to_gcs(bucket_name, source_file_name, destination_blob_name)
        logger.info(f".faiss uploaded to GCS successfully")

        source_file_name = os.path.join(os.path.dirname(os.path.dirname(__file__)),  "faiss_index/index.pkl")
        destination_blob_name = "faiss_index/index.pkl"

        logger.info(f"Preparing to upload .pkl to GCS")
        upload_to_gcs(bucket_name, source_file_name, destination_blob_name)
        logger.info(f".pkl data uploaded to GCS successfully")
    except Exception as e:
        logger.error(f"Error uploading merged data to GCS: {e}")
        raise

if __name__ == "__main__":
    upload_merged_data_to_gcs()


