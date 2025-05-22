import re
import os
import datetime
import glob

def extract_json_from_text(text: str):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group()
    return None

def is_template_string(s: str) -> bool:
    try:
        s.format()
        return False
    except KeyError:
        return True
    
def extract_time(file_path):
    file_name = os.path.basename(file_path)
    time_str = file_name.split(".json")[0]
    return datetime.strptime(time_str, "%Y-%m-%d-%H-%M")

def find_latest_json(result_dir):
    pattern = os.path.join(result_dir, "*-*-*-*-*.json")
    files = glob.glob(pattern)
    if not files:
        print(f"Json file not found at {result_dir}")
        return None
    latest_file = max(files, key=extract_time)
    return latest_file