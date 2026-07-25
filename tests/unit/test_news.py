from unittest.mock import MagicMock, patch
import pytest
from app.modules.news import NewsModule
from app.modules.base_module import IntentResult

def test_news_module_execute_success():
    module = NewsModule()
    intent_result = IntentResult(intent="get_news", entities={"category": "technology"})

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "articles": {
            "results": [
                {
                    "title": "Tech Article 1",
                    "url": "https://tech1.com",
                    "date": "2026-07-09",
                    "time": "12:00:00",
                    "body": "This is tech article 1 body.",
                    "source": {
                        "title": "TechCrunch"
                    }
                },
                {
                    "title": "Tech Article 2",
                    "url": "https://tech2.com",
                    "date": "2026-07-09",
                    "time": "13:00:00",
                    "body": "This is tech article 2 body.",
                    "source": {
                        "title": "Wired"
                    }
                }
            ]
        }
    }

    with patch("httpx.Client.get") as mock_get, \
         patch("app.modules.news.NEWS_API_KEY", "dummy_key"):
        mock_get.return_value = mock_response

        response = module.execute(intent_result)

        assert response.error is None
        assert "Tech Article 1" in response.text
        assert "Tech Article 2" in response.text
        assert response.card_type == "news"
        assert response.card_data["category"] == "Technology"
        assert len(response.card_data["articles"]) == 2
        assert response.card_data["articles"][0]["title"] == "Tech Article 1"
        assert response.card_data["articles"][0]["source"] == "TechCrunch"
        assert response.card_data["articles"][0]["published_at"] == "2026-07-09 12:00:00"

def test_news_module_execute_no_api_key():
    module = NewsModule()
    intent_result = IntentResult(intent="get_news", entities={})

    with patch("app.modules.news.NEWS_API_KEY", ""):
        response = module.execute(intent_result)
        assert response.error == "No articles available"
        assert "check your NewsAPI key" in response.text
