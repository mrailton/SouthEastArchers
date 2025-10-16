#!/bin/bash
set -e

echo "Waiting for database connection..."

# Wait for database to be ready
python << END
import sys
import time
from sqlalchemy import create_engine
from config import Config

max_retries = 30
retry_interval = 2

for i in range(max_retries):
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        conn = engine.connect()
        conn.close()
        print("Database connection established!")
        sys.exit(0)
    except Exception as e:
        if i < max_retries - 1:
            print(f"Database not ready yet (attempt {i+1}/{max_retries}), retrying in {retry_interval}s...")
            time.sleep(retry_interval)
        else:
            print(f"Failed to connect to database after {max_retries} attempts")
            sys.exit(1)
END

echo "Running database migrations..."
flask db upgrade

echo "Starting application..."
exec "$@"
