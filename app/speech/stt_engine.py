"""
PRISM Voice Assistant — Speech-to-Text Engine
Supports Google Speech Recognition (online) with Vosk offline fallback.
"""

from __future__ import annotations

import os
import threading
from typing import Optional

import speech_recognition as sr

from app.utils.event_bus import EventBus, EVENT_LISTENING_START, EVENT_LISTENING_STOP, EVENT_ERROR
from app.utils.logger import get_logger

logger = get_logger(__name__)
bus = EventBus.instance()


class STTEngine:
    """
    Listens to the microphone and returns transcribed text.
    Attempts Google Speech Recognition first; falls back to Vosk if:
      - No network is available, OR
      - stt_engine preference is set to 'vosk'.
    """

    def __init__(self, engine: str = "google") -> None:
        self.engine = engine  # 'google' | 'vosk'
        self._recognizer = sr.Recognizer()
        self._recognizer.pause_threshold = 0.8
        self._recognizer.energy_threshold = 300
        self._recognizer.dynamic_energy_threshold = True
        self._is_listening = False
        self._vosk_model = None
        self._lock = threading.Lock()

    # ── Public API ─────────────────────────────────────────────────────────────

    def listen_once(self) -> Optional[str]:
        """
        Capture one utterance from the microphone and return transcribed text.
        Blocks until speech is detected and processed.
        Returns None on failure.
        """
        with self._lock:
            self._is_listening = True

        bus.publish(EVENT_LISTENING_START)
        text = None
        try:
            with sr.Microphone() as source:
                logger.debug("Adjusting for ambient noise…")
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("Listening…")
                audio = self._recognizer.listen(source, timeout=8, phrase_time_limit=15)

            text = self._transcribe(audio)
            logger.info("Transcribed: %r", text)

        except sr.WaitTimeoutError:
            logger.warning("Microphone listen timeout — no speech detected.")
            bus.publish(EVENT_ERROR, "No speech detected. Please try again.")
        except OSError as exc:
            logger.error("Microphone error: %s", exc)
            bus.publish(EVENT_ERROR, "Microphone not available.")
        except Exception as exc:
            logger.error("Unexpected STT error: %s", exc)
            bus.publish(EVENT_ERROR, "Speech recognition failed.")
        finally:
            with self._lock:
                self._is_listening = False
            bus.publish(EVENT_LISTENING_STOP)

        return text

    def listen_async(self, callback) -> threading.Thread:
        """Start listening on a daemon thread; calls callback(text) when done."""
        t = threading.Thread(target=self._listen_worker, args=(callback,), daemon=True)
        t.start()
        return t

    # ── Private helpers ────────────────────────────────────────────────────────

    def _listen_worker(self, callback) -> None:
        text = self.listen_once()
        if text:
            callback(text)

    def _transcribe(self, audio: sr.AudioData) -> Optional[str]:
        """Try Google first; fall back to Vosk on failure."""
        if self.engine == "vosk":
            return self._vosk_transcribe(audio)

        # Google (online)
        try:
            result = self._recognizer.recognize_google(audio)
            return result
        except sr.UnknownValueError:
            logger.warning("Google STT: could not understand audio.")
            return None
        except sr.RequestError as exc:
            logger.warning("Google STT request failed (%s) — falling back to Vosk.", exc)
            return self._vosk_transcribe(audio)

    def _vosk_transcribe(self, audio: sr.AudioData) -> Optional[str]:
        """Transcribe using Vosk offline model."""
        try:
            if self._vosk_model is None:
                self._vosk_model = self._load_vosk_model()

            if self._vosk_model is None:
                return None

            from vosk import KaldiRecognizer
            import json as _json
            import wave, io

            # Convert audio to WAV bytes
            wav_bytes = audio.get_wav_data()
            wf = wave.open(io.BytesIO(wav_bytes))
            rec = KaldiRecognizer(self._vosk_model, wf.getframerate())
            rec.SetWords(True)

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                rec.AcceptWaveform(data)

            result = _json.loads(rec.FinalResult())
            text = result.get("text", "").strip()
            return text if text else None

        except Exception as exc:
            logger.error("Vosk transcription failed: %s", exc)
            return None

    def _load_vosk_model(self):
        """Attempt to load a local Vosk model from common locations."""
        try:
            from vosk import Model
            from app.core.config import ROOT_DIR

            model_paths = [
                ROOT_DIR / "models" / "vosk-model-small-en-us",
                ROOT_DIR / "models" / "vosk-model-en-us",
            ]
            for path in model_paths:
                if path.exists():
                    logger.info("Loading Vosk model from %s", path)
                    return Model(str(path))

            logger.warning(
                "No Vosk model found. Download from https://alphacephei.com/vosk/models "
                "and extract to %s/models/vosk-model-small-en-us/",
                ROOT_DIR,
            )
            return None
        except Exception as exc:
            logger.error("Failed to load Vosk model: %s", exc)
            return None

    @property
    def is_listening(self) -> bool:
        with self._lock:
            return self._is_listening
