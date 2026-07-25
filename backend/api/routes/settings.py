"""
PRISM API — Settings routes
GET  /api/settings  — read current preferences
POST /api/settings  — update one or more preference fields
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["settings"])


class SettingsUpdate(BaseModel):
    voice_rate: Optional[int] = None
    voice_volume: Optional[float] = None
    stt_engine: Optional[str] = None
    temperature_unit: Optional[str] = None
    news_category: Optional[str] = None
    news_location: Optional[str] = None
    theme: Optional[str] = None
    wake_word_enabled: Optional[bool] = None
    wake_word_model: Optional[str] = None
    default_city: Optional[str] = None


@router.get("/settings")
async def get_settings():
    try:
        from app.db.database import get_session
        from app.db.repository import PreferenceRepository
        with get_session() as session:
            prefs = PreferenceRepository.get(session)
            if not prefs:
                raise HTTPException(status_code=404, detail="Preferences not found")
            return {
                "voice_rate": prefs.voice_rate,
                "voice_volume": prefs.voice_volume,
                "stt_engine": prefs.stt_engine,
                "temperature_unit": prefs.temperature_unit,
                "news_category": prefs.news_category,
                "news_location": prefs.news_location,
                "theme": prefs.theme,
                "wake_word_enabled": prefs.wake_word_enabled,
                "wake_word_model": prefs.wake_word_model,
                "default_city": prefs.default_city,
            }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Settings GET error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/settings")
async def update_settings(body: SettingsUpdate):
    try:
        from app.db.database import get_session
        from app.db.repository import PreferenceRepository
        from app.utils.event_bus import EventBus, EVENT_SETTINGS_CHANGE
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields provided")
        with get_session() as session:
            PreferenceRepository.update(session, **updates)
        bus = EventBus.instance()
        for key, value in updates.items():
            bus.publish(EVENT_SETTINGS_CHANGE, {"key": key, "value": value})
        return {"status": "updated", "fields": list(updates.keys())}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Settings POST error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
