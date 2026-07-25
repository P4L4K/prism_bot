"""
PRISM API — Chat routes
POST /api/chat  — submit typed text to the orchestrator
POST /api/listen — trigger mic listen cycle
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    text: str
    session_id: Optional[str] = "default"


@router.post("/log_error")
async def log_error(req: Request):
    body = await req.json()
    with open('d:/voice_bot/frontend_error.log', 'a') as f:
        f.write(f"{body.get('message')}\n{body.get('stack')}\n\n")
    return {"status": "logged"}

@router.post("/chat")
async def chat(req: ChatRequest):
    """Submit a typed user message to the orchestrator pipeline."""
    try:
        from backend.api.app import get_orchestrator
        orch = get_orchestrator()
        orch.handle_text(req.text.strip(), req.session_id, is_typed=True)
        return {"status": "processing", "text": req.text, "session_id": req.session_id}
    except Exception as exc:
        logger.error("Chat route error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


class ListenRequest(BaseModel):
    session_id: Optional[str] = "default"

@router.post("/listen")
async def listen(req: ListenRequest = None):
    """Trigger a single mic listen cycle."""
    try:
        from backend.api.app import get_orchestrator
        orch = get_orchestrator()
        session_id = req.session_id if req else "default"
        orch.listen(session_id)
        return {"status": "listening", "session_id": session_id}
    except Exception as exc:
        logger.error("Listen route error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
