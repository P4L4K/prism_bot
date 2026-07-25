from unittest.mock import MagicMock, patch
import pytest
import numpy as np
from app.speech.wake_word import WakeWordDetector
from app.utils.event_bus import EventBus, EVENT_WAKE_WORD

def test_wake_word_detector_resolve_builtin():
    detector = WakeWordDetector(model_name="alexa")
    model_paths, key = detector._resolve_model_config("alexa")
    assert model_paths == ["alexa"]
    assert key == "alexa"

def test_wake_word_detector_resolve_custom_missing():
    detector = WakeWordDetector(model_name="nonexistent.onnx")
    model_paths, key = detector._resolve_model_config("nonexistent.onnx")
    assert model_paths == ["alexa"]
    assert key == "alexa"

@patch("app.speech.wake_word.Model")
@patch("pyaudio.PyAudio")
def test_wake_word_detector_lifecycle(mock_pyaudio, mock_model_class):
    # Mock PyAudio and stream
    mock_pa_inst = MagicMock()
    mock_pyaudio.return_value = mock_pa_inst
    mock_stream = MagicMock()
    mock_pa_inst.open.return_value = mock_stream
    
    # Mock openWakeWord Model instance
    mock_model_inst = MagicMock()
    mock_model_class.return_value = mock_model_inst
    
    detector = WakeWordDetector(model_name="hey_jarvis")
    
    # Start detector
    success = detector.start()
    assert success is True
    
    # Verify model is initialized with correct arguments
    mock_model_class.assert_called_once_with(
        wakeword_models=["hey_jarvis"],
        inference_framework="onnx"
    )
    
    # Stop detector
    detector.stop()
    assert detector._running is False
    mock_stream.close.assert_called_once()
    mock_pa_inst.terminate.assert_called_once()

@patch("app.speech.wake_word.Model")
@patch("pyaudio.PyAudio")
def test_wake_word_detector_loop_trigger(mock_pyaudio, mock_model_class):
    mock_pa_inst = MagicMock()
    mock_pyaudio.return_value = mock_pa_inst
    mock_stream = MagicMock()
    mock_pa_inst.open.return_value = mock_stream
    
    # We want to return pcm bytes once, then trigger exception/stop to exit loop
    # 1280 samples of 16-bit PCM is 2560 bytes
    dummy_bytes = b"\x00" * 2560
    
    # Return dummy_bytes once, then raise an exception to exit loop
    mock_stream.read.side_effect = [dummy_bytes, Exception("Exit loop")]
    
    mock_model_inst = MagicMock()
    mock_model_class.return_value = mock_model_inst
    
    # Simulate a high prediction score (> 0.5) to trigger the wake word event
    mock_model_inst.predict.return_value = {"alexa": 0.8}
    
    bus = EventBus.instance()
    event_triggered = False
    
    def on_wake_word(_payload):
        nonlocal event_triggered
        event_triggered = True
        
    bus.subscribe(EVENT_WAKE_WORD, on_wake_word)
    
    try:
        detector = WakeWordDetector(model_name="alexa")
        detector.start()
        
        # Wait a small amount for the thread to process the single loop and terminate
        detector._thread.join(timeout=1.0)
        
        assert event_triggered is True
    finally:
        detector.stop()
        # Unsubscribe/cleanup event bus
        bus._listeners[EVENT_WAKE_WORD].remove(on_wake_word)
