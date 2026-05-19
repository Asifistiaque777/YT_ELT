from datawarehouse.data_utils import (
    get_conn_cursor,
    close_conn_cursor,
    create_schema,
    create_table,
    get_all_video_ids,
)
from datawarehouse.data_loading import load_data
from datawarehouse.data_modification import insert_rows, update_rows, delete_rows
from datawarehouse.data_transformation import transform_data

import logging
from airflow.decorators import task

logger = logging.getLogger(__name__)
table = "yt_api"

@task
def staging_table():
    schema = "staging"
    conn, cur = None, None
    try:
        create_schema(schema)
        create_table(schema)

        conn, cur = get_conn_cursor()
        YT_data = load_data()
        
        if not YT_data:
            logger.info("No data found to process.")
            return

        table_ids = set(get_all_video_ids(schema)) 

        for row in YT_data:
            if row["video_id"] in table_ids:
                update_rows(cur, conn, schema, row)
            else:
                insert_rows(cur, conn, schema, row)

        ids_in_json = {row["video_id"] for row in YT_data}
        ids_to_delete = table_ids - ids_in_json
        if ids_to_delete:
            delete_rows(cur, conn, schema, list(ids_to_delete))

        conn.commit()
        logger.info(f"{schema} table update successful!")
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Error in {schema}: {e}")
        raise e
    finally:
        if conn: close_conn_cursor(conn, cur)

@task
def core_table():
    schema = "core"
    conn, cur = None, None
    try:
        create_schema(schema)
        create_table(schema)

        conn, cur = get_conn_cursor()
        table_ids = set(get_all_video_ids(schema))

        cur.execute(f'SELECT video_id, title, published_at, duration, view_count, like_count, comment_count FROM staging.{table};')
        rows = cur.fetchall()

        current_staging_ids = set()
        for row in rows:
            transformed_row = transform_data(dict(row))
            v_id = transformed_row.get("video_id")
            if not v_id:
                continue
            current_staging_ids.add(v_id)
            if v_id in table_ids:
                update_rows(cur, conn, schema, transformed_row)
            else:
                insert_rows(cur, conn, schema, transformed_row)

        ids_to_delete = table_ids - current_staging_ids
        if ids_to_delete:
            delete_rows(cur, conn, schema, list(ids_to_delete))

        conn.commit()
        logger.info(f"{schema} table update successful!")
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Error in {schema}: {e}")
        raise e
    finally:
        if conn: close_conn_cursor(conn, cur)