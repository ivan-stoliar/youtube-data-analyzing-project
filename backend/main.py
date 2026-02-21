"""
FastAPI Backend for YouTube Scraper Dashboard
Connects the Vue frontend to the scraper and database
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
import time

# Add scraper to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scraper-script'))

from scraper import YouTubeScraper
from db_manager import get_daily_quota_usage
from config import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube Scraper API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class ScrapeRequest(BaseModel):
    keyword: str
    max_videos: int = 50
    fetch_comments: bool = False
    fetch_transcripts: bool = False

class TopicAnalysisRequest(BaseModel):
    topic_id: str

# Global scraper instance
scraper = YouTubeScraper()

# Background scraping jobs
scraping_jobs = {}

@app.get("/")
def root():
    return {"message": "YouTube Scraper API", "status": "running"}

@app.get("/api/quota")
def get_quota():
    """Get current API quota usage"""
    try:
        used = get_daily_quota_usage()
        return {
            "used": used,
            "limit": 10000,
            "remaining": 10000 - used,
            "percentage": round((used / 10000) * 100, 2)
        }
    except Exception as e:
        logger.error(f"Error getting quota: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape")
def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Start a scraping job in the background"""
    try:
        job_id = f"{request.keyword}_{int(time.time())}"

        scraping_jobs[job_id] = {
            "status": "running",
            "keyword": request.keyword,
            "progress": 0
        }

        # Run scraper in background
        background_tasks.add_task(
            run_scraper,
            job_id,
            request.keyword,
            request.max_videos,
            request.fetch_comments,
            request.fetch_transcripts
        )

        return {
            "job_id": job_id,
            "status": "started",
            "keyword": request.keyword
        }
    except Exception as e:
        logger.error(f"Error starting scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scrape/status/{job_id}")
def get_scrape_status(job_id: str):
    """Get status of a scraping job"""
    if job_id not in scraping_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return scraping_jobs[job_id]

@app.get("/api/topics")
def get_topics():
    """Get all topics from database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        t.id,
                        t.main_keyword,
                        t.created_at,
                        COUNT(DISTINCT tv.video_id) as video_count,
                        COUNT(DISTINCT v.channel_id) as channel_count
                    FROM topics t
                    LEFT JOIN topic_videos tv ON t.id = tv.topic_id
                    LEFT JOIN videos v ON tv.video_id = v.id
                    GROUP BY t.id, t.main_keyword, t.created_at
                    ORDER BY t.created_at DESC
                """)

                topics = cur.fetchall()
                return [dict(row) for row in topics]
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/topics/{topic_id}/analysis")
def get_topic_analysis(topic_id: str):
    """Get comprehensive analysis for a topic"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get topic info
                cur.execute("""
                    SELECT * FROM topics WHERE id = %s
                """, (topic_id,))
                topic = cur.fetchone()

                if not topic:
                    raise HTTPException(status_code=404, detail="Topic not found")

                # Top videos by views
                cur.execute("""
                    SELECT
                        v.title,
                        v.youtube_video_id,
                        v.published_at,
                        v.duration_seconds,
                        v.is_shorts,
                        c.channel_name,
                        vmh.view_count,
                        vmh.like_count,
                        vmh.comment_count,
                        CASE
                            WHEN vmh.view_count > 0
                            THEN ROUND((vmh.like_count::float / vmh.view_count) * 100, 2)
                            ELSE 0
                        END as engagement_rate
                    FROM videos v
                    JOIN topic_videos tv ON v.id = tv.video_id
                    JOIN channels c ON v.channel_id = c.id
                    JOIN LATERAL (
                        SELECT view_count, like_count, comment_count
                        FROM video_metrics_history
                        WHERE video_id = v.id
                        ORDER BY collected_at DESC
                        LIMIT 1
                    ) vmh ON true
                    WHERE tv.topic_id = %s
                    ORDER BY vmh.view_count DESC
                    LIMIT 20
                """, (topic_id,))
                top_videos = [dict(row) for row in cur.fetchall()]

                # Channel distribution
                cur.execute("""
                    SELECT
                        c.channel_name,
                        c.youtube_channel_id,
                        COUNT(v.id) as video_count,
                        AVG(vmh.view_count) as avg_views
                    FROM channels c
                    JOIN videos v ON c.id = v.channel_id
                    JOIN topic_videos tv ON v.id = tv.video_id
                    JOIN LATERAL (
                        SELECT view_count
                        FROM video_metrics_history
                        WHERE video_id = v.id
                        ORDER BY collected_at DESC
                        LIMIT 1
                    ) vmh ON true
                    WHERE tv.topic_id = %s
                    GROUP BY c.id, c.channel_name, c.youtube_channel_id
                    ORDER BY video_count DESC
                    LIMIT 10
                """, (topic_id,))
                top_channels = [dict(row) for row in cur.fetchall()]

                # Shorts vs Regular
                cur.execute("""
                    SELECT
                        v.is_shorts,
                        COUNT(*) as count,
                        AVG(vmh.view_count) as avg_views,
                        AVG(vmh.like_count) as avg_likes
                    FROM videos v
                    JOIN topic_videos tv ON v.id = tv.video_id
                    JOIN LATERAL (
                        SELECT view_count, like_count
                        FROM video_metrics_history
                        WHERE video_id = v.id
                        ORDER BY collected_at DESC
                        LIMIT 1
                    ) vmh ON true
                    WHERE tv.topic_id = %s
                    GROUP BY v.is_shorts
                """, (topic_id,))
                shorts_analysis = [dict(row) for row in cur.fetchall()]

                # Duration distribution
                cur.execute("""
                    SELECT
                        CASE
                            WHEN duration_seconds < 60 THEN '0-1 min (Shorts)'
                            WHEN duration_seconds < 300 THEN '1-5 min'
                            WHEN duration_seconds < 600 THEN '5-10 min'
                            WHEN duration_seconds < 1200 THEN '10-20 min'
                            ELSE '20+ min'
                        END as duration_range,
                        COUNT(*) as count,
                        AVG(vmh.view_count) as avg_views
                    FROM videos v
                    JOIN topic_videos tv ON v.id = tv.video_id
                    JOIN LATERAL (
                        SELECT view_count
                        FROM video_metrics_history
                        WHERE video_id = v.id
                        ORDER BY collected_at DESC
                        LIMIT 1
                    ) vmh ON true
                    WHERE tv.topic_id = %s
                    GROUP BY duration_range
                    ORDER BY MIN(duration_seconds)
                """, (topic_id,))
                duration_distribution = [dict(row) for row in cur.fetchall()]

                # Overall stats
                cur.execute("""
                    SELECT
                        COUNT(DISTINCT v.id) as total_videos,
                        COUNT(DISTINCT v.channel_id) as total_channels,
                        AVG(vmh.view_count) as avg_views,
                        MAX(vmh.view_count) as max_views,
                        AVG(CASE
                            WHEN vmh.view_count > 0
                            THEN (vmh.like_count::float / vmh.view_count) * 100
                            ELSE 0
                        END) as avg_engagement_rate
                    FROM videos v
                    JOIN topic_videos tv ON v.id = tv.video_id
                    JOIN LATERAL (
                        SELECT view_count, like_count
                        FROM video_metrics_history
                        WHERE video_id = v.id
                        ORDER BY collected_at DESC
                        LIMIT 1
                    ) vmh ON true
                    WHERE tv.topic_id = %s
                """, (topic_id,))
                stats = dict(cur.fetchone())

                return {
                    "topic": dict(topic),
                    "stats": stats,
                    "top_videos": top_videos,
                    "top_channels": top_channels,
                    "shorts_analysis": shorts_analysis,
                    "duration_distribution": duration_distribution
                }
    except Exception as e:
        logger.error(f"Error analyzing topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/topics/{topic_id}/recommendations")
def get_recommendations(topic_id: str):
    """Get AI-powered recommendations for entering the niche"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Analyze competition
                cur.execute("""
                    SELECT
                        COUNT(DISTINCT v.channel_id) as unique_channels,
                        AVG(chm.subscribers) as avg_channel_size,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY vmh.view_count) as median_views,
                        AVG(vmh.view_count) as avg_views,
                        COUNT(CASE WHEN v.is_shorts THEN 1 END) as shorts_count,
                        COUNT(*) as total_videos
                    FROM videos v
                    JOIN topic_videos tv ON v.id = tv.topic_id
                    JOIN LATERAL (
                        SELECT view_count
                        FROM video_metrics_history
                        WHERE video_id = v.id
                        ORDER BY collected_at DESC
                        LIMIT 1
                    ) vmh ON true
                    LEFT JOIN LATERAL (
                        SELECT subscribers
                        FROM channel_metrics_history
                        WHERE channel_id = v.channel_id
                        ORDER BY collected_at DESC
                        LIMIT 1
                    ) chm ON true
                    WHERE tv.topic_id = %s
                """, (topic_id,))

                analysis = dict(cur.fetchone())

                # Generate recommendations
                recommendations = generate_recommendations(analysis)

                return {
                    "analysis": analysis,
                    "recommendations": recommendations
                }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_recommendations(analysis):
    """Generate strategic recommendations based on analysis"""
    recs = []

    # Competition level
    if analysis['unique_channels'] < 20:
        recs.append({
            "type": "opportunity",
            "title": "Low Competition Niche",
            "description": f"Only {analysis['unique_channels']} channels actively creating content. Great opportunity for new creators!",
            "action": "Consider entering this niche"
        })
    elif analysis['unique_channels'] > 100:
        recs.append({
            "type": "warning",
            "title": "High Competition",
            "description": f"{analysis['unique_channels']} channels competing. Difficult for beginners.",
            "action": "Find a sub-niche or unique angle"
        })
    else:
        recs.append({
            "type": "info",
            "title": "Moderate Competition",
            "description": f"{analysis['unique_channels']} active channels. Balanced opportunity.",
            "action": "Focus on quality and consistency"
        })

    # Channel size barrier
    avg_subs = analysis.get('avg_channel_size', 0)
    if avg_subs and avg_subs > 100000:
        recs.append({
            "type": "warning",
            "title": "High Subscriber Requirement",
            "description": f"Top channels average {int(avg_subs):,} subscribers. Requires significant investment.",
            "action": "Start with Shorts to build audience faster"
        })
    elif avg_subs and avg_subs < 10000:
        recs.append({
            "type": "opportunity",
            "title": "Accessible for Beginners",
            "description": f"Average channel size is {int(avg_subs):,} subscribers. Good for new creators!",
            "action": "Consistent uploads can help you compete"
        })

    # Shorts opportunity
    shorts_ratio = analysis['shorts_count'] / analysis['total_videos'] if analysis['total_videos'] > 0 else 0
    if shorts_ratio < 0.3:
        recs.append({
            "type": "opportunity",
            "title": "Shorts Opportunity",
            "description": f"Only {int(shorts_ratio * 100)}% of content is Shorts. Untapped potential!",
            "action": "Create Shorts to capture this audience"
        })

    # View expectations
    median_views = analysis.get('median_views', 0)
    if median_views:
        recs.append({
            "type": "info",
            "title": "View Expectations",
            "description": f"Median video gets {int(median_views):,} views. Set realistic goals.",
            "action": f"Aim for {int(median_views * 1.5):,}+ views to stand out"
        })

    return recs

def run_scraper(job_id, keyword, max_videos, fetch_comments, fetch_transcripts):
    """Background task to run scraper"""
    import time

    try:
        scraping_jobs[job_id]["status"] = "running"
        scraping_jobs[job_id]["progress"] = 10

        # Run scraper
        scraper.scrape_by_keyword(
            keyword=keyword,
            max_videos=max_videos,
            fetch_comments=fetch_comments,
            fetch_transcripts=fetch_transcripts
        )

        scraping_jobs[job_id]["status"] = "completed"
        scraping_jobs[job_id]["progress"] = 100

    except Exception as e:
        logger.error(f"Scraping job {job_id} failed: {e}")
        scraping_jobs[job_id]["status"] = "failed"
        scraping_jobs[job_id]["error"] = str(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
