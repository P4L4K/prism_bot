"""
PRISM Voice Assistant — News Skill Module
Fetches top headlines from NewsAPI.ai (Event Registry) with a 15-minute in-memory cache.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

import httpx

from app.core.config import NEWS_API_KEY, NEWS_API_TIMEOUT, NEWS_CACHE_TTL, NEWS_HEADLINE_COUNT
from app.modules.base_module import IntentResult, SkillModule, SkillResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

NEWSAPI_BASE = "https://eventregistry.org/api/v1/article/getArticles"

# Mapping of standard categories to Event Registry DMOZ category URIs
CATEGORY_MAPPING = {
    "business": "dmoz/Business",
    "entertainment": "dmoz/Arts",
    "health": "dmoz/Health",
    "science": "dmoz/Science",
    "sports": "dmoz/Sports",
    "technology": "dmoz/Computers",
}


class NewsModule(SkillModule):

    def __init__(self, news_location: Optional[str] = None) -> None:
        self.news_location = news_location
        self._cache: Dict[str, Tuple[float, List[dict]]] = {}  # category -> (ts, articles)
        self._last_headlines: List[dict] = []  # stale fallback

    def can_handle(self, intent: str) -> bool:
        return intent == "get_news"

    def execute(self, intent_result: IntentResult) -> SkillResponse:
        category = intent_result.entities.get("category", "general")

        try:
            articles = self._get_headlines(category)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                return SkillResponse(
                    text="Your NewsAPI key is unauthorized or invalid. Please verify that you have entered a valid key in the dot env file.",
                    error="Unauthorized API Key"
                )
            articles = []
        except ValueError as exc:
            return SkillResponse(
                text=str(exc),
                error="Configuration Error"
            )

        if not articles:
            stale_note = ""
            if self._last_headlines:
                articles = self._last_headlines
                stale_note = " (These are cached headlines — news feed currently unavailable.)"
            else:
                return SkillResponse(
                    text="I couldn't retrieve news headlines right now. Please check your NewsAPI key.",
                    error="No articles available",
                )
        else:
            self._last_headlines = articles

        # ── Spoken response: top 3 headlines ──────────────────────────────────
        text = f"Here are the top {category} news headlines:\n\n"
        for i, a in enumerate(articles[:3], 1):
            text += f"• {a['title']}\n  ({a['source']})\n\n"
            
        if len(articles) > 3:
            text += f"And {len(articles) - 3} more headlines are available."

        card_data = {
            "category": category.capitalize(),
            "articles": articles[:NEWS_HEADLINE_COUNT],
        }

        return SkillResponse(text=text, card_type="news", card_data=card_data)

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _get_headlines(self, category: str) -> List[dict]:
        cached = self._cache.get(category)
        if cached and time.time() - cached[0] < NEWS_CACHE_TTL:
            logger.debug("News cache hit for category=%s", category)
            return cached[1]

        if not NEWS_API_KEY or NEWS_API_KEY == "your_newsapi_key_here":
            logger.warning("NEWS_API_KEY not set or invalid.")
            raise ValueError("The News API key is not configured in the settings.")

        params = {
            "action": "getArticles",
            "apiKey": NEWS_API_KEY,
            "articlesPage": 1,
            "articlesCount": NEWS_HEADLINE_COUNT,
            "articlesSortBy": "date",
            "articlesSortByAsc": "false",
            "resultType": "articles",
            "lang": "eng",
        }

        category_uri = CATEGORY_MAPPING.get(category.lower())
        if category_uri:
            params["categoryUri"] = category_uri
            
        if self.news_location:
            params["keyword"] = self.news_location

        try:
            with httpx.Client(timeout=NEWS_API_TIMEOUT) as client:
                resp = client.get(NEWSAPI_BASE, params=params)
                resp.raise_for_status()
                data = resp.json()

            articles_data = data.get("articles", {}).get("results", [])
            articles = [
                {
                    "title": a.get("title", "Untitled"),
                    "source": a.get("source", {}).get("title", "Unknown"),
                    "url": a.get("url", ""),
                    "published_at": f"{a.get('date', '')} {a.get('time', '')}".strip(),
                    "description": a.get("body") or "",
                }
                for a in articles_data
                if a.get("title")
            ]
            self._cache[category] = (time.time(), articles)
            return articles

        except httpx.HTTPStatusError as exc:
            logger.error("NewsAPI.ai HTTP error %s: %s", exc.response.status_code, exc)
            raise
        except Exception as exc:
            logger.error("NewsAPI.ai fetch failed: %s", exc)
            return []
