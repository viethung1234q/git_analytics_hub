import pendulum
from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.utils.email import send_email
from datetime import datetime, timedelta


vnt_tz = pendulum.timezone("Asia/Ho_Chi_Minh")
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': pendulum.datetime(2024, 3, 16, tz='Asia/Ho_Chi_Minh'),
    'retries': 3,
}

# Push the date to process to XCom
def push_process_date(**kwargs):
    process_date = datetime.now(tz=vnt_tz).replace(minute=0, second=0, microsecond=0) - timedelta(days=1)
    process_date = process_date.strftime('%Y-%m-%d %H:%M:%S')
    kwargs['ti'].xcom_push(key='process_date', value=process_date)
    print(f"Pushed process_date: {process_date}")


def check_counter_value():
    counter_var = "hourly_collect_counter"
    counter = int(Variable.get(counter_var, default_var=0))  # Get counter, default 0
    counter += 1

    if counter >= 2:
        print("Reach threshold! Start aggregating data")
        counter = 0  # Reset counter
        Variable.set(counter_var, counter)  # Update variable
        return True

    Variable.set(counter_var, counter)
    print(f"Current counter: {counter}")
    return False


def send_email_alert():
    """Send email notification using Airflow email backend."""
    try:
        send_email(
            to=["<your_email"],  # Replace with your actual email,
            subject="Airflow Notification: Aggregation Successfully ✅",
            html_content="""
                <h2>Airflow Notification</h2>
                <p>Aggregation has been processed successfully.</p>
                <p>Go to your Airflow UI for more details.</p>
            """
        )
        print("OK")
    except Exception as e:
        print(f"Failed to send email: {e}")


with DAG(
    'git_analytics_hub',
    default_args=default_args,
    schedule=None,
    tags=["hourly", "dataset", "collect"]
) as dag:
    
    get_process_date = PythonOperator(
        task_id='get_process_date',
        python_callable=push_process_date,
        provide_context=True
    )

    fetch_data = BashOperator(
        dag=dag,
        task_id='fetch_data',
        bash_command=(
            "python /opt/airflow/src/scripts/fetch_raw_data.py "
            "{{ ti.xcom_pull(task_ids='get_process_date', key='process_date') }}"
        ),
        do_xcom_push=False
    )

    serialise_data = BashOperator(
        dag=dag,
        task_id='serialise_data',
        bash_command=(
            "python /opt/airflow/src/scripts/serialise_raw_data.py "
            "{{ ti.xcom_pull(task_ids='get_process_date', key='process_date') }}"
        ),
        do_xcom_push=False
    )

    check_counter = ShortCircuitOperator(
        task_id='check_counter',
        python_callable=check_counter_value,
        do_xcom_push=False
    )

    aggregate_data = BashOperator(
        dag=dag,
        task_id='aggregate_data',
        bash_command=(
            "python /opt/airflow/src/scripts/aggregate_tf_data.py "
            "{{ ti.xcom_pull(task_ids='get_process_date', key='process_date') }}"
        ),
        do_xcom_push=False
    )

    notify_to_email = PythonOperator(
        task_id='notify_to_email',
        python_callable=send_email_alert
    )

    # Task dependencies
    get_process_date >> fetch_data >> serialise_data >> check_counter >> aggregate_data >> notify_to_email
