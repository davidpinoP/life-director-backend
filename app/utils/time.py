"""
Time Utilities
Timezone handling and time formatting.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional


def get_current_hour() -> int:
    """Get current hour (0-23)."""
    return datetime.now().hour


def get_current_time() -> datetime:
    """Get current datetime."""
    return datetime.now()


def format_time(hour: int, minute: int = 0) -> str:
    """Format hour and minute to HH:MM."""
    return f"{hour:02d}:{minute:02d}"


def parse_time(time_str: str) -> Optional[tuple]:
    """
    Parse time string to (hour, minute) tuple.
    Returns None if invalid.
    """
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            return None
        hour = int(parts[0])
        minute = int(parts[1])
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)
        return None
    except (ValueError, AttributeError):
        return None


def get_time_block() -> str:
    """
    Get current time block name.
    morning: 06:00-12:00
    afternoon: 12:00-18:00
    evening: 18:00-22:00
    night: 22:00-06:00
    """
    hour = get_current_hour()
    
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "night"


def get_remaining_hours_today() -> float:
    """
    Get hours remaining until midnight.
    """
    now = datetime.now()
    midnight = datetime(now.year, now.month, now.day) + timedelta(days=1)
    remaining = (midnight - now).total_seconds() / 3600
    return round(remaining, 1)


def get_hours_until(target_hour: int) -> float:
    """
    Get hours until target hour today.
    If target hour has passed, returns hours until that time tomorrow.
    """
    now = datetime.now()
    target = datetime(now.year, now.month, now.day, target_hour)
    
    if target <= now:
        target += timedelta(days=1)
    
    diff = (target - now).total_seconds() / 3600
    return round(diff, 1)


def is_within_time_range(start: str, end: str) -> bool:
    """
    Check if current time is within a range.
    """
    start_parsed = parse_time(start)
    end_parsed = parse_time(end)
    
    if not start_parsed or not end_parsed:
        return False
    
    current = get_current_hour() * 60 + datetime.now().minute
    start_mins = start_parsed[0] * 60 + start_parsed[1]
    end_mins = end_parsed[0] * 60 + end_parsed[1]
    
    if end_mins > start_mins:
        return start_mins <= current <= end_mins
    else:
        # Crosses midnight
        return current >= start_mins or current <= end_mins


def days_until(target_date: datetime) -> int:
    """
    Get number of days until a target date.
    """
    now = datetime.now()
    diff = (target_date.date() - now.date()).days
    return max(0, diff)
