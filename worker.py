#!/usr/bin/env python
"""RQ worker process for background job execution"""

import os
import sys

from redis import Redis
from rq import Connection, Worker

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Start RQ worker"""
    # Get Redis URL from environment
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Connect to Redis
    redis_conn = Redis.from_url(redis_url)

    # Create worker with default queue
    with Connection(redis_conn):
        worker = Worker(["default"])
        print(f"Starting RQ worker on queue: default")
        print(f"Redis URL: {redis_url}")
        worker.work()


if __name__ == "__main__":
    main()
