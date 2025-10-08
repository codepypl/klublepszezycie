"""
Timezone utility functions
"""
import pytz
from datetime import datetime, timezone, timedelta

def get_local_datetime():
    """Get current datetime in local timezone for database defaults"""
    try:
        # Use local timezone directly to avoid circular imports
        tz = get_local_timezone()
        return datetime.now(tz)
    except:
        # Fallback to local time if config fails
        return datetime.now(get_local_timezone())

def get_local_timezone():
    """Get the configured timezone from config"""
    try:
        # Use environment variable or fallback to Europe/Warsaw
        import os
        timezone_name = os.getenv('TIMEZONE', 'Europe/Warsaw')
        return pytz.timezone(timezone_name)
    except:
        # Fallback to Central European Time
        return pytz.timezone('Europe/Warsaw')

def get_local_now():
    """Get current time in local timezone"""
    try:
        # Use local timezone directly to avoid circular imports
        tz = get_local_timezone()
        return datetime.now(tz)
    except:
        # Fallback to local time if config fails
        return datetime.now(get_local_timezone())

def convert_to_local(dt):
    """Convert UTC datetime to local timezone"""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    tz = get_local_timezone()
    return dt.astimezone(tz)

def convert_to_utc(dt):
    """Convert local datetime to UTC"""
    if dt.tzinfo is None:
        tz = get_local_timezone()
        dt = tz.localize(dt)
    return dt.astimezone(pytz.UTC)

