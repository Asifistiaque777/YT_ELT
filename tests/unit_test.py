import pytest
from airflow.models import DagBag

# --- ১. ভেরিয়েবল এবং হ্যান্ডেল টেস্ট ---
def test_api_key(api_key):
    """চেক করে যে মক এপিআই কী সঠিকভাবে লোড হচ্ছে কি না"""
    assert api_key == "MOCK_KEY1234"

def test_channel_handle(channel_handle):
    """চেক করে যে মক চ্যানেল হ্যান্ডেল সঠিকভাবে কাজ করছে কি না"""
    assert channel_handle == "MRCHEESE"

# --- ২. ডাটাবেস কানেকশন মক টেস্ট ---
def test_postgres_conn(mock_postgres_conn_vars):
    """এয়ারফ্লো কানেকশন ভেরিয়েবলগুলো মক লোকেশন থেকে রিড করছে কি না তা নিশ্চিত করে"""
    conn = mock_postgres_conn_vars
    assert conn.login == "mock_username"
    assert conn.password == "mock_password"
    assert conn.host == "mock_host"
    assert conn.port == 5432  # আপনার মক সেটআপ অনুযায়ী পোর্ট চেক করুন
    assert conn.schema == "mock_db_name"

# --- ৩. ড্যাগ ইনটেগ্রিটি এবং টাস্ক কাউন্ট টেস্ট ---
def test_dags_integrity(dagbag):
    """পুরো ড্যাগব্যাগ এবং এর ভেতরের টাস্কগুলো চেক করে"""
    
    # ১. ইমপোর্ট এরর চেক (কোনো ড্যাগ কি লোড হতে ব্যর্থ হয়েছে?)
    assert dagbag.import_errors == {}, f"DAG ইমপোর্টে এরর পাওয়া গেছে: {dagbag.import_errors}"

    # ২. প্রত্যাশিত সব ড্যাগ আইডি লোড হয়েছে কি না
    expected_dag_ids = ["produce_json", "update_db", "data_quality"]
    loaded_dag_ids = list(dagbag.dags.keys())
    
    for dag_id in expected_dag_ids:
        assert dag_id in loaded_dag_ids, f"DAG {dag_id} ড্যাগব্যাগে খুঁজে পাওয়া যায়নি।"

    # ৩. টোটাল ড্যাগ সংখ্যা চেক
    assert dagbag.size() == 3, f"আশা করা হয়েছিল ৩টি ড্যাগ, কিন্তু পাওয়া গেছে {dagbag.size()}টি।"

    # ৪. ড্যাগ অনুযায়ী টাস্ক কাউন্ট চেক
    # আপনার main.py কোড অনুযায়ী কাউন্ট:
    # produce_json: playlist_id, video_ids, extract_data, save_to_json, trigger_update_db = 5
    # update_db: update_staging, update_core, trigger_data_quality = 3
    # data_quality: soda_validate_staging, soda_validate_core = 2
    
    expected_task_counts = {
        "produce_json": 5,
        "update_db": 3,
        "data_quality": 2,
    }

    for dag_id, dag in dagbag.dags.items():
        if dag_id in expected_task_counts:
            expected_count = expected_task_counts[dag_id]
            actual_count = len(dag.tasks)
            assert actual_count == expected_count, (
                f"DAG '{dag_id}' এ টাস্ক সংখ্যা {actual_count}, "
                f"কিন্তু আশা করা হয়েছিল {expected_count}টি।"
            )
            print(f"Verified {dag_id}: {actual_count} tasks.")