"""
PRISM Voice Assistant — Entity Extractor
Extracts structured entities (datetime, city, number, category) from raw text.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional

import dateparser


class EntityExtractor:
    """Extracts typed entities from a natural-language string."""

    # ── News categories ────────────────────────────────────────────────────────
    NEWS_CATEGORIES = {
        "business", "entertainment", "general", "health",
        "science", "sports", "technology",
    }

    # ── City pattern: capitalized word(s) after location prepositions ──────────
    _CITY_RE = re.compile(
        r"\b(?:in|for|at|near|around|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        re.IGNORECASE,
    )

    # ── Number pattern ─────────────────────────────────────────────────────────
    _NUMBER_RE = re.compile(r"\b(\d+)\b")

    def extract_datetime(self, text: str) -> Optional[datetime]:
        """
        Parse natural date/time expressions like 'tomorrow at 6 PM',
        'in 30 minutes', 'next Monday', '8 PM today'.
        Returns None if no date/time found.
        """
        settings = {
            "PREFER_DATES_FROM": "future",
            "RETURN_AS_TIMEZONE_AWARE": False,
            "RELATIVE_BASE": datetime.now(),
        }
        try:
            result = dateparser.parse(text, settings=settings)
            # Sanity: don't return dates more than 1 year in the future
            if result and result > datetime.now() + timedelta(days=365):
                return None
            return result
        except Exception:
            return None

    def extract_city(self, text: str, spacy_doc=None) -> Optional[str]:
        """
        Extract a city/location name. Tries spaCy NER (GPE entities) first,
        then falls back to regex pattern matching.
        """
        # spaCy NER
        if spacy_doc is not None:
            for ent in spacy_doc.ents:
                if ent.label_ in ("GPE", "LOC"):
                    return ent.text.strip().title()

        # Regex fallback
        match = self._CITY_RE.search(text)
        if match:
            return match.group(1).strip().title()

        return None

    def extract_number(self, text: str) -> Optional[int]:
        """Extract the first integer found in text."""
        match = self._NUMBER_RE.search(text)
        return int(match.group(1)) if match else None

    def extract_news_category(self, text: str) -> str:
        """Return the news category mentioned in text, or 'general'."""
        text_lower = text.lower()
        for cat in self.NEWS_CATEGORIES:
            if cat in text_lower:
                return cat
        return "general"

    def extract_reminder_text(self, text: str) -> str:
        """
        Strip 'remind me to', 'set a reminder to' etc. to get the core reminder message.
        """
        patterns = [
            r"remind(?:\s+me)?\s+to\s+(.+?)(?:\s+at\s+|\s+in\s+|\s+on\s+|$)",
            r"set\s+(?:a\s+)?(?:reminder|alarm)\s+(?:to\s+)?(.+?)(?:\s+at\s+|\s+in\s+|\s+on\s+|$)",
            r"alarm\s+(?:for\s+)?(.+?)(?:\s+at\s+|\s+in\s+|\s+on\s+|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        # Fallback: return trimmed text
        return text.strip()
