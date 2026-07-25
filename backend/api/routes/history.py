"""
PRISM API — History routes
GET  /api/history        — fetch recent conversations
GET  /api/history/search — search conversations
DELETE /api/history/{id} — delete a single turn
POST /api/history/clear  — clear all history
"""

from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["history"])


def _turn_to_dict(t) -> dict:
    return {
        "id": t.id,
        "user_input": t.user_input,
        "intent": t.intent,
        "assistant_response": t.assistant_response,
        "response_latency_ms": t.response_latency_ms,
        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
    }


@router.get("/history/books")
def get_books():
    """Fetch distinct books (sessions)."""
    try:
        from app.db.database import get_session
        from app.db.repository import HistoryRepository
        with get_session() as session:
            return HistoryRepository.get_books(session)
    except Exception as exc:
        logger.error("Failed to fetch books: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


class RenameRequest(BaseModel):
    session_id: str
    title: str

@router.post("/history/rename")
def rename_book(req: RenameRequest):
    """Rename a specific book."""
    try:
        from app.db.database import get_session
        from app.db.repository import HistoryRepository
        with get_session() as session:
            success = HistoryRepository.rename_book(session, session_id=req.session_id, new_title=req.title)
            if not success:
                raise HTTPException(status_code=404, detail="Book not found or has no turns yet")
            return {"status": "renamed", "session_id": req.session_id, "title": req.title}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to rename book: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/history")
def get_history(limit: int = 50, session_id: str = "default"):
    """Fetch recent history turns for a specific book."""
    try:
        from app.db.database import get_session
        from app.db.repository import HistoryRepository
        with get_session() as session:
            turns = HistoryRepository.get_recent(session, limit=limit, session_id=session_id)
            return [_turn_to_dict(t) for t in turns]
    except Exception as exc:
        logger.error("History GET error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/history/{turn_id}")
async def delete_turn(turn_id: int):
    try:
        from app.db.database import get_session
        from app.db.repository import HistoryRepository
        with get_session() as session:
            deleted = HistoryRepository.delete(session, turn_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Turn not found")
        return {"status": "deleted", "id": turn_id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("History DELETE error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/history/clear")
async def clear_history():
    try:
        from app.db.database import get_session
        from app.db.repository import HistoryRepository
        with get_session() as session:
            count = HistoryRepository.clear_all(session)
        return {"status": "cleared", "count": count}
    except Exception as exc:
        logger.error("History CLEAR error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
