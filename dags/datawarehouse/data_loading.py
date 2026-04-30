import json
import os
from datetime import date 
import logging 

# লগিং সেটআপ
logger = logging.getLogger(__name__)

def load_data():
    """
    আজকের তারিখের JSON ফাইলটি লোড করে পাইথন ডিকশনারি হিসেবে রিটার্ন করে।
    """
    # ডকার কন্টেইনারের মাউন্টেড পাথ ব্যবহার করা নিরাপদ
    base_path = "/opt/airflow/data"
    file_name = f"YT_data_{date.today()}.json"
    file_path = os.path.join(base_path, file_name)

    try:
        # ফাইলটি আসলে আছে কি না চেক করা
        if not os.path.exists(file_path):
            logger.error(f"File not found at: {file_path}")
            raise FileNotFoundError(f"আজকের জন্য কোনো ডাটা ফাইল পাওয়া যায়নি: {file_path}")

        logger.info(f"Processing file: {file_name}")
        
        with open(file_path, 'r', encoding='utf-8') as raw_data:
            data = json.load(raw_data)
            
        # ডাটা সফলভাবে লোড হলে কতগুলো রেকর্ড আছে তা জানানো
        logger.info(f"Successfully loaded {len(data)} records from JSON.")
        return data 

    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in file {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading data: {e}")
        raise

# টেস্ট করার জন্য (Optional)
if __name__ == "__main__":
    try:
        my_data = load_data()
        print(my_data[0]) # প্রথম রেকর্ডটি প্রিন্ট করে দেখা
    except Exception:
        pass