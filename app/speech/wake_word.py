"""
PRISM Voice Assistant — Wake-Word Detection (openWakeWord)
Optional always-on detector. Disabled by default; enabled from Settings.
Publishes EVENT_WAKE_WORD on the event bus when the configured wake word is detected.
"""

from __future__ import annotations

import os
import threading
from typing import Optional

import numpy as np
import pyaudio
import openwakeword
from openwakeword.model import Model

from app.core.config import WAKEWORDS_DIR
from app.utils.event_bus import EventBus, EVENT_WAKE_WORD, EVENT_ERROR
from app.utils.logger import get_logger

logger = get_logger(__name__)
bus = EventBus.instance()


class WakeWordDetector:
    """
    Wraps openWakeWord offline detection.
    Supports built-in models (alexa, hey_mycroft, hey_jarvis, hey_rhasspy)
    or custom ONNX models stored in data/wakewords/.
    """

    def __init__(self, model_name: str = "alexa") -> None:
        self._model_name = model_name
        self._model = None
        self._pa = None
        self._audio_stream = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._prediction_key = ""

    def start(self) -> bool:
        """Start listening on a daemon thread. Returns True if successful."""
        try:
            # Resolve model path/name and the expected prediction key
            model_paths, self._prediction_key = self._resolve_model_config(self._model_name)
            logger.info("Initializing openWakeWord with models: %s (key: %r)", model_paths, self._prediction_key)

            self._model = Model(
                wakeword_models=model_paths,
                inference_framework="onnx"
            )

            self._pa = pyaudio.PyAudio()
            self._audio_stream = self._pa.open(
                rate=16000,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=1280,
            )

            self._running = True
            self._thread = threading.Thread(
                target=self._detect_loop, daemon=True, name="WakeWord-Thread"
            )
            self._thread.start()
            logger.info("Wake-word detector started (listening for %r).", self._prediction_key)
            return True

        except Exception as exc:
            logger.error("Failed to start wake-word detector: %s", exc, exc_info=True)
            bus.publish(EVENT_ERROR, f"Wake word init failed: {exc}")
            return False

    def stop(self) -> None:
        self._running = False
        if self._audio_stream:
            try:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
            except Exception:
                pass
            self._audio_stream = None
        if self._pa:
            try:
                self._pa.terminate()
            except Exception:
                pass
            self._pa = None
        self._model = None
        logger.info("Wake-word detector stopped.")

    def _resolve_model_config(self, model_name: str) -> tuple[list[str], str]:
        """Resolves the models to pass to openWakeWord and the dict key for prediction."""
        builtins = ["alexa", "hey_mycroft", "hey_jarvis", "hey_rhasspy"]
        
        # 1. Built-in models
        if model_name in builtins:
            return [model_name], model_name

        # 2. Absolute file paths
        if os.path.exists(model_name):
            base_name = os.path.splitext(os.path.basename(model_name))[0]
            return [model_name], base_name

        # 3. Model files in custom wakewords folder
        custom_path = WAKEWORDS_DIR / model_name
        if custom_path.exists():
            base_name = os.path.splitext(model_name)[0]
            return [str(custom_path)], base_name

        # 4. Fallback to default
        logger.warning("Wake word model %r not found. Falling back to 'alexa'.", model_name)
        return ["alexa"], "alexa"

    def _detect_loop(self) -> None:
        while self._running:
            try:
                # 1280 frames at 16000Hz is 80ms chunk (required by openWakeWord)
                pcm_bytes = self._audio_stream.read(1280, exception_on_overflow=False)
                if not pcm_bytes:
                    continue
                audio_frame = np.frombuffer(pcm_bytes, dtype=np.int16)
                prediction = self._model.predict(audio_frame)

                score = prediction.get(self._prediction_key, 0.0)
                if score > 0.5:
                    logger.info("Wake word '%s' detected (score: %f)!", self._prediction_key, score)
                    bus.publish(EVENT_WAKE_WORD)
            except Exception as exc:
                if self._running:
                    logger.error("Wake-word detection error: %s", exc)
                break
