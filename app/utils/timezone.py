"""
Timezone utility functions
"""
import pytz
from datetime import datetime

def get_local_datetime():
    """Get current datetime in local timezone for database defaults"""
    try:
        from config import config
        if getattr(config['development'], 'USE_LOCAL_TIME', True):
            tz = get_local_timezone()
            return datetime.now(tz)
        else:
            return datetime.utcnow()
    except:
        # Fallback to local time if config fails
        return datetime.now()

def get_local_timezone():
    """Get the configured timezone from config"""
    try:
        from config import config
        timezone_name = getattr(config['development'], 'TIMEZONE', 'Europe/Warsaw')
        return pytz.timezone(timezone_name)
    except:
        # Fallback to Central European Time
        return pytz.timezone('Europe/Warsaw')

def get_local_now():
    """Get current time in local timezone"""
    try:
        from config import config
        if getattr(config['development'], 'USE_LOCAL_TIME', True):
            tz = get_local_timezone()
            return datetime.now(tz)
        else:
            return datetime.utcnow()
    except:
        # Fallback to local time if config fails
        return datetime.now()

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

