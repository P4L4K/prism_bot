"""
PRISM Voice Assistant — Application Configuration
Loads settings from .env file and exposes typed config constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Resolve project root and load .env ─────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)

# ── Paths ───────────────────────────────────────────────────────────────────────
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"
ASSETS_DIR = ROOT_DIR / "assets"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'assistant.db'}")
LOG_FILE = LOGS_DIR / "assistant.log"

# ── API Keys & External URLs ───────────────────────────────────────────────────────
OPENWEATHERMAP_API_KEY: str = os.getenv("OPENWEATHERMAP_API_KEY", "")
NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
PICOVOICE_ACCESS_KEY: str = os.getenv("PICOVOICE_ACCESS_KEY", "")
FRONTEND_URL: str = os.getenv("FRONTEND_URL", "")

# ── Assistant Identity ──────────────────────────────────────────────────────────
ASSISTANT_NAME: str = os.getenv("PRISM_ASSISTANT_NAME", "PRISM")

# ── Speech Settings ─────────────────────────────────────────────────────────────
STT_ENGINE: str = os.getenv("PRISM_STT_ENGINE", "google")          # 'google' | 'vosk'
WAKE_WORD_ENABLED: bool = os.getenv("PRISM_WAKE_WORD_ENABLED", "false").lower() == "true"
WAKEWORDS_DIR = DATA_DIR / "wakewords"
WAKEWORDS_DIR.mkdir(parents=True, exist_ok=True)
WAKE_WORD_MODEL: str = os.getenv("PRISM_WAKE_WORD_MODEL", "alexa")


# ── Weather ─────────────────────────────────────────────────────────────────────
DEFAULT_CITY: str = os.getenv("PRISM_DEFAULT_CITY", "London")
TEMPERATURE_UNIT: str = os.getenv("PRISM_TEMPERATURE_UNIT", "C").upper()  # 'C' | 'F'
WEATHER_CACHE_TTL: int = 60         # seconds
WEATHER_API_TIMEOUT: int = 10       # seconds

# ── News ────────────────────────────────────────────────────────────────────────
NEWS_CATEGORY: str = os.getenv("PRISM_NEWS_CATEGORY", "general")
NEWS_CACHE_TTL: int = 900           # 15 minutes
NEWS_HEADLINE_COUNT: int = 5
NEWS_API_TIMEOUT: int = 10

# ── UI / Theme ──────────────────────────────────────────────────────────────────
THEME: str = os.getenv("PRISM_THEME", "dark")   # 'dark' | 'light'

# ── Logging ─────────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("PRISM_LOG_LEVEL", "INFO")

# ── TTS Defaults ────────────────────────────────────────────────────────────────
TTS_DEFAULT_RATE: int = 175
TTS_DEFAULT_VOLUME: float = 1.0
