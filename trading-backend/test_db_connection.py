import sys
sys.path.insert(0, "/mnt/storage/trading/trading-backend")

from app.database import engine
from sqlalchemy import text

def test_connection():
    print("=== Database Connection Test ===\n")
    try:
        with engine.connect() as conn:
            # PostgreSQL version
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"PostgreSQL Version: {version[:60]}...\n")
            
            # List tables
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"))
            tables = [row[0] for row in result]
            print(f"Tables ({len(tables)}): {', '.join(tables)}\n")
            
            # Count records
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"Total Users: {user_count}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM sessions"))
            session_count = result.fetchone()[0]
            print(f"Total Sessions: {session_count}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM api_keys"))
            api_key_count = result.fetchone()[0]
            print(f"Total API Keys: {api_key_count}\n")
            
            # Check recent users
            if user_count > 0:
                result = conn.execute(text("SELECT email, name, created_at FROM users ORDER BY created_at DESC LIMIT 3"))
                print("Recent Users:")
                for row in result:
                    print(f"  - {row[0]} ({row[1]}) - Created: {row[2]}")
            
            print("\n✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
