from airflow import DAG
import pendulum
from datetime import datetime, timedelta
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

# আপনার কাস্টম মডিউলগুলো ইমপোর্ট করা হচ্ছে
from api.video_stats import (
    get_playlist_id,
    get_video_ids,
    extract_video_data,
    save_to_json,
)

from datawarehouse.dwh import staging_table, core_table
from dataquality.soda import yt_elt_data_quality

# টাইমজোন সেটআপ
local_tz = pendulum.timezone("Europe/Malta")

# Default Args
default_args = {
    "owner": "dataengineers",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "email": "data@engineers.com",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "max_active_runs": 1,
    "dagrun_timeout": timedelta(hours=1),
    "start_date": datetime(2025, 1, 1, tzinfo=local_tz),
}

# ভেরিয়েবল (স্কিমা নামগুলো এখানে ডিফাইন করা ভালো)
staging_schema = "staging"
core_schema = "core"

# --- DAG 1: produce_json ---
with DAG(
    dag_id="produce_json",
    default_args=default_args,
    description="DAG to produce JSON file with raw data",
    schedule="0 14 * * *",
    catchup=False,
    tags=['youtube', 'raw_data'],
) as dag_produce:

    playlist_id_task = get_playlist_id()
    video_ids_task = get_video_ids(playlist_id_task)
    extract_data_task = extract_video_data(video_ids_task)
    save_to_json_task = save_to_json(extract_data_task)

    trigger_update_db = TriggerDagRunOperator(
        task_id="trigger_update_db",
        trigger_dag_id="update_db",
        wait_for_completion=True, # এটি দিলে প্রথম DAG শেষ না হওয়া পর্যন্ত দ্বিতীয়টি শুরু হবে না
    )

    playlist_id_task >> video_ids_task >> extract_data_task >> save_to_json_task >> trigger_update_db


# --- DAG 2: update_db ---
with DAG(
    dag_id="update_db",
    default_args=default_args,
    description="DAG to process JSON and insert data into DB",
    catchup=False,
    schedule=None,
    tags=['youtube', 'dwh'],
) as dag_update:

    update_staging_task = staging_table()
    update_core_task = core_table()

    trigger_data_quality = TriggerDagRunOperator(
        task_id="trigger_data_quality",
        trigger_dag_id="data_quality",
        wait_for_completion=True,
    )

    update_staging_task >> update_core_task >> trigger_data_quality


# --- DAG 3: data_quality ---
with DAG(
    dag_id="data_quality",
    default_args=default_args,
    description="DAG to check data quality using Soda",
    catchup=False,
    schedule=None,
    tags=['youtube', 'quality_check'],
) as dag_quality:

    # এখানে স্কিমা অনুযায়ী টাস্ক ডিফাইন করা হয়েছে
    soda_validate_staging = yt_elt_data_quality(staging_schema)
    soda_validate_core = yt_elt_data_quality(core_schema)

    soda_validate_staging >> soda_validate_core