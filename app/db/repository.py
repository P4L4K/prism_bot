"""
PRISM Voice Assistant — Data Access Layer (Repository)
All database CRUD operations are concentrated here.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import ConversationTurn, Preference, Reminder, User
from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_USER_ID = 1


# ── User Repository ─────────────────────────────────────────────────────────────
class UserRepository:

    @staticmethod
    def get_default_user(session: Session) -> Optional[User]:
        return session.get(User, DEFAULT_USER_ID)

    @staticmethod
    def create_default_user(session: Session) -> User:
        from app.core.config import (
            DEFAULT_CITY, NEWS_CATEGORY, TEMPERATURE_UNIT, THEME,
            TTS_DEFAULT_RATE, TTS_DEFAULT_VOLUME, WAKE_WORD_ENABLED,
            WAKE_WORD_MODEL,
        )
        user = User(id=DEFAULT_USER_ID, name="User")
        prefs = Preference(
            user_id=DEFAULT_USER_ID,
            voice_rate=TTS_DEFAULT_RATE,
            voice_volume=TTS_DEFAULT_VOLUME,
            temperature_unit=TEMPERATURE_UNIT,
            news_category=NEWS_CATEGORY,
            theme=THEME,
            wake_word_enabled=WAKE_WORD_ENABLED,
            wake_word_model=WAKE_WORD_MODEL,
            stt_engine="google",
            default_city=DEFAULT_CITY,
        )
        session.add(user)
        session.add(prefs)
        session.flush()
        return user


# ── Preferences Repository ──────────────────────────────────────────────────────
class PreferenceRepository:

    @staticmethod
    def get(session: Session) -> Optional[Preference]:
        return session.query(Preference).filter_by(user_id=DEFAULT_USER_ID).first()

    @staticmethod
    def update(session: Session, **kwargs) -> Preference:
        pref = PreferenceRepository.get(session)
        if not pref:
            raise RuntimeError("No preferences record found — run init_db() first.")
        for key, value in kwargs.items():
            if hasattr(pref, key):
                setattr(pref, key, value)
        session.flush()
        return pref


# ── Reminder Repository ─────────────────────────────────────────────────────────
class ReminderRepository:

    @staticmethod
    def create(
        session: Session,
        text: str,
        trigger_at: datetime,
        is_recurring: bool = False,
        recurrence_rule: Optional[str] = None,
    ) -> Reminder:
        reminder = Reminder(
            user_id=DEFAULT_USER_ID,
            text=text,
            trigger_at=trigger_at,
            is_recurring=is_recurring,
            recurrence_rule=recurrence_rule,
            status="pending",
        )
        session.add(reminder)
        session.flush()
        logger.info("Reminder created: id=%s text=%r at=%s", reminder.id, text, trigger_at)
        return reminder

    @staticmethod
    def get_pending(session: Session) -> List[Reminder]:
        return (
            session.query(Reminder)
            .filter_by(user_id=DEFAULT_USER_ID, status="pending")
            .order_by(Reminder.trigger_at)
            .all()
        )

    @staticmethod
    def mark_fired(session: Session, reminder_id: int) -> None:
        reminder = session.get(Reminder, reminder_id)
        if reminder:
            reminder.status = "fired"
            reminder.notified_at = datetime.utcnow()
            session.flush()

    @staticmethod
    def cancel(session: Session, reminder_id: int) -> bool:
        reminder = session.get(Reminder, reminder_id)
        if reminder and reminder.status == "pending":
            reminder.status = "cancelled"
            session.flush()
            return True
        return False

    @staticmethod
    def delete_all(session: Session) -> int:
        count = session.query(Reminder).filter_by(user_id=DEFAULT_USER_ID).delete()
        session.flush()
        return count


# ── Conversation History Repository ────────────────────────────────────────────
class HistoryRepository:

    @staticmethod
    def log_turn(
        session: Session,
        user_input: str,
        intent: str,
        entities: dict,
        assistant_response: str,
        response_latency_ms: Optional[int] = None,
        session_id: str = "default",
    ) -> ConversationTurn:
        turn = ConversationTurn(
            user_id=DEFAULT_USER_ID,
            session_id=session_id,
            user_input=user_input,
            intent=intent,
            entities_json=json.dumps(entities) if entities else None,
            assistant_response=assistant_response,
            response_latency_ms=response_latency_ms,
            timestamp=datetime.utcnow(),
        )
        session.add(turn)
        session.flush()
        return turn

    @staticmethod
    def get_recent(session: Session, limit: int = 50, session_id: str = "default") -> List[ConversationTurn]:
        return (
            session.query(ConversationTurn)
            .filter_by(user_id=DEFAULT_USER_ID, session_id=session_id)
            .order_by(ConversationTurn.timestamp.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_books(session: Session) -> List[dict]:
        from sqlalchemy import func
        books = []
        results = session.query(
            ConversationTurn.session_id,
            func.max(ConversationTurn.timestamp).label("last_updated"),
            func.count(ConversationTurn.id).label("message_count")
        ).filter_by(user_id=DEFAULT_USER_ID).group_by(ConversationTurn.session_id).order_by(func.max(ConversationTurn.timestamp).desc()).all()
        
        for r in results:
            first_turn = session.query(ConversationTurn).filter_by(session_id=r.session_id).order_by(ConversationTurn.timestamp.asc()).first()
            title = "New Book"
            if first_turn:
                title = first_turn.custom_title if first_turn.custom_title else first_turn.user_input
            if len(title) > 30:
                title = title[:30] + "..."
            books.append({
                "id": r.session_id,
                "title": title,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
                "message_count": r.message_count
            })
        return books

    @staticmethod
    def rename_book(session: Session, session_id: str, new_title: str) -> bool:
        first_turn = session.query(ConversationTurn).filter_by(session_id=session_id).order_by(ConversationTurn.timestamp.asc()).first()
        if first_turn:
            first_turn.custom_title = new_title
            session.flush()
            return True
        return False

    @staticmethod
    def search(session: Session, query: str, limit: int = 20) -> List[ConversationTurn]:
        like = f"%{query}%"
        return (
            session.query(ConversationTurn)
            .filter_by(user_id=DEFAULT_USER_ID)
            .filter(
                ConversationTurn.user_input.ilike(like)
                | ConversationTurn.assistant_response.ilike(like)
            )
            .order_by(ConversationTurn.timestamp.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete(session: Session, turn_id: int) -> bool:
        """Delete a single conversation turn by its primary key."""
        turn = session.get(ConversationTurn, turn_id)
        if turn:
            session.delete(turn)
            session.flush()
            return True
        return False

    @staticmethod
    def clear_all(session: Session) -> int:
        count = session.query(ConversationTurn).filter_by(user_id=DEFAULT_USER_ID).delete()
        session.flush()
        return count

