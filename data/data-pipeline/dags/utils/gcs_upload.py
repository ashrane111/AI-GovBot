from google.cloud import storage
import os

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def upload_merged_data_to_gcs(data):
    """Uploads the merged data to GCS."""
    bucket_name = "datasets-mlops-25" 

    source_file_name = os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), "result_data"), "Documents_segments_merged_cleaned.csv")
    destination_blob_name = "result_data/Documents_segments_merged_cleaned.csv"

    upload_to_gcs(bucket_name, source_file_name, destination_blob_name)
