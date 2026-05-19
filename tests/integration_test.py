import os
import requests
import pytest
import psycopg2

def test_youtube_api_response(airflow_variable):
    
    api_key = airflow_variable("API_KEY") 
    channel_handle = airflow_variable("CHANNEL_HANDLE")

    if not api_key:
        api_key = os.getenv("API_KEY") or os.getenv("AIRFLOW_VAR_API_KEY")
    if not channel_handle:
        channel_handle = os.getenv("CHANNEL_HANDLE") or os.getenv("AIRFLOW_VAR_CHANNEL_HANDLE")

    if not api_key or not channel_handle:
        pytest.fail(f"Environment variables missing! API_KEY: {'Found' if api_key else 'Missing'}, "
                    f"CHANNEL_HANDLE: {'Found' if channel_handle else 'Missing'}")

    url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={channel_handle}&key={api_key}"

    try:
        response = requests.get(url, timeout=10)
        assert response.status_code == 200, f"YouTube API returned {response.status_code}: {response.text}"
        print(f"\nSuccessfully connected to YouTube API for handle: {channel_handle}")
        
    except requests.RequestException as e:
        pytest.fail(f"YouTube API-তে রিকোয়েস্ট ব্যর্থ হয়েছে: {e}")

def test_real_postgres_connection(real_postgres_connection):
    cursor = None

    try:
        cursor = real_postgres_connection.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        assert result is not None, "Database returned no result."
        assert result[0] == 1, f"Expected 1, but got {result[0]}"
        print("\nSuccessfully connected to the Real Postgres database.")

    except psycopg2.Error as e:
        pytest.fail(f"ডাটাবেস কুয়েরি ব্যর্থ হয়েছে: {e}")

    finally:
        if cursor is not None:
            cursor.close()