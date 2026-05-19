import os
import pytest
import psycopg2
from unittest import mock
from airflow.models import Variable, Connection, DagBag

# --- Airflow Variables Fixtures ---

@pytest.fixture
def api_key():
    mock_val = os.getenv("API_KEY", "MOCK_KEY1234")
    with mock.patch.dict("os.environ", AIRFLOW_VAR_API_KEY=mock_val):
        yield Variable.get("API_KEY")

@pytest.fixture
def channel_handle():
    mock_val = os.getenv("CHANNEL_HANDLE", "MRCHEESE")
    with mock.patch.dict("os.environ", AIRFLOW_VAR_CHANNEL_HANDLE=mock_val):
        yield Variable.get("CHANNEL_HANDLE")

# --- Airflow Connection Mock Fixture ---

@pytest.fixture
def mock_postgres_conn_vars():
    conn = Connection(
        conn_id="POSTGRES_DB_YT_ELT",
        conn_type="postgres",
        login="mock_username",
        password="mock_password",
        host="mock_host",
        port=5432,
        schema="mock_db_name",
    )
    conn_uri = conn.get_uri()

    with mock.patch.dict("os.environ", AIRFLOW_CONN_POSTGRES_DB_YT_ELT=conn_uri):
        yield Connection.get_connection_from_secrets(conn_id="POSTGRES_DB_YT_ELT")

# --- DAG Analysis Fixture ---

@pytest.fixture()
def dagbag():
    return DagBag(dag_folder='dags', include_examples=False)

@pytest.fixture()
def airflow_variable():
    def get_airflow_variable(variable_name):
        env_var = f"AIRFLOW_VAR_{variable_name.upper()}"
        return os.getenv(env_var)
    return get_airflow_variable


@pytest.fixture
def real_postgres_connection():
    dbname = os.getenv("ELT_DATABASE_NAME", "elt_db")
    user = os.getenv("ELT_DATABASE_USERNAME", "yt_api_user")
    password = os.getenv("ELT_DATABASE_PASSWORD", "X57tmQ846GYP3Jgb")
    host = os.getenv("POSTGRES_CONN_HOST", "postgres") 
    port = os.getenv("POSTGRES_CONN_PORT", "5432")

    conn = None
    try:
        conn = psycopg2.connect(
            dbname=dbname, 
            user=user, 
            password=password, 
            host=host, 
            port=port
        )
        yield conn
    except psycopg2.Error as e:
        pytest.fail(f"Could not connect to the real Postgres database: {e}")
    finally:
        if conn:
            conn.close()