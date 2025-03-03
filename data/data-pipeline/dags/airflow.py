#airflow definition
# Import necessary libraries and modules
import os
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
from airflow import configuration as conf
from utils.data_validation import validate_downloaded_data_files, check_validation_status
from utils.bias_detection import detect_and_simulate_bias
# Enable pickle support for XCom, allowing data to be passed between tasks
conf.set('core', 'enable_xcom_pickling', 'True')

# Define default arguments for your DAG
default_args = {
    'owner': 'Vedant Rishi Das',
    'start_date': datetime(2025, 2, 19),
    'retries': 0, # Number of retries in case of task failure
    'retry_delay': timedelta(minutes=5), # Delay before retries
}

# Define EmailOperators for success and failure notifications
# def task_success_slack_alert(context):
#     success_email = EmailOperator(
#         task_id='send_email',
#         to='vedantdas130701@gmail.com',
#         subject='Success Notification from Airflow',
#         html_content='<p>The task is successful.</p>',
#         dag=context['dag']
#     )
#     success_email.execute(context=context)

# def task_fail_slack_alert(context):
#     failure_email = EmailOperator(
#         task_id='send_email',
#         to='vedantdas130701@gmail.com',
#         subject='Failure Notification from Airflow',
#         html_content='<p>The task has failed.</p>',
#         dag=context['dag']
#     )
#     failure_email.execute(context=context)

# Create a DAG instance named 'Airflow_Lab1' with the defined default arguments
dag = DAG(
    'Data_pipeline_HARVEY',
    default_args=default_args,
    description='Dag for the data pipeline',
    schedule_interval=None,  # Set the schedule interval or use None for manual triggering
    catchup=False,
)

# Task to download data in zip, calls the 'download_zip_file' Python function
download_unzip_task = PythonOperator(
    task_id='download_unzip_task',
    python_callable=download_and_unzip_data_file,
    op_kwargs={
        'download_url': 'https://zenodo.org/records/14877811/files/agora.zip', 
        'output_dir_name': 'merged_input',  
    },
    dag=dag,
)

# Validation task
validate_schema_task = PythonOperator(
    task_id='validate_schema_task',
    python_callable=validate_downloaded_data_files,
    op_kwargs={
        'file_schema_pairs':  [
            (os.path.join(os.path.dirname(__file__), "merged_input/agora/authorities.csv"),
            os.path.join(os.path.dirname(__file__), "schema/authorities_data_schema.pbtxt")),
            (os.path.join(os.path.dirname(__file__), "merged_input/agora/collections.csv"),
            os.path.join(os.path.dirname(__file__), "schema/collections_data_schema.pbtxt")),
            (os.path.join(os.path.dirname(__file__), "merged_input/agora/documents.csv"),
            os.path.join(os.path.dirname(__file__), "schema/documents_data_schema.pbtxt")),
            (os.path.join(os.path.dirname(__file__), "merged_input/agora/segments.csv"),
            os.path.join(os.path.dirname(__file__), "schema/segments_data_schema.pbtxt")),
        ]},
    dag=dag,
)

check_validation_task = PythonOperator(
    task_id='check_validation_status',
    python_callable=check_validation_status,
    provide_context=True,
    dag=dag,
)

# Email alert for validation failure with anomalies
def send_validation_failure_email(**kwargs):
    ti = kwargs['ti']
    anomalies = ti.xcom_pull(task_ids='check_validation_status', key='anomalies')

    email_task = EmailOperator(
        task_id='send_validation_failure_email',
        to='sanjanajd115@gmail.com',
        subject='Data Pipeline Alert: Schema Validation Failed',
        html_content=f'<p>Schema validation failed with the following anomalies:</p><p>{anomalies}</p>',
        dag=kwargs['dag'],
    )
    email_task.execute(context=kwargs)

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
        'temp_dir': os.path.join(os.path.dirname(__file__), "merged_input/agora"), 
    },
    dag=dag,
)


# Task to load data, calls the 'load_data' Python function
load_data_task = PythonOperator(
    task_id='load_data_task',
    python_callable=load_data,
    op_args=[os.path.join(os.path.dirname(__file__), "merged_input/Documents_segments_merged.csv")],
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
generate_embeddings_task = PythonOperator(
    task_id='generate_embeddings_task',
    python_callable=generate_embeddings,
    op_args=[clean_text_task.output],
    provide_context=True,
    dag=dag,
)
# Task to load a model using the 'load_model_elbow' function, depends on 'build_save_model_task'
create_index_task = PythonOperator(
    task_id='create_index_task',
    python_callable=create_index,
    op_args=[generate_embeddings_task.output],
    dag=dag,
)

upload_to_gcs_task = PythonOperator(
    task_id='upload_to_gcs_task',
    python_callable=upload_merged_data_to_gcs,
    op_args=[create_index_task.output],
    dag=dag,
)

send_email = EmailOperator(
    task_id='send_email',
    to='baravkardhanshree@gmail.com',
    subject='Notification from Airflow',
    html_content='<p>This task is completed.</p>',
    dag=dag
)

# TriggerDag = TriggerDagRunOperator(
#     task_id='my_trigger_task',
#     trigger_rule=TriggerRule.ALL_DONE,
#     trigger_dag_id='Airflow_Lab2_Flask',
#     dag=dag
# )

# Set task dependencies
download_unzip_task >> validate_schema_task >> check_validation_task
check_validation_task >> data_combine_task  # If validation passes, continue
check_validation_task >> trigger_validation_failure_email  # If validation fails, send an alert

# Continue the pipeline after successful validation
data_combine_task >> load_data_task >> preprocess_data_task >> clean_text_task >> generate_embeddings_task >> create_index_task >> upload_to_gcs_task >> send_email
load_data_task >> data_bias_task

# If this script is run directly, allow command-line interaction with the DAG
if __name__ == "__main__":
    dag.cli()

