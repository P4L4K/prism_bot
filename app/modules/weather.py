"""
PRISM Voice Assistant — Weather Skill Module
Fetches current weather and 5-day forecast from OpenWeatherMap.
In-memory cache with 60-second TTL to respect free-tier rate limits.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, Optional, Tuple

import httpx

from app.core.config import (
    DEFAULT_CITY, OPENWEATHERMAP_API_KEY,
    TEMPERATURE_UNIT, WEATHER_API_TIMEOUT, WEATHER_CACHE_TTL,
)
from app.modules.base_module import IntentResult, SkillModule, SkillResponse
from app.utils.helpers import celsius_to_fahrenheit, get_weather_emoji, wind_direction
from app.utils.logger import get_logger


def _get_saved_city() -> str:
    """Read the user's saved default city from the DB at runtime.

    Falls back to the .env / config value so the module keeps working
    even before the DB is initialised.
    """
    try:
        from app.db.database import get_session
        from app.db.repository import PreferenceRepository
        with get_session() as session:
            prefs = PreferenceRepository.get(session)
            if prefs and prefs.default_city:
                return prefs.default_city.strip()
    except Exception:
        pass
    return DEFAULT_CITY

logger = get_logger(__name__)

OWM_BASE = "https://api.openweathermap.org/data/2.5"


class WeatherModule(SkillModule):

    def __init__(self) -> None:
        self._cache: Dict[str, Tuple[float, dict]] = {}  # city -> (timestamp, data)

    def can_handle(self, intent: str) -> bool:
        return intent == "get_weather"

    def execute(self, intent_result: IntentResult) -> SkillResponse:
        city = intent_result.entities.get("city") or _get_saved_city()
        unit = TEMPERATURE_UNIT

        try:
            current = self._get_current(city, unit)
            forecast = self._get_forecast(city, unit)
        except Exception as exc:
            logger.error("Weather fetch error: %s", exc)
            return SkillResponse(
                text=f"I'm sorry, I couldn't retrieve weather data for {city} right now.",
                error=str(exc),
            )

        if not current:
            return SkillResponse(
                text=f"Weather data for {city} is currently unavailable. Please check your API key.",
            )

        # ── Build spoken response ──────────────────────────────────────────────
        symbol = "°F" if unit == "F" else "°C"
        temp = current["temp"]
        feels = current["feels_like"]
        desc = current["description"].capitalize()
        emoji = get_weather_emoji(current["description"])

        text = (
            f"Currently in {city}: {emoji} {desc}. "
            f"Temperature is {temp}{symbol}, feels like {feels}{symbol}. "
            f"Humidity {current['humidity']}%, wind {current['wind_speed']} km/h "
            f"from the {current['wind_dir']}."
        )

        # ── Build card data ────────────────────────────────────────────────────
        card_data = {
            "city": city,
            "country": current.get("country", ""),
            "temp": temp,
            "feels_like": feels,
            "description": desc,
            "emoji": emoji,
            "humidity": current["humidity"],
            "wind_speed": current["wind_speed"],
            "wind_dir": current["wind_dir"],
            "unit": symbol,
            "forecast": forecast,
        }

        return SkillResponse(text=text, card_type="weather", card_data=card_data)

    # ── Internal API helpers ───────────────────────────────────────────────────

    def _get_current(self, city: str, unit: str) -> Optional[dict]:
        cache_key = f"current:{city}:{unit}"
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached[0] < WEATHER_CACHE_TTL:
            logger.debug("Weather cache hit for %s", city)
            return cached[1]

        if not OPENWEATHERMAP_API_KEY:
            logger.warning("OPENWEATHERMAP_API_KEY not set.")
            return None

        url = f"{OWM_BASE}/weather"
        params = {
            "q": city,
            "appid": OPENWEATHERMAP_API_KEY,
            "units": "imperial" if unit == "F" else "metric",
        }

        try:
            with httpx.Client(timeout=WEATHER_API_TIMEOUT) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ValueError(f"City '{city}' not found.")
            raise

        wind_deg = data["wind"].get("deg", 0)
        result = {
            "temp": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "wind_speed": round(data["wind"].get("speed", 0) * 3.6, 1),  # m/s → km/h
            "wind_dir": wind_direction(wind_deg),
            "country": data["sys"].get("country", ""),
        }
        self._cache[cache_key] = (time.time(), result)
        return result

    def _get_forecast(self, city: str, unit: str) -> list:
        cache_key = f"forecast:{city}:{unit}"
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached[0] < WEATHER_CACHE_TTL:
            return cached[1]

        if not OPENWEATHERMAP_API_KEY:
            return []

        url = f"{OWM_BASE}/forecast"
        params = {
            "q": city,
            "appid": OPENWEATHERMAP_API_KEY,
            "units": "imperial" if unit == "F" else "metric",
            "cnt": 5,  # 5 × 3-hour slots ≈ next 15 hours; enough for a daily summary
        }

        try:
            with httpx.Client(timeout=WEATHER_API_TIMEOUT) as client:
                resp = client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("Forecast fetch failed: %s", exc)
            return []

        days = []
        seen_dates = set()
        for item in data.get("list", []):
            dt = datetime.fromtimestamp(item["dt"])
            date_str = dt.strftime("%a %d")
            if date_str not in seen_dates:
                seen_dates.add(date_str)
                days.append({
                    "date": date_str,
                    "temp": round(item["main"]["temp"], 1),
                    "description": item["weather"][0]["description"],
                    "emoji": get_weather_emoji(item["weather"][0]["description"]),
                })
            if len(days) >= 3:
                break

        self._cache[cache_key] = (time.time(), days)
        return days
