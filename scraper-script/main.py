from scraper import YouTubeScraper
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'scraper_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for YouTube scraper"""

    logger.info("=" * 60)
    logger.info("🚀 YouTube Scraper Started")
    logger.info("=" * 60)

    scraper = YouTubeScraper()

    try:
        # Example 1: Simple keyword search
        logger.info("\n📌 Example 1: Scraping by keyword")
        scraper.scrape_by_keyword(
            keyword="warframe",
            max_videos=50,
            fetch_transcripts=False,  # Set to True if you need transcripts
            fetch_comments=False       # Set to True if you need comments (quota-heavy!)
        )

        # Example 2: Multiple related keywords for one topic
        #logger.info("\n📌 Example 2: Multiple keywords for deep analysis")
        #keywords = ["machine learning tutorial", "ML beginner guide", "learn machine learning"]

       # for keyword in keywords:
        #     scraper.scrape_by_keyword(
        #         keyword=keyword,
        #         max_videos=30,
        #         fetch_transcripts=False,
        #         fetch_comments=False
        #     )

        # # Example 3: Scrape specific channel
        # logger.info("\n📌 Example 3: Scraping specific channel")
        # scraper.scrape_by_channel(
        #     channel_id="UC8butISFwT-Wl7EV0hUK0BQ",  # freeCodeCamp
        #     topic_keyword="programming education",
        #     max_videos=20
        # )

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Scraping interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("\n" + "=" * 60)
    logger.info("✅ YouTube Scraper Finished")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
