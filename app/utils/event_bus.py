"""
PRISM Voice Assistant — Thread-Safe Event Bus
Decouples background threads (STT, TTS, Orchestrator) from the Tkinter UI thread.

Usage:
    bus = EventBus.instance()
    bus.subscribe("RESPONSE", my_callback)   # on UI thread
    bus.publish("RESPONSE", payload)         # from any thread
    bus.poll()                               # call from Tkinter .after() loop
"""

from __future__ import annotations

import queue
from typing import Any, Callable, Dict, List

# ── Event name constants ────────────────────────────────────────────────────────
EVENT_LISTENING_START = "LISTENING_START"
EVENT_LISTENING_STOP  = "LISTENING_STOP"
EVENT_TRANSCRIPT      = "TRANSCRIPT"       # payload: str (transcribed text)
EVENT_RESPONSE        = "RESPONSE"         # payload: dict {text, card_type, card_data}
EVENT_TTS_START       = "TTS_START"
EVENT_TTS_STOP        = "TTS_STOP"
EVENT_WAKE_WORD       = "WAKE_WORD"
EVENT_REMINDER_FIRE   = "REMINDER_FIRE"    # payload: dict {text}
EVENT_ERROR           = "ERROR"            # payload: str (error message)
EVENT_SETTINGS_CHANGE = "SETTINGS_CHANGE"  # payload: dict {key, value}
EVENT_HISTORY_CLEAR   = "HISTORY_CLEAR"


class EventBus:
    """Singleton pub/sub bus. Background threads publish; UI thread polls."""

    _instance: EventBus | None = None

    def __init__(self) -> None:
        self._queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    @classmethod
    def instance(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Publisher (any thread) ─────────────────────────────────────────────────
    def publish(self, event: str, payload: Any = None) -> None:
        self._queue.put_nowait((event, payload))

    # ── Subscriber registration (UI thread) ───────────────────────────────────
    def subscribe(self, event: str, callback: Callable[[Any], None]) -> None:
        self._subscribers.setdefault(event, []).append(callback)

    def unsubscribe(self, event: str, callback: Callable[[Any], None]) -> None:
        if event in self._subscribers:
            self._subscribers[event] = [
                cb for cb in self._subscribers[event] if cb is not callback
            ]

    # ── Poll — call from Tkinter .after() loop ────────────────────────────────
    def poll(self) -> None:
        try:
            while True:
                event, payload = self._queue.get_nowait()
                for cb in self._subscribers.get(event, []):
                    cb(payload)
        except queue.Empty:
            pass
