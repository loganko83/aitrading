#!/bin/bash
set -e

echo "=========================================="
echo "TradingBot AI Backend - Starting..."
echo "=========================================="

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "✅ PostgreSQL is ready!"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "✅ Redis is ready!"

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head || {
    echo "❌ Migration failed! Exiting..."
    exit 1
}
echo "✅ Migrations completed!"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p /app/logs /app/models /app/cache
echo "✅ Directories created!"

# Test database connection
echo "🔍 Testing database connection..."
python -c "
from app.database.base import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('✅ Database connection successful!')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" || exit 1

# Test Redis connection
echo "🔍 Testing Redis connection..."
python -c "
from app.core.redis_client import RedisClient
import asyncio

async def test_redis():
    try:
        client = await RedisClient.get_client()
        await client.ping()
        print('✅ Redis connection successful!')
    except Exception as e:
        print(f'❌ Redis connection failed: {e}')
        exit(1)

asyncio.run(test_redis())
" || exit 1

echo "=========================================="
echo "✅ All health checks passed!"
echo "🚀 Starting application..."
echo "=========================================="

# Execute the main command
exec "$@"
