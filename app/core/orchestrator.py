"""
PRISM Voice Assistant — Core Orchestrator
Coordinates the full pipeline: STT → NLP → Skill → TTS + UI.
Logs every conversation turn to the database asynchronously.
"""

from __future__ import annotations

import threading
import time
from typing import List, Optional

from app.core.config import (
    ASSISTANT_NAME, PICOVOICE_ACCESS_KEY, WAKE_WORD_ENABLED,
)
from app.db.database import get_session
from app.db.repository import HistoryRepository, PreferenceRepository
from app.modules.base_module import IntentResult, SkillModule, SkillResponse
from app.modules.chitchat import ChitchatModule
from app.modules.news import NewsModule
from app.modules.reminders import ReminderModule
from app.modules.weather import WeatherModule
from app.nlp.intent_classifier import IntentClassifier
from app.speech.stt_engine import STTEngine
from app.speech.tts_engine import TTSEngine
from app.speech.wake_word import WakeWordDetector
from app.utils.event_bus import (
    EventBus, EVENT_RESPONSE, EVENT_TRANSCRIPT, EVENT_WAKE_WORD,
    EVENT_REMINDER_FIRE, EVENT_SETTINGS_CHANGE, EVENT_HISTORY_CLEAR,
)
from app.utils.helpers import clean_text_for_tts
from app.utils.logger import get_logger

logger = get_logger(__name__)
bus = EventBus.instance()


class Orchestrator:
    """
    Central pipeline coordinator. One instance per application run.
    Instantiated once in main.py and injected into the UI.
    """

    def __init__(self) -> None:
        # ── Load preferences ───────────────────────────────────────────────────
        with get_session() as session:
            prefs = PreferenceRepository.get(session)
            stt_engine = prefs.stt_engine if prefs else "google"
            tts_rate = prefs.voice_rate if prefs else 175
            tts_volume = prefs.voice_volume if prefs else 1.0
            wake_enabled = prefs.wake_word_enabled if prefs else False
            self._wake_word_model = prefs.wake_word_model if prefs and hasattr(prefs, "wake_word_model") else "alexa"
            news_location = prefs.news_location if prefs and hasattr(prefs, "news_location") else None

        # ── Speech I/O ─────────────────────────────────────────────────────────
        self._stt = STTEngine(engine=stt_engine)
        self._tts = TTSEngine(rate=tts_rate, volume=tts_volume)

        # ── NLP ────────────────────────────────────────────────────────────────
        self._classifier = IntentClassifier()

        # ── Skill modules ──────────────────────────────────────────────────────
        self._weather = WeatherModule()
        self._news = NewsModule(news_location=news_location)
        self._reminders = ReminderModule()
        self._chitchat = ChitchatModule()

        self._modules: List[SkillModule] = [
            self._weather,
            self._news,
            self._reminders,
            self._chitchat,   # must be last (handles 'unknown')
        ]

        # ── Wake word (optional) ───────────────────────────────────────────────
        self._wake_detector: Optional[WakeWordDetector] = None
        if wake_enabled:
            self._start_wake_detector()

        # ── Subscribe to bus events ────────────────────────────────────────────
        bus.subscribe(EVENT_WAKE_WORD, self._on_wake_word)
        bus.subscribe(EVENT_REMINDER_FIRE, self._on_reminder_fire)
        bus.subscribe(EVENT_SETTINGS_CHANGE, self._on_settings_change)
        bus.subscribe(EVENT_HISTORY_CLEAR, self._on_history_clear)

        logger.info("Orchestrator initialized. %s is ready.", ASSISTANT_NAME)

    # ── Public API ─────────────────────────────────────────────────────────────

    def listen(self, session_id: str = "default") -> None:
        """Start one STT listen cycle asynchronously."""
        self._stt.listen_async(callback=lambda text: self.handle_text(text, session_id, is_typed=False))

    def handle_text(self, text: str, session_id: str = "default", is_typed: bool = False) -> None:
        """
        Process a text command (from STT or typed input).
        Runs the full NLP → skill → TTS + UI pipeline on a worker thread.
        """
        if not text or not text.strip():
            return

        t = threading.Thread(
            target=self._pipeline, args=(text.strip(), session_id, is_typed), daemon=True, name="Pipeline"
        )
        t.start()

    @property
    def is_listening(self) -> bool:
        return self._stt.is_listening

    def shutdown(self) -> None:
        """Graceful shutdown: stop TTS, wake detector."""
        self._tts.stop()
        if self._wake_detector:
            self._wake_detector.stop()
        logger.info("Orchestrator shut down.")

    # ── Pipeline ───────────────────────────────────────────────────────────────

    def _pipeline(self, text: str, session_id: str, is_typed: bool = False) -> None:
        start_ms = time.time()

        # 1. Publish transcript to UI (if it's spoken STT)
        if not is_typed:
            bus.publish(EVENT_TRANSCRIPT, {"text": text, "session_id": session_id})

        # 2. Classify intent
        try:
            intent_result: IntentResult = self._classifier.classify(text)
        except Exception as exc:
            logger.error("Intent classification failed: %s", exc)
            self._emit_error("I had trouble understanding that. Please try again.")
            return

        # 3. Handle clear_history specially
        if intent_result.intent == "clear_history":
            self._handle_clear_history()
            return

        # 4. Dispatch to skill module
        response: Optional[SkillResponse] = None
        for module in self._modules:
            if module.can_handle(intent_result.intent):
                try:
                    response = module.execute(intent_result)
                except Exception as exc:
                    logger.error("Module %s crashed: %s", module.__class__.__name__, exc)
                    response = SkillResponse(
                        text="I ran into an error processing that request. Please try again.",
                        error=str(exc),
                    )
                break

        if response is None:
            response = SkillResponse(
                text="I'm not sure how to handle that. Please try again."
            )

        # 5. Speak the response (non-blocking)
        self._tts.speak(clean_text_for_tts(response.text))

        # 6. Emit response to UI
        latency_ms = int((time.time() - start_ms) * 1000)
        bus.publish(EVENT_RESPONSE, {
            "text": response.text,
            "card_type": response.card_type,
            "card_data": response.card_data,
            "latency_ms": latency_ms,
            "session_id": session_id,
        })

        # 7. Log to DB asynchronously
        threading.Thread(
            target=self._log_turn,
            args=(text, intent_result, response, latency_ms, session_id),
            daemon=True,
        ).start()

    def _log_turn(
        self, text: str, intent_result: IntentResult,
        response: SkillResponse, latency_ms: int, session_id: str
    ) -> None:
        try:
            with get_session() as session:
                HistoryRepository.log_turn(
                    session,
                    user_input=text,
                    intent=intent_result.intent,
                    entities=intent_result.entities,
                    assistant_response=response.text,
                    response_latency_ms=latency_ms,
                    session_id=session_id
                )
        except Exception as exc:
            logger.error("Failed to log conversation turn: %s", exc)

    def _handle_clear_history(self) -> None:
        try:
            with get_session() as session:
                count = HistoryRepository.clear_all(session)
            text = f"Done! I've cleared {count} conversation records from your history."
            self._tts.speak(text)
            bus.publish(EVENT_HISTORY_CLEAR, {"count": count, "text": text})
        except Exception as exc:
            logger.error("Failed to clear history: %s", exc)
            self._emit_error("Failed to clear history.")

    def _emit_error(self, msg: str) -> None:
        self._tts.speak(msg)
        bus.publish(EVENT_RESPONSE, {"text": msg, "card_type": None, "card_data": None})

    # ── Event handlers ─────────────────────────────────────────────────────────

    def _on_wake_word(self, _payload) -> None:
        logger.info("Wake word triggered — starting listen cycle.")
        self.listen()

    def _on_reminder_fire(self, payload: dict) -> None:
        text = f"Reminder: {payload.get('text', '')}"
        self._tts.speak(text)

    def _on_settings_change(self, payload: dict) -> None:
        key = payload.get("key")
        value = payload.get("value")
        if key == "voice_rate":
            self._stt  # no-op
            self._tts.set_rate(int(value))
        elif key == "voice_volume":
            self._tts.set_volume(float(value))
        elif key == "stt_engine":
            self._stt.engine = value
        elif key == "wake_word_enabled":
            if value and not self._wake_detector:
                self._start_wake_detector()
            elif not value and self._wake_detector:
                self._wake_detector.stop()
                self._wake_detector = None
        elif key == "wake_word_model":
            self._wake_word_model = value
            if self._wake_detector:
                logger.info("Restarting wake word detector with new model: %s", value)
                self._wake_detector.stop()
                self._start_wake_detector()
        elif key == "news_location":
            self._news.news_location = value

    def _on_history_clear(self, _payload) -> None:
        pass  # UI handles the visual update

    def _start_wake_detector(self) -> None:
        self._wake_detector = WakeWordDetector(model_name=self._wake_word_model)
        self._wake_detector.start()
