import logging

logger = logging.getLogger(__name__)
table = "yt_api"

def insert_rows(cur, conn, schema, row):
    try:
        if schema == "staging":
            columns = '(video_id, title, published_at, duration, view_count, like_count, comment_count)'
            values = '(%(video_id)s, %(title)s, %(publishedAt)s, %(duration)s, %(viewCount)s, %(likeCount)s, %(commentCount)s)'
            update_set = """
                title = EXCLUDED.title,
                published_at = EXCLUDED.published_at,
                duration = EXCLUDED.duration,
                view_count = EXCLUDED.view_count,
                like_count = EXCLUDED.like_count,
                comment_count = EXCLUDED.comment_count
            """
            id_key = "video_id"
        else:
            columns = '(video_id, title, published_at, duration, video_type, view_count, like_count, comment_count)'
            values = '(%(video_id)s, %(title)s, %(published_at)s, %(duration)s, %(video_type)s, %(view_count)s, %(like_count)s, %(comment_count)s)'
            update_set = """
                title = EXCLUDED.title,
                published_at = EXCLUDED.published_at,
                duration = EXCLUDED.duration,
                video_type = EXCLUDED.video_type,
                view_count = EXCLUDED.view_count,
                like_count = EXCLUDED.like_count,
                comment_count = EXCLUDED.comment_count
            """
            id_key = "video_id"

        sql = f"""
            INSERT INTO {schema}.{table} {columns}
            VALUES {values}
            ON CONFLICT (video_id)
            DO UPDATE SET {update_set};
        """
        cur.execute(sql, row)
        conn.commit()
        logger.info(f"Upserted row in {schema}: {row[id_key]}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error in insert_rows ({schema}): {e}")
        raise e


def update_rows(cur, conn, schema, row):
    try:
        if schema == "staging":
            sql = f"""
                UPDATE {schema}.{table}
                SET title = %(title)s,
                    view_count = %(viewCount)s,
                    like_count = %(likeCount)s,
                    comment_count = %(commentCount)s
                WHERE video_id = %(video_id)s;
            """
        else:
            sql = f"""
                UPDATE {schema}.{table}
                SET title = %(title)s,
                    view_count = %(view_count)s,
                    like_count = %(like_count)s,
                    comment_count = %(comment_count)s
                WHERE video_id = %(video_id)s;
            """
        cur.execute(sql, row)
        conn.commit()
        logger.info(f"Updated row: {row.get('video_id')}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating row: {e}")
        raise e


def delete_rows(cur, conn, schema, ids_to_delete):
    if not ids_to_delete:
        return
    try:
        cur.execute(
            f'DELETE FROM {schema}.{table} WHERE video_id IN %s;',
            (tuple(ids_to_delete),)
        )
        conn.commit()
        logger.info(f"Deleted {len(ids_to_delete)} rows from {schema}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting rows: {e}")
        raise e