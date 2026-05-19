from datetime import timedelta, datetime
import re

def parse_duration(duration_str):
    pattern = re.compile(r'P(?:(?P<days>\d+)D)?T?(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?')
    match = pattern.match(duration_str)
    if not match:
        return timedelta(0)
    parts = {k: int(v) if v else 0 for k, v in match.groupdict().items()}
    return timedelta(**parts)

def transform_data(row):
    duration_str = row.get("duration") or row.get("Duration", "PT0S")
    duration_td = parse_duration(duration_str)
    
    row["duration"] = str((datetime.min + duration_td).time())
    row["video_type"] = "Shorts" if duration_td.total_seconds() <= 60 else "Normal"
    
    return row