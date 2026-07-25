"""
PRISM Voice Assistant — Intent Classifier
Rule-based regex engine enriched with spaCy NER for entity extraction.
Fast, deterministic, and requires no training data.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from app.modules.base_module import IntentResult
from app.nlp.entity_extractor import EntityExtractor
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Intent rule table — ordered from most specific to most general ─────────────
# Each entry: (compiled_pattern, intent_label)
_INTENT_RULES: List[Tuple[re.Pattern, str]] = [
    # Weather
    (re.compile(r"\b(weather|forecast|temperature|temp|hot|cold|rain|sunny|humid|wind)\b", re.I), "get_weather"),

    # News
    (re.compile(r"\b(news|headline|headlines|latest|breaking|happening|update|updates)\b", re.I), "get_news"),

    # Reminders — set
    (re.compile(r"\b(remind\s+me|set\s+(a\s+)?(reminder|alarm)|alarm\s+for|wake\s+me)\b", re.I), "set_reminder"),

    # Reminders — list
    (re.compile(r"\b(show\s+(my\s+)?reminders?|list\s+reminders?|what(\'s| is| are)\s+(my\s+)?reminders?|upcoming\s+(reminders?|alarms?))\b", re.I), "list_reminders"),

    # Reminders — cancel
    (re.compile(r"\b(cancel|delete|remove)\s+(my\s+)?(reminder|alarm)\b", re.I), "cancel_reminder"),

    # Chitchat — time/date
    (re.compile(r"\b(what\s+time|what\'s\s+the\s+time|current\s+time|what\s+(is|\'s)\s+the\s+date|today\'s\s+date)\b", re.I), "chitchat_time"),

    # Chitchat — jokes
    (re.compile(r"\b(joke|funny|laugh|humor|make\s+me\s+(laugh|smile)|something\s+funny)\b", re.I), "chitchat_joke"),

    # Chitchat — identity / capabilities
    (re.compile(r"\b(who\s+are\s+you|what\s+(are|can)\s+you|your\s+name|introduce\s+yourself|what\s+do\s+you\s+do)\b", re.I), "chitchat_identity"),

    # Chitchat — greetings
    (re.compile(r"^\s*(hello|hi|hey|good\s+(morning|afternoon|evening|night)|howdy|what\'s\s+up|sup|greetings)\b", re.I), "chitchat_greet"),

    # Chitchat — farewell
    (re.compile(r"\b(bye|goodbye|see\s+you|farewell|good\s+night|exit|quit|close)\b", re.I), "chitchat_bye"),

    # Clear history
    (re.compile(r"\b(clear\s+(my\s+)?(history|conversation|chat)|delete\s+my\s+data|wipe\s+(history|data))\b", re.I), "clear_history"),
]


class IntentClassifier:
    """
    Classifies user input into one of the PRISM intent labels.
    Loads spaCy lazily to avoid startup delay.
    """

    def __init__(self) -> None:
        self._nlp = None
        self._extractor = EntityExtractor()

    def classify(self, text: str) -> IntentResult:
        """
        Classify text and extract entities in a single pass.
        Returns IntentResult with intent label and entities dict.
        """
        text_stripped = text.strip()
        if not text_stripped:
            return IntentResult(intent="unknown", raw_text=text)

        # Run spaCy for NER if available
        doc = None
        try:
            if self._nlp is None:
                import spacy
                self._nlp = spacy.load("en_core_web_sm")
            doc = self._nlp(text_stripped)
        except Exception as exc:
            logger.warning("spaCy unavailable: %s — using regex only.", exc)

        # Match intent
        intent = self._match_intent(text_stripped)

        # Extract entities relevant to the intent
        entities = self._extract_entities(text_stripped, intent, doc)

        logger.debug("Intent: %r | Entities: %s | Text: %r", intent, entities, text_stripped)
        return IntentResult(intent=intent, entities=entities, confidence=1.0, raw_text=text_stripped)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _match_intent(self, text: str) -> str:
        for pattern, intent in _INTENT_RULES:
            if pattern.search(text):
                return intent
        return "unknown"

    def _extract_entities(self, text: str, intent: str, doc) -> dict:
        entities: dict = {}

        if intent == "get_weather":
            city = self._extractor.extract_city(text, doc)
            if city:
                entities["city"] = city
            dt = self._extractor.extract_datetime(text)
            if dt:
                entities["date"] = dt.isoformat()

        elif intent in ("set_reminder", "cancel_reminder"):
            reminder_text = self._extractor.extract_reminder_text(text)
            if reminder_text:
                entities["reminder_text"] = reminder_text
            dt = self._extractor.extract_datetime(text)
            if dt:
                entities["trigger_at"] = dt.isoformat()
            num = self._extractor.extract_number(text)
            if num:
                entities["number"] = num

        elif intent == "get_news":
            entities["category"] = self._extractor.extract_news_category(text)

        elif intent == "cancel_reminder":
            num = self._extractor.extract_number(text)
            if num:
                entities["reminder_id"] = num

        return entities
