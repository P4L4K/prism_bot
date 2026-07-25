"""
PRISM Voice Assistant — Chitchat Skill Module
Handles greetings, jokes, time/date, identity, and farewells.
Fully offline — no external API calls.
"""

from __future__ import annotations

import random
from datetime import datetime

from app.core.config import ASSISTANT_NAME
from app.modules.base_module import IntentResult, SkillModule, SkillResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

_GREETINGS = [
    f"Hello! I'm {ASSISTANT_NAME}, your personal voice assistant. How can I help you today?",
    f"Hi there! {ASSISTANT_NAME} at your service. What can I do for you?",
    f"Hey! Great to hear from you. What would you like to do?",
    f"Good to see you! I'm ready to help. What's on your mind?",
    f"Hello! What can I assist you with today?",
]

_FAREWELLS = [
    f"Goodbye! {ASSISTANT_NAME} signing off. Have a wonderful day!",
    "See you later! Take care.",
    "Farewell! Come back anytime you need assistance.",
    "Goodbye! It was a pleasure helping you.",
]

_JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "What do you call a fish without eyes? A fsh.",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "I asked Siri to tell me a joke. She said 'Siri-ously?'",
    "Why can't you give Elsa a balloon? Because she'll let it go.",
    "What do you call a bear with no teeth? A gummy bear!",
    "Why did the bicycle fall over? Because it was two-tired.",
    "How do you organize a space party? You planet.",
    "Why don't eggs tell jokes? They'd crack each other up.",
    "What's a computer's favorite snack? Microchips!",
    "I'm reading a book on anti-gravity. It's impossible to put down.",
    "Why did the math book look so sad? Because it had too many problems.",
    "What do you call a fake noodle? An impasta!",
    "Why did the coffee file a police report? It got mugged.",
    "I tried to catch some fog earlier. I mist.",
    "What do you call cheese that isn't yours? Nacho cheese!",
    "Why don't skeletons fight each other? They don't have the guts.",
    "What do you call a dinosaur that crashes their car? Tyrannosaurus wrecks.",
]

_CAPABILITIES = f"""I'm {ASSISTANT_NAME}, your personal voice assistant. Here's what I can do:
🌤 Check weather — try 'What's the weather in Paris?'
📰 Get news — try 'Latest technology news'
⏰ Set reminders — try 'Remind me to call mom at 6 PM'
📋 List reminders — try 'Show my reminders'
💬 Casual conversation — just say hello!
You can speak to me or type your commands below."""


class ChitchatModule(SkillModule):

    def can_handle(self, intent: str) -> bool:
        return intent in (
            "chitchat_greet", "chitchat_joke", "chitchat_time",
            "chitchat_identity", "chitchat_bye", "unknown",
        )

    def execute(self, intent_result: IntentResult) -> SkillResponse:
        intent = intent_result.intent

        if intent == "chitchat_greet":
            return SkillResponse(text=random.choice(_GREETINGS))

        elif intent == "chitchat_joke":
            return SkillResponse(text=random.choice(_JOKES))

        elif intent == "chitchat_time":
            now = datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            time_str = now.strftime("%I:%M %p")
            return SkillResponse(text=f"It's {time_str} on {date_str}.")

        elif intent == "chitchat_identity":
            return SkillResponse(text=_CAPABILITIES)

        elif intent == "chitchat_bye":
            return SkillResponse(
                text=random.choice(_FAREWELLS),
                card_type="bye",
                card_data={"exit": True},
            )

        else:  # unknown
            fallbacks = [
                "I'm not sure how to help with that. Try asking about weather, news, or reminders.",
                f"I didn't quite catch that. Say 'what can you do' to see {ASSISTANT_NAME}'s capabilities.",
                "Hmm, I'm not sure about that one. You can ask me about weather, news, or set a reminder.",
                "I didn't understand that command. Try rephrasing or ask 'what can you do'.",
            ]
            return SkillResponse(text=random.choice(fallbacks))
