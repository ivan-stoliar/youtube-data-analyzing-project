import time
import re
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries=3, base_delay=1):
    """
    Decorator for exponential backoff retry logic
    Handles YouTube API temporary failures
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts: {e}")
                        raise

                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)

        return wrapper
    return decorator

def parse_duration(duration_str):
    """
    Convert YouTube duration (PT15M33S) to seconds
    Examples:
        PT15M33S -> 933
        PT1H2M10S -> 3730
        PT45S -> 45
    """
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)

    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds

def detect_language(text):
    """
    Detect language from text using langdetect
    Falls back to 'unknown' if detection fails
    """
    try:
        from langdetect import detect
        return detect(text)
    except:
        return 'unknown'

def calculate_engagement_rate(stats):
    """
    Calculate engagement rate: (likes + comments) / views
    Returns 0 if views are 0 to avoid division by zero
    """
    views = int(stats.get('viewCount', 0))
    if views == 0:
        return 0.0

    likes = int(stats.get('likeCount', 0))
    comments = int(stats.get('commentCount', 0))

    return round((likes + comments) / views, 4)

def is_shorts(duration_seconds):
    """Detect if video is a Short (< 60 seconds)"""
    return duration_seconds < 60

def batch_list(items, batch_size=50):
    """Split a list into chunks of specified size"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]
