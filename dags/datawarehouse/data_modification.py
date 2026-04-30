import logging

logger = logging.getLogger(__name__)
table = "yt_api"
def insert_rows(cur, conn, schema, row):
    try:
        # ১. স্কিমা অনুযায়ী কলাম ম্যাপিং এবং ডিকশনারি কি (Key) সেট করা
        if schema == "staging":
            # জেসন ফাইল থেকে সরাসরি আসা কি (Keys)
            mapping = {
                "id": "video_id", "title": "title", "date": "publishedAt",
                "duration": "duration", "views": "viewCount", 
                "likes": "likeCount", "comments": "commentCount"
            }
            # ON CONFLICT আপডেট করার সময় Video_Type নেই কারণ স্ট্যাজিংয়ে এটি থাকে না
            update_set = """
                "Video_Title" = EXCLUDED."Video_Title",
                "Upload_Date" = EXCLUDED."Upload_Date",
                "Duration" = EXCLUDED."Duration",
                "Video_Views" = EXCLUDED."Video_Views",
                "Likes_Count" = EXCLUDED."Likes_Count",
                "Comments_Count" = EXCLUDED."Comments_Count"
            """
            columns = '("Video_ID", "Video_Title", "Upload_Date", "Duration", "Video_Views", "Likes_Count", "Comments_Count")'
            values = f"(%({mapping['id']})s, %({mapping['title']})s, %({mapping['date']})s, %({mapping['duration']})s, %({mapping['views']})s, %({mapping['likes']})s, %({mapping['comments']})s)"
        

        else:
            # কোর টেবিলের জন্য ট্রান্সফর্ম করা কি (Keys)
            mapping = {"id": "Video_ID"} # কোর-এ কি এবং কলাম একই হয়
            update_set = """
                "Video_Title" = EXCLUDED."Video_Title",
                "Upload_Date" = EXCLUDED."Upload_Date",
                "Duration" = EXCLUDED."Duration",
                "Video_Type" = EXCLUDED."Video_Type",
                "Video_Views" = EXCLUDED."Video_Views",
                "Likes_Count" = EXCLUDED."Likes_Count",
                "Comments_Count" = EXCLUDED."Comments_Count"
            """
            columns = '("Video_ID", "Video_Title", "Upload_Date", "Duration", "Video_Type", "Video_Views", "Likes_Count", "Comments_Count")'
            values = "(%(Video_ID)s, %(Video_Title)s, %(Upload_Date)s, %(Duration)s, %(Video_Type)s, %(Video_Views)s, %(Likes_Count)s, %(Comments_Count)s)"

        # ২. UPSERT কমান্ড (INSERT + ON CONFLICT DO UPDATE)
        sql = f"""
            INSERT INTO {schema}.{table} {columns}
            VALUES {values}
            ON CONFLICT ("Video_ID") 
            DO UPDATE SET {update_set};
        """
        
        cur.execute(sql, row)
        conn.commit()
        logger.info(f"Upserted (Insert/Update) row in {schema}: {row[mapping['id']]}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error in insert_rows ({schema}): {e}")
        raise e

def update_rows(cur, conn, schema, row):
    """
    দ্রষ্টব্য: উপরের insert_rows এখন নিজেই আপডেট হ্যান্ডেল করতে পারে (Upsert)। 
    তারপরেও যদি আলাদাভাবে আপডেট দরকার হয়, তবে এই ফাংশন ব্যবহার করুন।
    """
    try:
        if schema == "staging":
            mapping = {"id": "video_id", "title": "title", "views": "viewCount", "likes": "likeCount", "comments": "commentCount"}
        else:
            mapping = {"id": "Video_ID", "title": "Video_Title", "views": "Video_Views", "likes": "Likes_Count", "comments": "Comments_Count"}

        cur.execute(
            f"""
            UPDATE {schema}.{table}
            SET "Video_Title" = %({mapping['title']})s,
                "Video_Views" = %({mapping['views']})s, 
                "Likes_Count" = %({mapping['likes']})s, 
                "Comments_Count" = %({mapping['comments']})s
            WHERE "Video_ID" = %({mapping['id']})s;
            """,
            row,
        )
        conn.commit()
        logger.info(f"Updated row with Video_ID: {row[mapping['id']]}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating row: {e}")
        raise e

def delete_rows(cur, conn, schema, ids_to_delete):
    if not ids_to_delete:
        return
    try:
        cur.execute(
            f'DELETE FROM {schema}.{table} WHERE "Video_ID" IN %s;',
            (tuple(ids_to_delete),)
        )
        conn.commit()
        logger.info(f"Deleted {len(ids_to_delete)} rows from {schema}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting rows: {e}")
        raise e