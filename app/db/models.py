"""
PRISM Voice Assistant — SQLAlchemy ORM Models
Defines the four core database tables.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(100), nullable=False, default="User")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    preferences       = relationship("Preference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reminders         = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    conversation_turns = relationship("ConversationTurn", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name!r}>"


class Preference(Base):
    __tablename__ = "preferences"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    user_id            = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    voice_rate         = Column(Integer, nullable=False, default=175)
    voice_volume       = Column(Float, nullable=False, default=1.0)
    temperature_unit   = Column(String(1), nullable=False, default="C")
    news_category      = Column(String(50), nullable=False, default="general")
    news_location      = Column(String(100), nullable=True)
    theme              = Column(String(20), nullable=False, default="dark")
    wake_word_enabled  = Column(Boolean, nullable=False, default=False)
    wake_word_model    = Column(String(200), nullable=False, default="alexa")
    stt_engine         = Column(String(20), nullable=False, default="google")
    default_city       = Column(String(100), nullable=True)

    user = relationship("User", back_populates="preferences")

    def __repr__(self) -> str:
        return f"<Preference user_id={self.user_id}>"


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (Index("ix_reminders_trigger_at", "trigger_at"),)

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    text            = Column(Text, nullable=False)
    trigger_at      = Column(DateTime, nullable=False)
    is_recurring    = Column(Boolean, nullable=False, default=False)
    recurrence_rule = Column(String(200), nullable=True)
    status          = Column(String(20), nullable=False, default="pending")  # pending | fired | cancelled
    created_at      = Column(DateTime, nullable=False, default=datetime.utcnow)
    notified_at     = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="reminders")

    def __repr__(self) -> str:
        return f"<Reminder id={self.id} text={self.text!r} at={self.trigger_at}>"


class ConversationTurn(Base):
    __tablename__ = "conversation_history"
    __table_args__ = (Index("ix_conversation_history_timestamp", "timestamp"),)

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id          = Column(String(50), nullable=False, default="default")
    custom_title        = Column(String(100), nullable=True)
    user_input          = Column(Text, nullable=False)
    intent              = Column(String(100), nullable=False)
    entities_json       = Column(Text, nullable=True)          # JSON string
    assistant_response  = Column(Text, nullable=False)
    response_latency_ms = Column(Integer, nullable=True)
    timestamp           = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="conversation_turns")

    @property
    def entities(self) -> dict:
        if self.entities_json:
            try:
                return json.loads(self.entities_json)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @entities.setter
    def entities(self, value: dict) -> None:
        self.entities_json = json.dumps(value) if value else None

    def __repr__(self) -> str:
        return f"<ConversationTurn id={self.id} intent={self.intent!r}>"
