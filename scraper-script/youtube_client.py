from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import YOUTUBE_API_KEY
from utils import retry_with_backoff, batch_list
import time
import logging

logger = logging.getLogger(__name__)

class YouTubeClient:
    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    @retry_with_backoff(max_retries=3)
    def search_videos(self, query, max_results=50, published_after=None, order='relevance'):
        """
        Search for videos by keyword

        Args:
            query: Search term
            max_results: Number of results (max 50 per call)
            published_after: ISO 8601 timestamp (e.g., '2024-01-01T00:00:00Z')
            order: 'relevance', 'date', 'viewCount', 'rating'

        Returns:
            List of video items with quota cost
        """
        try:
            request = self.youtube.search().list(
                q=query,
                part='id,snippet',
                type='video',
                maxResults=min(max_results, 50),
                publishedAfter=published_after,
                order=order
            )
            response = request.execute()

            items = response.get('items', [])
            logger.info(f"Search '{query}': found {len(items)} videos (quota: 100)")

            return {
                'items': items,
                'quota_cost': 100
            }

        except HttpError as e:
            logger.error(f"YouTube API Error in search: {e}")
            return {'items': [], 'quota_cost': 100}

    @retry_with_backoff(max_retries=3)
    def get_video_details(self, video_ids):
        """
        Get detailed info for videos (batched in chunks of 50)

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            Dict with videos list and total quota cost
        """
        if not video_ids:
            return {'items': [], 'quota_cost': 0}

        try:
            all_videos = []
            total_quota = 0

            for chunk in batch_list(video_ids, 50):
                request = self.youtube.videos().list(
                    part='snippet,contentDetails,statistics',
                    id=','.join(chunk)
                )
                response = request.execute()
                all_videos.extend(response.get('items', []))
                total_quota += 1

                time.sleep(0.1)  # Rate limiting

            logger.info(f"Fetched details for {len(all_videos)} videos (quota: {total_quota})")

            return {
                'items': all_videos,
                'quota_cost': total_quota
            }

        except HttpError as e:
            logger.error(f"YouTube API Error in video details: {e}")
            return {'items': [], 'quota_cost': total_quota}

    @retry_with_backoff(max_retries=3)
    def get_channel_details(self, channel_ids):
        """
        Get channel info (batched in chunks of 50)

        Args:
            channel_ids: List of YouTube channel IDs

        Returns:
            Dict with channels list and total quota cost
        """
        if not channel_ids:
            return {'items': [], 'quota_cost': 0}

        try:
            all_channels = []
            total_quota = 0

            for chunk in batch_list(channel_ids, 50):
                request = self.youtube.channels().list(
                    part='snippet,statistics',
                    id=','.join(chunk)
                )
                response = request.execute()
                all_channels.extend(response.get('items', []))
                total_quota += 1

                time.sleep(0.1)

            logger.info(f"Fetched details for {len(all_channels)} channels (quota: {total_quota})")

            return {
                'items': all_channels,
                'quota_cost': total_quota
            }

        except HttpError as e:
            logger.error(f"YouTube API Error in channel details: {e}")
            return {'items': [], 'quota_cost': total_quota}

    def get_video_comments_generator(self, video_id, max_results=100):
        """
        Generator that yields comments in batches to avoid memory issues
        Use this for videos with thousands of comments

        Args:
            video_id: YouTube video ID
            max_results: Total comments to fetch

        Yields:
            Batches of comment items
        """
        try:
            next_page_token = None
            fetched = 0
            quota_used = 0

            while fetched < max_results:
                request = self.youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=min(100, max_results - fetched),
                    pageToken=next_page_token,
                    order='relevance'
                )

                try:
                    response = request.execute()
                    quota_used += 1

                    items = response.get('items', [])
                    if not items:
                        break

                    fetched += len(items)
                    yield {
                        'items': items,
                        'quota_cost': 1
                    }

                    next_page_token = response.get('nextPageToken')
                    if not next_page_token:
                        break

                    time.sleep(0.1)

                except HttpError as e:
                    if e.resp.status == 403:
                        logger.warning(f"Comments disabled for video {video_id}")
                    else:
                        logger.error(f"Error fetching comments: {e}")
                    break

        except Exception as e:
            logger.error(f"Unexpected error in comments generator: {e}")

    def get_video_transcript(self, video_id):
        """
        Fetch video transcript using youtube-transcript-api

        NOTE: This is NOT part of YouTube Data API - uses a separate library
        Install: pip install youtube-transcript-api

        Args:
            video_id: YouTube video ID

        Returns:
            Full transcript as string or None
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            full_transcript = ' '.join([entry['text'] for entry in transcript_list])

            logger.info(f"Fetched transcript for {video_id} ({len(full_transcript)} chars)")
            return full_transcript

        except Exception as e:
            logger.warning(f"Could not fetch transcript for {video_id}: {e}")
            return None
