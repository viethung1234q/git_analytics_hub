from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 16),
    'retries': 3,
}

dag = DAG(
    'git_analytics_hub',
    default_args=default_args,
    schedule_interval=None
)

run_serialise_script = BashOperator(
    task_id='run_serialise_data',
    bash_command='python /opt/airflow/src/scripts/fetch_raw_data.py',
    dag=dag,
)

run_serialise_script
