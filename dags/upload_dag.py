from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from gcs_utils import upload_blob  # Import your function from gcs_utils

# Define your parameters
BUCKET_NAME = 'datasets-mlops-25'
SOURCE_FILE = '../agora_dataset/agora/documents.csv'
DESTINATION_BLOB = 'datasets/dataset.csv'


def upload_file():
    upload_blob(BUCKET_NAME, SOURCE_FILE, DESTINATION_BLOB)


default_args = {
    'start_date': datetime(2023, 1, 1),
}

with DAG(
        dag_id='upload_file_to_gcs',
        default_args=default_args,
        schedule_interval='@daily',
        catchup=False
) as dag:
    upload_task = PythonOperator(
        task_id='upload_task',
        python_callable=upload_file
    )

