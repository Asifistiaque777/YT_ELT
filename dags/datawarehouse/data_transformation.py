from datetime import timedelta, datetime
import re

def parse_duration(duration_str):
    """
    ISO 8601 duration (e.g., PT1M30S, PT1H, P1DT2H) পার্স করার জন্য 
    রেগুলার এক্সপ্রেশন ব্যবহার করা সবচেয়ে নিরাপদ।
    """
    # Regex pattern: দিন, ঘণ্টা, মিনিট এবং সেকেন্ড আলাদা করার জন্য
    pattern = re.compile(r'P(?:(?P<days>\d+)D)?T?(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?')
    match = pattern.match(duration_str)
    
    if not match:
        return timedelta(0)

    # গ্রুপগুলো থেকে ভ্যালু নিয়ে ইন্টিজারে রূপান্তর (না থাকলে ০)
    parts = {k: int(v) if v else 0 for k, v in match.groupdict().items()}
    
    return timedelta(**parts)


def transform_data(row):
    # ১. ডিউরেশন পার্স করা
    duration_td = parse_duration(row["Duration"])

    # ২. ডিউরেশনকে HH:MM:SS ফরম্যাটে নেওয়া (ডাটাবেসে সেভ করার সুবিধার জন্য)
    # datetime.min + duration_td ব্যবহার করলে টাইম অবজেক্ট পাওয়া যায়
    row["Duration"] = str((datetime.min + duration_td).time())

    # ৩. ভিডিও টাইপ নির্ধারণ (৬০ সেকেন্ড বা তার কম হলে Shorts)
    row["Video_Type"] = "Shorts" if duration_td.total_seconds() <= 60 else "Normal"

    return row