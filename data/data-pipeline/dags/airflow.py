#airflow definition
# Import necessary libraries and modules
import os
import json
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.email_operator import EmailOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from utils.data_loader import load_data
from utils.text_clean import clean_full_text
from utils.embeddings_gen import generate_embeddings
from utils.create_vector_index import create_index
from utils.gcs_upload import upload_merged_data_to_gcs
from utils.download_data import download_and_unzip_data_file
from utils.data_extract_combine import extract_and_merge_documents
from utils.preprocess_data import preprocess_data
from utils.data_vector_formatter import format_documents_dict
from utils.create_lang_vector_index import create_lang_index
from airflow import configuration as conf
from utils.data_validation import validate_downloaded_data_files, check_validation_status
from utils.bias_detection import detect_and_simulate_bias
from utils.update_config import update_config_with_download_url
# from utils.sentence_transformer_encoder import SentenceTransformerEmbeddings
# Enable pickle support for XCom, allowing data to be passed between tasks
conf.set('core', 'enable_xcom_pickling', 'True')

def update_download_url_task():
    config_path = os.path.join(os.environ.get('AIRFLOW_HOME', '/opt/airflow'), 'config', 'config.json')
    success = update_config_with_download_url(config_path)
    if not success:
        raise Exception("Failed to update config.json")


def get_config_value(key, default=None):
    """Get a value from the config.json file"""
    try:
        config_path = os.path.join(os.environ.get('AIRFLOW_HOME', '/opt/airflow'), 'config', 'config.json')
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        return config.get(key, default)
    except Exception as e:
        print(f"Error reading config file: {e}")
        return default
    
to_email = get_config_value('TO_EMAIL', 'vedantrishidas@gmail.com')

def get_file_schema_pairs():
    """Get file schema pairs from config.json"""
    file_schema_pairs = get_config_value('file_schema_pairs', [])
    
    # Convert the JSON structure to the format needed by the validation function
    result = []
    base_dir = os.path.dirname(__file__)
    
    for pair in file_schema_pairs:
        file_path = os.path.join(base_dir, pair.get('file', ''))
        schema_path = os.path.join(base_dir, pair.get('schema', ''))
        result.append((file_path, schema_path))
    
    return result

def get_file_path(config_key, default_path=None):
    """Get full file path from config value"""
    config_path = get_config_value('data_dir', {}).get(config_key, default_path)
    if not config_path:
        return None
    return os.path.join(os.path.dirname(__file__), config_path)

# Email alert for validation failure with anomalies
def send_validation_failure_email(**kwargs):
    ti = kwargs['ti']
    anomalies = ti.xcom_pull(task_ids='check_validation_status', key='anomalies')

    email_task = EmailOperator(
        task_id='send_validation_failure_email',
        to=to_email,
        subject='Data Pipeline Alert: Schema Validation Failed',
        html_content=f'<p>Schema validation failed with the following anomalies:</p><p>{anomalies}</p>',
        dag=kwargs['dag'],
    )
    email_task.execute(context=kwargs)

# Define default arguments for your DAG
default_args = {
    'owner': get_config_value('airflow_owner', 'airflow'),
    'start_date': datetime(2025, 2, 19),
    'retries': 0, # Number of retries in case of task failure
    'retry_delay': timedelta(minutes=5), # Delay before retries
}

# Create a DAG instance named 'Airflow_Lab1' with the defined default arguments
dag = DAG(
    'Data_pipeline_HARVEY',
    default_args=default_args,
    description='Dag for the data pipeline',
    schedule_interval=None,  # Set the schedule interval or use None for manual triggering
    catchup=False,
)

# Task 0: Update config.json
update_config_operator = PythonOperator(
    task_id='update_config_task',
    python_callable=update_download_url_task,
    dag=dag,
)

# Task to download data in zip, calls the 'download_zip_file' Python function
download_unzip_task = PythonOperator(
    task_id='download_unzip_task',
    python_callable=download_and_unzip_data_file,
    op_kwargs={
        'download_url': get_config_value('download_url', 'https://zenodo.org/records/14877811/files/agora.zip'), 
        'output_dir_name': get_config_value('output_dir_name', 'merged_input'), 
    },
    dag=dag,
)

# Validation task
validate_schema_task = PythonOperator(
    task_id='validate_schema_task',
    python_callable=validate_downloaded_data_files,
    op_kwargs={
        'file_schema_pairs':  get_file_schema_pairs()
        },
    dag=dag,
)

check_validation_task = PythonOperator(
    task_id='check_validation_status',
    python_callable=check_validation_status,
    provide_context=True,
    dag=dag,
)

trigger_validation_failure_email = PythonOperator(
    task_id='trigger_validation_failure_email',
    python_callable=send_validation_failure_email,
    provide_context=True,
    trigger_rule=TriggerRule.ONE_FAILED,  # Ensures execution only if validation fails
    dag=dag,
)


data_combine_task = PythonOperator(
    task_id='data_combine_task',
    python_callable=extract_and_merge_documents,
    op_kwargs={
        'temp_dir': get_file_path('agora_dir', "merged_input/agora"), 
    },
    dag=dag,
)


# Task to load data, calls the 'load_data' Python function
load_data_task = PythonOperator(
    task_id='load_data_task',
    python_callable=load_data,
    op_args=[get_file_path('merged_data_file', "merged_input/Documents_segments_merged.csv")],
    dag=dag,
)

data_bias_task = PythonOperator(
    task_id='data_bias_task',
    python_callable=detect_and_simulate_bias,
    op_args=[load_data_task.output],  # Pass the loaded data to the bias function
    dag=dag,
)


preprocess_data_task = PythonOperator(
    task_id='preprocess_data_task',
    python_callable=preprocess_data,
    op_args=[load_data_task.output],
    dag=dag,
)
# Task to perform data preprocessing, depends on 'load_data_task'
clean_text_task = PythonOperator(
    task_id='clean_text_task',
    python_callable=clean_full_text,
    op_args=[preprocess_data_task.output],
    dag=dag,
)
# Task to generate embeddings of the full text, depends on 'clean_text_task'
# generate_embeddings_task = PythonOperator(
#     task_id='generate_embeddings_task',
#     python_callable=generate_embeddings,
#     op_args=[clean_text_task.output, get_config_value('embedding_model', "sentence-transformers/all-mpnet-base-v2")],
#     provide_context=True,
#     dag=dag,
# )

format_vector_data_task = PythonOperator(
    task_id='format_vector_data_task',
    python_callable=format_documents_dict,
    op_args=[clean_text_task.output],
    dag=dag,
)
# Task to load a model using the 'load_model_elbow' function, depends on 'build_save_model_task'
# create_index_task = PythonOperator(
#     task_id='create_index_task',
#     python_callable=create_index,
#     op_args=[generate_embeddings_task.output],
#     dag=dag,
# )

create_lang_index_task = PythonOperator(
    task_id='create_lang_index_task',
    python_callable=create_lang_index,
    op_args=[format_vector_data_task.output, get_config_value('embedding_model', "sentence-transformers/all-mpnet-base-v2")],
    dag=dag,
)

upload_to_gcs_task = PythonOperator(
    task_id='upload_to_gcs_task',
    python_callable=upload_merged_data_to_gcs,
    op_args=[create_lang_index_task.output],
    dag=dag,
)

send_email = EmailOperator(
    task_id='send_email',
    to=to_email,
    subject='Notification from Airflow',
    html_content='<p>This task is completed.</p>',
    dag=dag
)

# Set task dependencies
update_config_operator >> download_unzip_task
download_unzip_task >> validate_schema_task >> check_validation_task
check_validation_task >> data_combine_task  # If validation passes, continue
check_validation_task >> trigger_validation_failure_email  # If validation fails, send an alert

# Continue the pipeline after successful validation
# data_combine_task >> load_data_task >> preprocess_data_task >> clean_text_task >> generate_embeddings_task >> create_index_task >> upload_to_gcs_task >> send_email
data_combine_task >> load_data_task >> preprocess_data_task >> clean_text_task >> format_vector_data_task >> create_lang_index_task >> upload_to_gcs_task >> send_email
load_data_task >> data_bias_task

# If this script is run directly, allow command-line interaction with the DAG
if __name__ == "__main__":
    dag.cli()

