from dotenv import load_dotenv
import os
from google.cloud import storage

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """
    Uploads a file from a local path to a GCS bucket.

    Arguments:
      bucket_name: Name of the target GCS bucket.
      source_file_name: Local path to the file to upload.
      destination_blob_name: Desired path/name for the file in GCS.
    """
    # The google-cloud-storage library automatically picks up the
    # GOOGLE_APPLICATION_CREDENTIALS environment variable.
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File '{source_file_name}' uploaded to '{destination_blob_name}'.")

# To run as a standalone script:
if __name__ == '__main__':
    # Load variables from the .env file into the environment
    load_dotenv()

    BUCKET_NAME = 'datasets-mlops-25'
    SOURCE_FILE = '../agora_dataset/agora/documents.csv'
    DESTINATION_BLOB = 'datasets/dataset.csv'
    upload_blob(BUCKET_NAME, SOURCE_FILE, DESTINATION_BLOB)
