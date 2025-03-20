from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 16),
    'retries': 3,
}

def push_process_date(**kwargs):
    process_date = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(days=1)
    kwargs['ti'].xcom_push(key='process_date', value=str(process_date))
    print(f"Pushed process_date: {process_date}")


with DAG(
    'git_analytics_hub',
    default_args=default_args,
    schedule_interval=None
) as dag:
    
    get_process_date = PythonOperator(
        task_id='get_process_date',
        python_callable=push_process_date,
        provide_context=True
    )

    fetch_data = BashOperator(
        dag=dag,
        task_id='fetch_data',
        bash_command="python /opt/airflow/src/scripts/fetch_raw_data.py {{ ti.xcom_pull(task_ids='get_process_date', key='process_date') }}",
        do_xcom_push=False
    )

    # Task dependencies
    get_process_date >> fetch_data
