"""Datetime utility functions"""
from datetime import datetime, timezone


def utc_now():
    """Get current UTC datetime (timezone-aware)"""
    return datetime.now(timezone.utc)
