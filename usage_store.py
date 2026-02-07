from collections import defaultdict
from datetime import datetime
import time
usage_data = {}
total_usage = {}
RATE_LIMIT = 5
WINDOW_SECONDS = 60

def check_rate_limit(api_key: str) -> bool:
    now = time.time()
    window_start = now - WINDOW_SECONDS
    
    if api_key not in usage_data:
        usage_data[api_key] = []
    
    usage_data[api_key] = [t for t in usage_data[api_key] if t > window_start]
    
    if len(usage_data[api_key]) >= RATE_LIMIT:
        return False
    
    usage_data[api_key].append(now)
    total_usage[api_key] = total_usage.get(api_key,0) + 1
    return True

def get_usage_stats():
    return total_usage