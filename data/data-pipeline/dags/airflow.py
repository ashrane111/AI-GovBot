#airflow definition
# Import necessary libraries and modules
import os
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from utils.data_loader import load_data
from utils.text_clean import clean_full_text
from utils.embeddings_gen import generate_embeddings
from utils.create_vector_index import create_index

from airflow import configuration as conf

# Enable pickle support for XCom, allowing data to be passed between tasks
conf.set('core', 'enable_xcom_pickling', 'True')

# Define default arguments for your DAG
default_args = {
    'owner': 'Vedant Rishi Das',
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

# Define PythonOperators for each function

# Task to load data, calls the 'load_data' Python function
load_data_task = PythonOperator(
    task_id='load_data_task',
    python_callable=load_data,
    op_args=[os.path.join(os.path.dirname(__file__), "./merged_input/Documents_segments_merged.csv")],
    dag=dag,
)
# Task to perform data preprocessing, depends on 'load_data_task'
clean_text_task = PythonOperator(
    task_id='clean_text_task',
    python_callable=clean_full_text,
    op_args=[load_data_task.output],
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



# Set task dependencies
load_data_task >> clean_text_task >> generate_embeddings_task >> create_index_task

# If this script is run directly, allow command-line interaction with the DAG
if __name__ == "__main__":
    dag.cli()
