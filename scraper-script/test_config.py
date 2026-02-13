"""
Quick test script to verify your .env configuration
Run this before running the main scraper
"""

from dotenv import load_dotenv
import os
import sys

def test_configuration():
    print("=" * 60)
    print("🔍 Testing YouTube Scraper Configuration")
    print("=" * 60)
    print()

    # Load environment variables
    load_dotenv()

    all_good = True

    # Test 1: YouTube API Key
    print("1️⃣  Testing YouTube API Key...")
    api_key = os.getenv('YOUTUBE_API_KEY')
    if api_key:
        if api_key.startswith('AIza'):
            print(f"   ✅ API Key found: {api_key[:15]}...")
        else:
            print(f"   ⚠️  API Key found but doesn't look valid: {api_key[:15]}...")
            all_good = False
    else:
        print("   ❌ YOUTUBE_API_KEY not found in .env file")
        all_good = False
    print()

    # Test 2: Database URL
    print("2️⃣  Testing Database URL...")
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        print(f"   ✅ DATABASE_URL found")

        # Parse and display parts
        if db_url.startswith('postgresql://'):
            try:
                # Extract parts (basic parsing)
                parts = db_url.replace('postgresql://', '').split('@')
                user_pass = parts[0].split(':')
                host_db = parts[1].split('/')

                username = user_pass[0]
                host_port = host_db[0].split(':')
                host = host_port[0]
                port = host_port[1] if len(host_port) > 1 else '5432'
                dbname = host_db[1].split('?')[0]

                print(f"   📊 Details:")
                print(f"      - Username: {username}")
                print(f"      - Host: {host}")
                print(f"      - Port: {port}")
                print(f"      - Database: {dbname}")
            except:
                print("   ⚠️  Could not parse DATABASE_URL format")
        else:
            print("   ⚠️  DATABASE_URL doesn't start with 'postgresql://'")
            all_good = False
    else:
        print("   ❌ DATABASE_URL not found in .env file")
        all_good = False
    print()

    # Test 3: Database Connection
    print("3️⃣  Testing Database Connection...")
    if db_url:
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            print("   ✅ Successfully connected to database!")

            # Test if tables exist
            cur = conn.cursor()
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('topics', 'videos', 'channels')
            """)
            tables = cur.fetchall()

            if len(tables) >= 3:
                print(f"   ✅ Found {len(tables)} required tables")
            else:
                print(f"   ⚠️  Only found {len(tables)}/3 required tables")
                print("   💡 Did you run the schema.sql file?")
                all_good = False

            conn.close()

        except ImportError:
            print("   ❌ psycopg2 not installed")
            print("   💡 Run: pip install psycopg2-binary")
            all_good = False
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            print()
            print("   💡 Common fixes:")
            print("      - Check username and password")
            print("      - Make sure PostgreSQL is running")
            print("      - Verify host and port are correct")
            all_good = False
    else:
        print("   ⏭️  Skipped (no DATABASE_URL)")
    print()

    # Test 4: YouTube API
    print("4️⃣  Testing YouTube API...")
    if api_key:
        try:
            from googleapiclient.discovery import build
            youtube = build('youtube', 'v3', developerKey=api_key)

            # Simple test request
            request = youtube.search().list(
                q='test',
                part='id',
                type='video',
                maxResults=1
            )
            response = request.execute()

            print("   ✅ YouTube API is working!")

        except ImportError:
            print("   ❌ google-api-python-client not installed")
            print("   💡 Run: pip install -r requirements.txt")
            all_good = False
        except Exception as e:
            print(f"   ❌ API test failed: {e}")
            print()
            print("   💡 Common fixes:")
            print("      - Check if API key is correct")
            print("      - Enable 'YouTube Data API v3' in Google Cloud Console")
            print("      - Check for API key restrictions")
            all_good = False
    else:
        print("   ⏭️  Skipped (no API key)")
    print()

    # Summary
    print("=" * 60)
    if all_good:
        print("✅ All tests passed! You're ready to run the scraper.")
        print()
        print("Next steps:")
        print("   python main.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print()
        print("Need help? Check SETUP_GUIDE.md")
    print("=" * 60)

    return all_good

if __name__ == "__main__":
    success = test_configuration()
    sys.exit(0 if success else 1)
