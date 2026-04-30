import psycopg2
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import RealDictCursor

# টেবিলের নাম কনফিগারেশন
TABLE_NAME = "yt_api"

def get_conn_cursor():
    """এয়ারফ্লো কানেকশন আইডি ব্যবহার করে ডাটাবেসে কানেক্ট করা"""
    try:
        # নিশ্চিত করুন এয়ারফ্লো Admin > Connections এ 'postgres_db_elt' আইডিটি আছে
        hook = PostgresHook(postgres_conn_id="postgres_db_elt")
        conn = hook.get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        return conn, cur
    except Exception as e:
        print(f"FAILED to connect to Postgres: {e}")
        raise e

def close_conn_cursor(conn, cur):
    if cur: cur.close()
    if conn: conn.close()

def create_schema(schema):
    conn, cur = get_conn_cursor()
    try:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        conn.commit()
    finally:
        close_conn_cursor(conn, cur)

def create_table(schema):
    conn, cur = get_conn_cursor()
    # কলামের নামগুলো ছোট হাতের রাখা হয়েছে যাতে কুয়েরি করতে সুবিধা হয়
    columns_sql = """
        video_id VARCHAR(255) PRIMARY KEY,
        title TEXT,
        published_at TIMESTAMP,
        duration VARCHAR(50),
        view_count BIGINT,
        like_count BIGINT,
        comment_count BIGINT,
        video_type VARCHAR(50),
        inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """
    table_sql = f"CREATE TABLE IF NOT EXISTS {schema}.{TABLE_NAME} ({columns_sql});"
    try:
        cur.execute(table_sql)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        close_conn_cursor(conn, cur)

def get_all_video_ids(schema):
    conn, cur = None, None
    try:
        conn, cur = get_conn_cursor()
        # টেবিল আছে কি না চেক করা
        cur.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = '{schema}' AND table_name = '{TABLE_NAME}');")
        if not cur.fetchone()['exists']:
            return []
            
        cur.execute(f"SELECT video_id FROM {schema}.{TABLE_NAME};")
        rows = cur.fetchall()
        return [row['video_id'] for row in rows]
    except Exception as e:
        return []
    finally:
        if conn: close_conn_cursor(conn, cur)