"""
PRISM Voice Assistant — Text-to-Speech Engine
Uses pyttsx3 (OS-native SAPI5 on Windows) on a dedicated daemon thread.
Non-blocking: callers publish to a queue; TTS drains it independently.
"""

from __future__ import annotations

import queue
import threading
from typing import Optional

import pyttsx3

from app.utils.event_bus import EventBus, EVENT_TTS_START, EVENT_TTS_STOP
from app.utils.logger import get_logger

logger = get_logger(__name__)
bus = EventBus.instance()

_STOP_SENTINEL = object()


class TTSEngine:
    """
    Thread-safe TTS engine. Accepts text via speak() and plays it on a
    background daemon thread, ensuring the UI thread is never blocked.
    """

    def __init__(self, rate: int = 175, volume: float = 1.0) -> None:
        self._rate = rate
        self._volume = volume
        self._queue: queue.Queue = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True, name="TTS-Worker")
        self._thread.start()
        logger.info("TTS engine started (rate=%s, volume=%s)", rate, volume)

    # ── Public API ─────────────────────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """Enqueue text for speaking. Returns immediately."""
        if text and text.strip():
            self._queue.put(text)

    def set_rate(self, rate: int) -> None:
        self._rate = max(100, min(300, rate))

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))

    def stop(self) -> None:
        """Drain queue and signal worker to exit."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        self._queue.put(_STOP_SENTINEL)

    # ── Worker thread ──────────────────────────────────────────────────────────

    def _worker(self) -> None:
        """Runs on daemon thread — processes TTS requests serially."""
        try:
            engine = pyttsx3.init()
        except Exception as exc:
            logger.error("Failed to initialize pyttsx3: %s", exc)
            return

        while True:
            item = self._queue.get()
            if item is _STOP_SENTINEL:
                logger.info("TTS worker received stop signal.")
                break

            try:
                engine.setProperty("rate", self._rate)
                engine.setProperty("volume", self._volume)
                bus.publish(EVENT_TTS_START)
                engine.say(item)
                engine.runAndWait()
                bus.publish(EVENT_TTS_STOP)
            except Exception as exc:
                logger.error("TTS playback error: %s", exc)
                bus.publish(EVENT_TTS_STOP)
