"""
PRISM Voice Assistant — FastAPI Backend Adapter
Bridges the existing Python orchestrator to the React frontend via HTTP REST
and Server-Sent Events (SSE) for real-time streaming of orchestrator events.

Run with:
    uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload

The existing Orchestrator, DB, NLP, TTS/STT modules are left UNTOUCHED.
This file only WIRES them up to HTTP endpoints and an SSE event stream.
"""

from __future__ import annotations

import asyncio
import json
import sys
import threading
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# ── Make sure the project root is on the path ─────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from app.core.config import ASSISTANT_NAME
from app.db.database import init_db
from app.core.orchestrator import Orchestrator
from app.utils.event_bus import (
    EventBus,
    EVENT_LISTENING_START, EVENT_LISTENING_STOP,
    EVENT_TRANSCRIPT, EVENT_RESPONSE,
    EVENT_TTS_START, EVENT_TTS_STOP,
    EVENT_REMINDER_FIRE, EVENT_HISTORY_CLEAR, EVENT_ERROR,
)
from app.utils.logger import get_logger
from backend.api.routes import chat, history, settings as settings_router

logger = get_logger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=f"{ASSISTANT_NAME} API",
    description="Python orchestrator bridge for PRISM voice assistant React UI",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "app://.", "file://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global orchestrator singleton ─────────────────────────────────────────────
_orchestrator: Orchestrator | None = None
_sse_queue: asyncio.Queue = asyncio.Queue()


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    return _orchestrator


# ── SSE event bridge ──────────────────────────────────────────────────────────
def _make_sse_event(event_type: str, payload) -> str:
    data = json.dumps({"type": event_type, "payload": payload})
    return f"data: {data}\n\n"


def _bridge_event(event_type: str, payload) -> None:
    """Called from the EventBus background thread — pushes into asyncio queue."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.call_soon_threadsafe(_sse_queue.put_nowait, (event_type, payload))
    except Exception as exc:
        logger.debug("SSE bridge error: %s", exc)


def _start_event_polling() -> None:
    """Poll the synchronous EventBus and re-publish to the async SSE queue."""
    bus = EventBus.instance()
    for evt in [
        EVENT_LISTENING_START, EVENT_LISTENING_STOP,
        EVENT_TRANSCRIPT, EVENT_RESPONSE,
        EVENT_TTS_START, EVENT_TTS_STOP,
        EVENT_REMINDER_FIRE, EVENT_HISTORY_CLEAR, EVENT_ERROR,
    ]:
        bus.subscribe(evt, lambda payload, e=evt: _bridge_event(e, payload))

    def _poll_loop():
        while True:
            bus.poll()
            import time; time.sleep(0.05)

    threading.Thread(target=_poll_loop, daemon=True).start()


# ── Startup / Shutdown ────────────────────────────────────────────────────────
@app.on_event("startup")
async def _startup():
    global _orchestrator
    logger.info("PRISM API server starting…")
    init_db()
    _orchestrator = Orchestrator()
    _start_event_polling()
    logger.info("PRISM API ready — %s is alive.", ASSISTANT_NAME)


@app.on_event("shutdown")
async def _shutdown():
    if _orchestrator:
        _orchestrator.shutdown()


# ── SSE stream endpoint ───────────────────────────────────────────────────────
@app.get("/api/events")
async def events():
    """Server-Sent Events stream. The React frontend subscribes here for live updates."""

    async def _generator() -> AsyncGenerator[str, None]:
        yield _make_sse_event("connected", {"name": ASSISTANT_NAME})
        while True:
            try:
                event_type, payload = await asyncio.wait_for(_sse_queue.get(), timeout=25)
                yield _make_sse_event(event_type, payload)
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"   # keep connection alive

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "assistant": ASSISTANT_NAME}


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(chat.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
