"""Simple caching for API calls"""

import functools
import hashlib
import json
import time
from pathlib import Path

CACHE_DIR = Path(".cache")
CACHE_TTL = 3600  # 1 hour


def cached(ttl=CACHE_TTL):
    """Cache function results to disk"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            CACHE_DIR.mkdir(exist_ok=True)

            # Create cache key from function name and args
            key_data = f"{func.__name__}:{args}:{kwargs}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            cache_file = CACHE_DIR / f"{cache_key}.json"

            # Check cache
            if cache_file.exists():
                cache_data = json.loads(cache_file.read_text())
                if time.time() - cache_data["timestamp"] < ttl:
                    return cache_data["result"]

            # Call function and cache result
            result = func(*args, **kwargs)
            cache_file.write_text(json.dumps({"timestamp": time.time(), "result": result}))
            return result

        return wrapper

    return decorator
