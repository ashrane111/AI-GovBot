#!/usr/bin/env python3
import os
import logging
from google.cloud import storage
import datetime
import hashlib

# Set up a custom logger for download operations
logger = logging.getLogger('gcs_download_logger')
logger.setLevel(logging.INFO)

# Create a directory for logs if it doesn't exist
current_dir = os.path.dirname(os.path.abspath(__file__))
# parent dir is directory above current directory
parent_dir = os.path.dirname(current_dir)
log_dir = os.path.join(current_dir, 'util_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'gcs_download.log')

# Create file handler and set formatter
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False

def download_latest_file(bucket_name, blob_prefix, local_destination):
    """
    Downloads the latest version of the file matching the given blob_prefix
    from the specified GCS bucket to the local_destination.

    If your GCS bucket has object versioning enabled, this code will list all versions,
    sort by the updated timestamp, and select the most recent one.
    
    Parameters:
      - bucket_name (str): Name of the GCS bucket.
      - blob_prefix (str): Prefix of the blob (or exact blob name) to search for.
      - local_destination (str): Local file path where the file should be saved.
    """
    try:
        logger.info(f"Searching for blobs in bucket '{bucket_name}' with prefix '{blob_prefix}'.")
        client = storage.Client()

        # Include older versions if versioning is enabled using versions=True
        blobs = list(client.list_blobs(bucket_name, prefix=blob_prefix, versions=True))
        if not blobs:
            logger.error(f"No blobs found with prefix '{blob_prefix}' in bucket '{bucket_name}'.")
            return

        # Sort all matching blobs by updated timestamp (most recent first)
        blobs.sort(key=lambda b: b.updated, reverse=True)
        latest_blob = blobs[0]
        logger.info(f"Latest blob found: '{latest_blob.name}' updated at {latest_blob.updated}.")

        # Ensure that the local destination directory exists
        local_dir = os.path.dirname(local_destination)
        os.makedirs(local_dir, exist_ok=True)

        # Download the most recent blob to the local file
        latest_blob.download_to_filename(local_destination)
        logger.info(f"Blob '{latest_blob.name}' downloaded successfully to '{local_destination}'.")
    except Exception as e:
        logger.error(f"Error downloading blob with prefix '{blob_prefix}' from bucket '{bucket_name}': {e}")
        raise


def is_blob_updated(bucket_name: str, blob_prefix: str, local_destination: str) -> bool:
    """
    Return True if the GCS blob is newer than the local file, or if the SHA256 checksums differ,
    or if the local file is missing. Otherwise return False.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.get_blob(blob_prefix)
    if blob is None:
        logger.error(f"Blob '{blob_prefix}' not found in bucket '{bucket_name}'")
        return False

    # Check existence
    if not os.path.exists(local_destination):
        return True

    # Timestamp check
    remote_ts: datetime.datetime = blob.updated  # UTC tz‑aware
    local_ts = datetime.datetime.fromtimestamp(
        os.path.getmtime(local_destination),
        tz=datetime.timezone.utc
    )
    if remote_ts > local_ts:
        return True

    # Checksum check – expects SHA256 stored in blob.metadata['sha256']
    blob.reload()  # ensure metadata is present
    remote_sha = None
    if blob.metadata and 'sha256' in blob.metadata:
        remote_sha = blob.metadata['sha256']
        logger.info(f"Remote SHA256: {remote_sha}")
    else:
        logger.warning(f"No SHA256 metadata on blob '{blob_prefix}'; skipping checksum check")
        return False

    # Compute local SHA256
    hash_obj = hashlib.sha256()
    with open(local_destination, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
    local_sha = hash_obj.hexdigest()
    logger.info(f"Local SHA256: {local_sha}")

    return remote_sha.lower() != local_sha.lower()

if __name__ == '__main__':
    BUCKET_NAME = "datasets-mlops-25"

    BLOB_PREFIX = "faiss_index/index.pkl"
    # Destination path for the downloaded file
    LOCAL_DESTINATION = os.path.join(parent_dir, "index", "index.pkl")

    if is_blob_updated(BUCKET_NAME, BLOB_PREFIX, LOCAL_DESTINATION):
        logger.info("Remote FAISS index is newer or missing locally.")
        download_latest_file(BUCKET_NAME, BLOB_PREFIX, LOCAL_DESTINATION)
    else:
        logger.info("Local FAISS index is up‑to‑date.")
    
