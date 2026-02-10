import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import sys

load_dotenv()

# Environment validation
REQUIRED_ENV_VARS = ['YOUTUBE_API_KEY', 'DATABASE_URL']
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
QUOTA_LIMIT = int(os.getenv('QUOTA_LIMIT', '10000'))

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_persistent_connection():
    """Get a persistent connection for batch operations"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
