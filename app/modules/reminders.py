"""
PRISM Voice Assistant — Reminders Skill Module
Creates, lists, and cancels reminders. Schedules APScheduler jobs.
On each app start, reloads all pending reminders from SQLite.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from app.db.database import get_session
from app.db.repository import ReminderRepository
from app.modules.base_module import IntentResult, SkillModule, SkillResponse
from app.utils.event_bus import EventBus, EVENT_REMINDER_FIRE
from app.utils.helpers import format_datetime, friendly_time_delta
from app.utils.logger import get_logger

logger = get_logger(__name__)
bus = EventBus.instance()


class ReminderModule(SkillModule):

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler(daemon=True)
        self._scheduler.start()
        self._lock = threading.Lock()
        self._reload_pending()

    def can_handle(self, intent: str) -> bool:
        return intent in ("set_reminder", "list_reminders", "cancel_reminder")

    def execute(self, intent_result: IntentResult) -> SkillResponse:
        intent = intent_result.intent
        if intent == "set_reminder":
            return self._create(intent_result)
        elif intent == "list_reminders":
            return self._list()
        elif intent == "cancel_reminder":
            return self._cancel(intent_result)
        return SkillResponse(text="I couldn't handle that reminder request.")

    # ── Create ─────────────────────────────────────────────────────────────────

    def _create(self, intent_result: IntentResult) -> SkillResponse:
        entities = intent_result.entities
        trigger_str: Optional[str] = entities.get("trigger_at")
        reminder_text: str = entities.get("reminder_text") or intent_result.raw_text

        if not trigger_str:
            return SkillResponse(
                text="I need to know when to remind you. Please include a time, like 'remind me to call mom at 6 PM'.",
            )

        trigger_at = datetime.fromisoformat(trigger_str)
        if trigger_at <= datetime.now():
            return SkillResponse(
                text="That time has already passed. Please specify a future time for the reminder.",
            )

        with get_session() as session:
            reminder = ReminderRepository.create(
                session, text=reminder_text, trigger_at=trigger_at
            )
            reminder_id = reminder.id

        self._schedule_job(reminder_id, trigger_at, reminder_text)

        friendly = format_datetime(trigger_at)
        delta = friendly_time_delta(trigger_at)
        text = f"Got it! I'll remind you to '{reminder_text}' on {friendly} ({delta})."

        card_data = {
            "id": reminder_id,
            "text": reminder_text,
            "trigger_at": trigger_at.isoformat(),
            "friendly_time": friendly,
            "delta": delta,
        }

        return SkillResponse(text=text, card_type="reminder", card_data=card_data)

    # ── List ───────────────────────────────────────────────────────────────────

    def _list(self) -> SkillResponse:
        with get_session() as session:
            reminders = ReminderRepository.get_pending(session)

        if not reminders:
            return SkillResponse(
                text="You have no pending reminders.",
                card_type="reminder",
                card_data={"reminders": []},
            )

        items = []
        for r in reminders[:5]:
            items.append({
                "id": r.id,
                "text": r.text,
                "trigger_at": r.trigger_at.isoformat(),
                "friendly_time": format_datetime(r.trigger_at),
                "delta": friendly_time_delta(r.trigger_at),
            })

        if len(reminders) == 1:
            text = f"You have 1 reminder: {reminders[0].text} at {format_datetime(reminders[0].trigger_at)}."
        else:
            spoken = "; ".join(f"{r.text} {friendly_time_delta(r.trigger_at)}" for r in reminders[:3])
            text = f"You have {len(reminders)} pending reminders: {spoken}."
            if len(reminders) > 3:
                text += f" And {len(reminders) - 3} more on screen."

        return SkillResponse(
            text=text, card_type="reminder", card_data={"reminders": items}
        )

    # ── Cancel ─────────────────────────────────────────────────────────────────

    def _cancel(self, intent_result: IntentResult) -> SkillResponse:
        reminder_id = intent_result.entities.get("reminder_id") or intent_result.entities.get("number")

        if not reminder_id:
            return SkillResponse(
                text="Please specify which reminder to cancel by its number. "
                     "Say 'list my reminders' to see them first.",
            )

        with get_session() as session:
            cancelled = ReminderRepository.cancel(session, int(reminder_id))

        if cancelled:
            job_id = f"reminder_{reminder_id}"
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass
            return SkillResponse(text=f"Reminder {reminder_id} has been cancelled.")
        else:
            return SkillResponse(text=f"I couldn't find reminder {reminder_id} to cancel.")

    # ── Scheduler helpers ──────────────────────────────────────────────────────

    def _schedule_job(self, reminder_id: int, trigger_at: datetime, text: str) -> None:
        job_id = f"reminder_{reminder_id}"
        self._scheduler.add_job(
            func=self._fire_reminder,
            trigger=DateTrigger(run_date=trigger_at),
            id=job_id,
            args=[reminder_id, text],
            replace_existing=True,
            misfire_grace_time=300,
        )
        logger.info("Scheduled reminder job %s for %s", job_id, trigger_at)

    def _fire_reminder(self, reminder_id: int, text: str) -> None:
        logger.info("Firing reminder %s: %r", reminder_id, text)

        # Mark as fired in DB
        with get_session() as session:
            ReminderRepository.mark_fired(session, reminder_id)

        # OS notification
        try:
            from plyer import notification
            notification.notify(
                title="PRISM Reminder",
                message=text,
                app_name="PRISM Voice Assistant",
                timeout=10,
            )
        except Exception as exc:
            logger.warning("OS notification failed: %s", exc)

        # Publish to event bus (UI + TTS will handle)
        bus.publish(EVENT_REMINDER_FIRE, {"text": text, "id": reminder_id})

    def _reload_pending(self) -> None:
        """On startup, reload all pending reminders from DB into APScheduler."""
        now = datetime.now()
        try:
            with get_session() as session:
                pending = ReminderRepository.get_pending(session)

            overdue = []
            for r in pending:
                if r.trigger_at <= now:
                    # Missed while app was closed — fire immediately
                    overdue.append((r.id, r.text))
                else:
                    self._schedule_job(r.id, r.trigger_at, r.text)

            if overdue:
                logger.info("Found %d overdue reminder(s) — firing.", len(overdue))
                for rid, rtext in overdue:
                    # Slight delay so the UI has time to initialize
                    import threading
                    t = threading.Timer(3.0, self._fire_reminder, args=[rid, rtext])
                    t.daemon = True
                    t.start()

        except Exception as exc:
            logger.error("Failed to reload pending reminders: %s", exc)
