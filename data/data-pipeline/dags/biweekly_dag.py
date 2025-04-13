from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta

# Define default arguments for the biweekly DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the biweekly DAG
with DAG(
    'biweekly_trigger_dag',
    default_args=default_args,
    description='Trigger the Data_pipeline_HARVEY DAG every 2 weeks',
    schedule_interval='0 0 */14 * *',  # Every 14 days at midnight
    start_date=datetime(2025, 1, 1),  # Adjust start date as needed
    catchup=False,
    tags=['biweekly'],
) as dag:
    # Task to trigger the Data_pipeline_HARVEY DAG
    trigger_data_pipeline = TriggerDagRunOperator(
        task_id='trigger_data_pipeline',
        trigger_dag_id='Data_pipeline_HARVEY',  # The ID of the DAG to trigger
        reset_dag_run=True,  # Reset the DAG run if it already exists
        wait_for_completion=False,  # Do not wait for the triggered DAG to complete
    )