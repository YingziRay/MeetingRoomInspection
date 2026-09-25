#!/bin/sh
set -e

echo "Waiting for PostgreSQL database to be ready..."
until python -c "
import psycopg, os
url = os.environ.get('DATABASE_URL', '').replace('+psycopg', '')
conn = psycopg.connect(url)
conn.close()
" 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping 1s"
  sleep 1
done

echo "PostgreSQL is up and ready!"

echo "Running Alembic migrations..."
alembic upgrade head

echo "Seeding initial data if needed..."
python scripts/seed_data.py || true

echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
