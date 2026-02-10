from config import get_db_connection
from utils import parse_duration, detect_language, calculate_engagement_rate, is_shorts
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

def create_or_get_topic(keyword, cur):
    """Create topic or return existing one - uses provided cursor"""
    cur.execute("""
        INSERT INTO topics (main_keyword)
        VALUES (%s)
        ON CONFLICT DO NOTHING
        RETURNING id
    """, (keyword,))

    result = cur.fetchone()
    if result:
        return result['id']

    # Topic already exists, fetch it
    cur.execute("SELECT id FROM topics WHERE main_keyword = %s", (keyword,))
    return cur.fetchone()['id']

def insert_channel(channel_data, cur):
    """
    Insert or update channel using provided cursor
    Returns internal DB channel ID
    """
    snippet = channel_data['snippet']
    stats = channel_data.get('statistics', {})

    cur.execute("""
        INSERT INTO channels (
            youtube_channel_id, channel_name, channel_url, last_scraped_at
        ) VALUES (%s, %s, %s, NOW())
        ON CONFLICT (youtube_channel_id)
        DO UPDATE SET
            channel_name = EXCLUDED.channel_name,
            last_scraped_at = NOW()
        RETURNING id
    """, (
        channel_data['id'],
        snippet.get('title'),
        f"https://youtube.com/channel/{channel_data['id']}"
    ))

    channel_id = cur.fetchone()['id']

    # ALWAYS insert new metrics record (never update - we want history!)
    if stats:
        cur.execute("""
            INSERT INTO channel_metrics_history (
                channel_id, subscribers, total_views, video_count
            ) VALUES (%s, %s, %s, %s)
        """, (
            channel_id,
            int(stats.get('subscriberCount', 0)),
            int(stats.get('viewCount', 0)),
            int(stats.get('videoCount', 0))
        ))

    return channel_id

def insert_video(video_data, channel_id, topic_id, search_query, search_position, cur):
    """
    Insert video with all related data using provided cursor
    Returns internal DB video ID
    """
    snippet = video_data['snippet']
    content = video_data['contentDetails']
    stats = video_data.get('statistics', {})

    # Parse duration and detect shorts
    duration_str = content.get('duration', 'PT0S')
    duration_seconds = parse_duration(duration_str)
    is_shorts_flag = is_shorts(duration_seconds)

    # Detect language from title + description
    text_for_lang = f"{snippet.get('title', '')} {snippet.get('description', '')}"
    detected_language = snippet.get('defaultLanguage') or detect_language(text_for_lang)

    # Insert or update video
    cur.execute("""
        INSERT INTO videos (
            youtube_video_id, channel_id, title, description,
            published_at, duration_seconds, is_shorts,
            thumbnail_url, language, raw_json,
            discovered_via_query, search_position,
            first_seen_at, last_updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (youtube_video_id)
        DO UPDATE SET
            last_updated_at = NOW(),
            title = EXCLUDED.title,
            description = EXCLUDED.description
        RETURNING id
    """, (
        video_data['id'],
        channel_id,
        snippet.get('title'),
        snippet.get('description'),
        snippet.get('publishedAt'),
        duration_seconds,
        is_shorts_flag,
        snippet.get('thumbnails', {}).get('high', {}).get('url'),
        detected_language,
        json.dumps(video_data),
        search_query,
        search_position
    ))

    video_id = cur.fetchone()['id']

    # Link video to topic
    cur.execute("""
        INSERT INTO topic_videos (topic_id, video_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (topic_id, video_id))

    # Insert tags with conflict handling
    tags = snippet.get('tags', [])
    for tag in tags:
        cur.execute("""
            INSERT INTO video_tags (video_id, tag)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (video_id, tag))

    # ALWAYS insert new metrics (we want history, not updates!)
    engagement_rate = calculate_engagement_rate(stats)

    cur.execute("""
        INSERT INTO video_metrics_history (
            video_id, view_count, like_count, comment_count,
            collection_source
        ) VALUES (%s, %s, %s, %s, %s)
    """, (
        video_id,
        int(stats.get('viewCount', 0)),
        int(stats.get('likeCount', 0)),
        int(stats.get('commentCount', 0)),
        'search'
    ))

    logger.debug(f"Inserted video: {snippet.get('title')[:50]}... (ID: {video_id})")

    return video_id

def insert_transcript(video_id, transcript_text, cur):
    """Update video with transcript"""
    if transcript_text:
        cur.execute("""
            UPDATE videos
            SET transcript = %s
            WHERE id = %s
        """, (transcript_text, video_id))
        logger.debug(f"Added transcript for video {video_id}")

def insert_comments_batch(video_id, comments_data, cur):
    """
    Insert comments in batch using provided cursor
    Returns count of inserted comments
    """
    inserted = 0

    for comment_item in comments_data:
        comment = comment_item['snippet']['topLevelComment']['snippet']

        try:
            cur.execute("""
                INSERT INTO comments (
                    video_id, youtube_comment_id, comment_text,
                    likes, published_at
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (youtube_comment_id) DO NOTHING
            """, (
                video_id,
                comment_item['id'],
                comment.get('textDisplay'),
                comment.get('likeCount', 0),
                comment.get('publishedAt')
            ))
            inserted += 1
        except Exception as e:
            logger.warning(f"Failed to insert comment: {e}")

    return inserted

def log_api_usage(endpoint, quota_cost, cur):
    """Track API quota usage using provided cursor"""
    cur.execute("""
        INSERT INTO api_quota_usage (endpoint, quota_cost)
        VALUES (%s, %s)
    """, (endpoint, quota_cost))

def get_daily_quota_usage():
    """Check total quota used today - opens its own connection"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(SUM(quota_cost), 0) as total
                FROM api_quota_usage
                WHERE (requested_at AT TIME ZONE 'UTC')::DATE = CURRENT_DATE
            """)
            return cur.fetchone()['total']

def mark_video_as_deleted(youtube_video_id, cur):
    """Mark a video as deleted when API returns 404 or video is unavailable"""
    cur.execute("""
        UPDATE videos
        SET deleted_at = NOW()
        WHERE youtube_video_id = %s AND deleted_at IS NULL
    """, (youtube_video_id,))

    if cur.rowcount > 0:
        logger.info(f"Marked video {youtube_video_id} as deleted")

def create_scrape_job(topic_id, keyword, cur):
    """Create a new scrape job and return its ID"""
    cur.execute("""
        INSERT INTO scrape_jobs (
            topic_id, keyword, status, started_at
        ) VALUES (%s, %s, 'running', NOW())
        RETURNING id
    """, (topic_id, keyword))

    return cur.fetchone()['id']

def update_scrape_job(job_id, status, videos_found=0, error_message=None, cur=None):
    """Update scrape job status"""
    if cur is None:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                _update_scrape_job_query(job_id, status, videos_found, error_message, cur)
    else:
        _update_scrape_job_query(job_id, status, videos_found, error_message, cur)

def _update_scrape_job_query(job_id, status, videos_found, error_message, cur):
    """Internal helper for scrape job update"""
    cur.execute("""
        UPDATE scrape_jobs
        SET status = %s,
            videos_found = %s,
            error_message = %s,
            completed_at = CASE WHEN %s IN ('completed', 'failed') THEN NOW() ELSE NULL END
        WHERE id = %s
    """, (status, videos_found, error_message, status, job_id))
