import logging
from airflow.operators.bash import BashOperator

logger = logging.getLogger(__name__)

SODA_PATH = "/opt/airflow/include/soda"
DATASOURCE = "pg_datasource"

def yt_elt_data_quality(schema):
    """
    SODA স্ক্যান রান করার জন্য একটি BashOperator তৈরি করে।
    """
    # try-except বাদ দেওয়া হয়েছে কারণ অপারেটর ডিক্লারেশনে এটি দরকার নেই
    return BashOperator(
        task_id=f"soda_test_{schema}",
        # -v SCHEMA={schema} ব্যবহার করা হয়েছে যা একটি ভালো প্র্যাকটিস
        bash_command=f"soda scan -d {DATASOURCE} -c {SODA_PATH}/configuration.yml -v SCHEMA={schema} {SODA_PATH}/checks.yml",
    )