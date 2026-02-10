from youtube_client import YouTubeClient
from db_manager import (
    create_or_get_topic, insert_channel, insert_video,
    insert_transcript, insert_comments_batch, log_api_usage,
    get_daily_quota_usage, create_scrape_job, update_scrape_job
)
from config import get_persistent_connection, QUOTA_LIMIT
import logging

logger = logging.getLogger(__name__)

class YouTubeScraper:
    def __init__(self):
        self.client = YouTubeClient()
        self.quota_limit = QUOTA_LIMIT

    def scrape_by_keyword(self, keyword, max_videos=100, fetch_transcripts=False, fetch_comments=False):
        """
        Main scraping function with persistent DB connection

        Args:
            keyword: Search keyword
            max_videos: Maximum videos to scrape
            fetch_transcripts: Whether to fetch video transcripts (slow!)
            fetch_comments: Whether to fetch comments (quota-expensive!)
        """
        conn = None
        cur = None
        job_id = None

        try:
            # Check quota before starting
            used = get_daily_quota_usage()
            logger.info(f"📊 Quota used today: {used}/{self.quota_limit}")

            if used >= self.quota_limit:
                logger.error("⚠️  Daily quota exceeded!")
                return

            # Persistent connection for batch operations
            conn = get_persistent_connection()
            cur = conn.cursor()

            # Create or get topic
            topic_id = create_or_get_topic(keyword, cur)
            conn.commit()
            logger.info(f"🎯 Topic: {keyword} (ID: {topic_id})")

            # Create scrape job
            job_id = create_scrape_job(topic_id, keyword, cur)
            conn.commit()
            logger.info(f"📝 Created scrape job ID: {job_id}")

            # Search videos
            logger.info(f"🔍 Searching for: {keyword}")
            search_result = self.client.search_videos(keyword, max_results=max_videos)
            search_items = search_result['items']

            # Log API usage
            log_api_usage('search', search_result['quota_cost'], cur)
            conn.commit()

            if not search_items:
                logger.warning("No results found")
                update_scrape_job(job_id, 'completed', 0, cur=cur)
                conn.commit()
                return

            video_ids = [item['id']['videoId'] for item in search_items]
            logger.info(f"✅ Found {len(video_ids)} videos")

            # Get detailed video data
            logger.info("📥 Fetching video details...")
            videos_result = self.client.get_video_details(video_ids)
            videos = videos_result['items']

            log_api_usage('videos', videos_result['quota_cost'], cur)
            conn.commit()

            # Get unique channel IDs
            channel_ids = list(set([v['snippet']['channelId'] for v in videos]))
            logger.info(f"📺 Found {len(channel_ids)} unique channels")

            # Get channel data
            logger.info("📥 Fetching channel details...")
            channels_result = self.client.get_channel_details(channel_ids)
            channels = channels_result['items']

            log_api_usage('channels', channels_result['quota_cost'], cur)
            conn.commit()

            # Create channel lookup
            channel_map = {}
            for channel_data in channels:
                db_channel_id = insert_channel(channel_data, cur)
                channel_map[channel_data['id']] = db_channel_id

            conn.commit()
            logger.info(f"💾 Inserted {len(channel_map)} channels")

            # Insert videos
            logger.info("💾 Inserting videos...")
            videos_inserted = 0

            for position, video_data in enumerate(videos, 1):
                yt_channel_id = video_data['snippet']['channelId']
                db_channel_id = channel_map.get(yt_channel_id)

                if db_channel_id:
                    video_id = insert_video(
                        video_data,
                        db_channel_id,
                        topic_id,
                        keyword,
                        position,
                        cur
                    )
                    videos_inserted += 1

                    # Optional: Fetch transcript
                    if fetch_transcripts:
                        transcript = self.client.get_video_transcript(video_data['id'])
                        if transcript:
                            insert_transcript(video_id, transcript, cur)

                    # Optional: Fetch comments (expensive!)
                    if fetch_comments:
                        total_comments = 0
                        for comment_batch in self.client.get_video_comments_generator(video_data['id'], max_results=100):
                            batch_count = insert_comments_batch(video_id, comment_batch['items'], cur)
                            total_comments += batch_count
                            log_api_usage('comments', comment_batch['quota_cost'], cur)

                        if total_comments > 0:
                            logger.info(f"  💬 Inserted {total_comments} comments")

                # Commit every 10 videos to avoid huge transactions
                if videos_inserted % 10 == 0:
                    conn.commit()
                    logger.info(f"  Progress: {videos_inserted}/{len(videos)} videos")

            # Final commit
            conn.commit()

            # Update scrape job
            update_scrape_job(job_id, 'completed', videos_inserted, cur=cur)
            conn.commit()

            logger.info(f"✨ Done! Scraped {videos_inserted} videos")
            logger.info(f"📊 New quota usage: {get_daily_quota_usage()}/{self.quota_limit}")

        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}", exc_info=True)
            if conn:
                conn.rollback()
            if job_id and cur:
                update_scrape_job(job_id, 'failed', 0, str(e), cur=cur)
                try:
                    conn.commit()
                except:
                    pass
            raise

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def scrape_by_channel(self, channel_id, topic_keyword=None, max_videos=50):
        """
        Scrape all videos from a specific channel

        Args:
            channel_id: YouTube channel ID
            topic_keyword: Optional topic to associate videos with
            max_videos: Max videos to fetch
        """
        conn = None
        cur = None

        try:
            conn = get_persistent_connection()
            cur = conn.cursor()

            # Get channel details
            logger.info(f"📺 Fetching channel: {channel_id}")
            channel_result = self.client.get_channel_details([channel_id])

            if not channel_result['items']:
                logger.error("Channel not found")
                return

            channel_data = channel_result['items'][0]
            db_channel_id = insert_channel(channel_data, cur)
            conn.commit()

            log_api_usage('channels', channel_result['quota_cost'], cur)
            conn.commit()

            # Search videos from this channel
            search_result = self.client.search_videos(
                query='',
                max_results=max_videos,
                order='date'  # Get latest videos
            )

            # Filter only videos from this channel
            channel_videos = [
                item for item in search_result['items']
                if item['snippet']['channelId'] == channel_id
            ]

            logger.info(f"✅ Found {len(channel_videos)} videos from channel")

            # Get video details and insert
            video_ids = [item['id']['videoId'] for item in channel_videos]
            videos_result = self.client.get_video_details(video_ids)

            topic_id = None
            if topic_keyword:
                topic_id = create_or_get_topic(topic_keyword, cur)
                conn.commit()

            for position, video_data in enumerate(videos_result['items'], 1):
                insert_video(
                    video_data,
                    db_channel_id,
                    topic_id,
                    f"channel:{channel_id}",
                    position,
                    cur
                )

            conn.commit()
            logger.info(f"✨ Scraped {len(videos_result['items'])} videos from channel")

        except Exception as e:
            logger.error(f"❌ Channel scraping failed: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
