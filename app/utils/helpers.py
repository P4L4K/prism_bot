"""
PRISM Voice Assistant — Helper Utilities
Date/time formatting, text truncation, and unit conversions.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


def format_datetime(dt: datetime, fmt: str = "%A, %B %d at %I:%M %p") -> str:
    """Return a human-readable datetime string."""
    return dt.strftime(fmt)


def friendly_time_delta(dt: datetime) -> str:
    """Return a friendly relative time string (e.g. 'in 2 hours', '3 minutes ago')."""
    now = datetime.now()
    delta = dt - now
    seconds = int(delta.total_seconds())

    if seconds < 0:
        seconds = abs(seconds)
        if seconds < 60:
            return f"{seconds} seconds ago"
        elif seconds < 3600:
            return f"{seconds // 60} minute{'s' if seconds // 60 != 1 else ''} ago"
        elif seconds < 86400:
            return f"{seconds // 3600} hour{'s' if seconds // 3600 != 1 else ''} ago"
        else:
            return f"{seconds // 86400} day{'s' if seconds // 86400 != 1 else ''} ago"
    else:
        if seconds < 60:
            return f"in {seconds} seconds"
        elif seconds < 3600:
            return f"in {seconds // 60} minute{'s' if seconds // 60 != 1 else ''}"
        elif seconds < 86400:
            return f"in {seconds // 3600} hour{'s' if seconds // 3600 != 1 else ''}"
        else:
            return f"in {seconds // 86400} day{'s' if seconds // 86400 != 1 else ''}"


def celsius_to_fahrenheit(c: float) -> float:
    return round(c * 9 / 5 + 32, 1)


def fahrenheit_to_celsius(f: float) -> float:
    return round((f - 32) * 5 / 9, 1)


def truncate(text: str, max_len: int = 80) -> str:
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def clean_text_for_tts(text: str) -> str:
    """Strip markdown and special chars that confuse TTS engines."""
    text = re.sub(r"[*_`#\[\]()•]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def wind_direction(degrees: float) -> str:
    """Convert wind bearing degrees to compass direction."""
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    ix = int((degrees + 22.5) / 45) % 8
    return dirs[ix]


def get_weather_emoji(condition: str) -> str:
    """Return a weather emoji based on OWM condition string."""
    condition = condition.lower()
    if "thunderstorm" in condition:
        return "⛈️"
    elif "drizzle" in condition or "rain" in condition:
        return "🌧️"
    elif "snow" in condition:
        return "❄️"
    elif "mist" in condition or "fog" in condition or "haze" in condition:
        return "🌫️"
    elif "clear" in condition:
        return "☀️"
    elif "few clouds" in condition:
        return "🌤️"
    elif "cloud" in condition:
        return "☁️"
    else:
        return "🌡️"
