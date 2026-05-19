import pytest
from airflow.models import DagBag

def test_api_key(api_key):
    assert api_key == "MOCK_KEY1234"

def test_channel_handle(channel_handle):
    assert channel_handle == "MRCHEESE"

def test_postgres_conn(mock_postgres_conn_vars):
    conn = mock_postgres_conn_vars
    assert conn.login == "mock_username"
    assert conn.password == "mock_password"
    assert conn.host == "mock_host"
    assert conn.port == 5432  
    assert conn.schema == "mock_db_name"

def test_dags_integrity(dagbag):
    
    assert dagbag.import_errors == {}, f"DAG ইমপোর্টে এরর পাওয়া গেছে: {dagbag.import_errors}"

    expected_dag_ids = ["produce_json", "update_db", "data_quality"]
    loaded_dag_ids = list(dagbag.dags.keys())
    
    for dag_id in expected_dag_ids:
        assert dag_id in loaded_dag_ids, f"DAG {dag_id} ড্যাগব্যাগে খুঁজে পাওয়া যায়নি।"

    assert dagbag.size() == 3, f"আশা করা হয়েছিল ৩টি ড্যাগ, কিন্তু পাওয়া গেছে {dagbag.size()}টি।"

    
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