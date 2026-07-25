"""
PRISM Voice Assistant — Skill Module Base
Defines the SkillModule ABC and shared data contracts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class IntentResult:
    """Output of the NLP intent classification stage."""
    intent: str
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    raw_text: str = ""


@dataclass
class SkillResponse:
    """Output of a Skill Module's execute() call."""
    text: str                            # Natural language response (for TTS + chat)
    card_type: Optional[str] = None      # 'weather' | 'news' | 'reminder' | None
    card_data: Optional[Dict] = None     # Structured payload for rich UI card
    error: Optional[str] = None          # Non-None if module failed gracefully


class SkillModule(ABC):
    """Abstract base class that all PRISM skill modules must implement."""

    @abstractmethod
    def can_handle(self, intent: str) -> bool:
        """Return True if this module handles the given intent label."""
        ...

    @abstractmethod
    def execute(self, intent_result: IntentResult) -> SkillResponse:
        """
        Execute the skill for the given intent + entities.
        Must never raise — catch all exceptions and return error SkillResponse.
        """
        ...
