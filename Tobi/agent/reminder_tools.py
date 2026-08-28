"""
Tobi Reminder Tool Implementations

Async callable functions that back the reminder-related Claude tool schemas.
Claude calls these via tool_use when the user says things like:
  "remind me to follow up with OPES on Friday"
  "set an alarm for 7am tomorrow"
  "show me my upcoming reminders"
  "cancel reminder 3"
  "snooze that for 20 minutes"

Each function returns a human-readable string that Claude incorporates
into its response.  Heavy date parsing is intentionally delegated to
Claude — these tools receive already-resolved timestamps (epoch floats)
from the LLM layer rather than raw natural-language strings.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("Tobi.agent.reminders")

# ── lazy import guard ─────────────────────────────────────────────────────────
def _store():
    from Tobi.memory import reminders_store as rs
    return rs


# ─────────────────────────────────── CREATE ──────────────────────────────────

async def create_reminder(
    content: str,
    due_at_iso: str,
    is_alarm: bool = False,
    recurrence: str = "none",
    playback_mode: str = "tobi_voice",
) -> str:
    """
    Create a new reminder.

    Args:
        content:      Plain-text description of what to remind about.
        due_at_iso:   ISO-8601 datetime string (e.g. "2026-09-01T09:00:00").
                      Claude resolves relative phrases ("Friday", "tomorrow at 9am")
                      to an absolute datetime before calling this tool.
        is_alarm:     True = full alarm that wakes the device; False = soft notification.
        recurrence:   "none" | "daily" | "weekly" | "weekdays" | "monthly"
        playback_mode: "tobi_voice" | "own_voice"
                       Use "own_voice" only when audio_url will be set afterwards
                       via the /reminders/{id}/audio upload endpoint.
    """
    rs = _store()
    try:
        due_dt = datetime.fromisoformat(due_at_iso)
        due_ts = due_dt.timestamp()
    except (ValueError, TypeError) as e:
        return f"Could not parse due date '{due_at_iso}': {e}. Please provide an ISO-8601 datetime."

    try:
        rec = rs.Recurrence(recurrence)
    except ValueError:
        rec = rs.Recurrence.NONE

    try:
        pm = rs.PlaybackMode(playback_mode)
    except ValueError:
        pm = rs.PlaybackMode.TOBI_VOICE

    reminder = rs.create_reminder(
        content=content,
        due_at=due_ts,
        playback_mode=pm,
        is_alarm=is_alarm,
        recurrence=rec,
    )

    due_fmt = due_dt.strftime("%A, %B %d at %I:%M %p").replace(" 0", " ")
    alarm_label = "alarm" if is_alarm else "reminder"
    rec_label = f" (repeats {rec.value})" if rec != rs.Recurrence.NONE else ""
    return (
        f"Done. {alarm_label.capitalize()} set for {due_fmt}{rec_label}. "
        f"ID: {reminder.id}. Content: \"{content}\""
    )


# ─────────────────────────────────── LIST ────────────────────────────────────

async def list_reminders(upcoming_only: bool = True, hours: int = 48) -> str:
    """
    List reminders.

    Args:
        upcoming_only: If True, only return pending/snoozed reminders due
                       within the next `hours` hours.  If False, return all
                       non-deleted reminders.
        hours:         Look-ahead window when upcoming_only=True (default 48h).
    """
    rs = _store()
    if upcoming_only:
        reminders = rs.get_upcoming_reminders(hours=hours)
        header = f"Upcoming reminders (next {hours}h)"
    else:
        reminders = rs.get_all_reminders(include_deleted=False)
        header = "All active reminders"

    if not reminders:
        return "No reminders found." if not upcoming_only else f"Nothing due in the next {hours} hours."

    lines = [f"{header} — {len(reminders)} total:"]
    for r in reminders:
        due_fmt = datetime.fromtimestamp(r.due_at).strftime("%a %b %d, %I:%M %p")
        status = "" if r.status.value == "pending" else f" [{r.status.value}]"
        rec = f" ↻{r.recurrence.value}" if r.recurrence != rs.Recurrence.NONE else ""
        alarm = " 🔔" if r.is_alarm else ""
        audio = " 🎙" if r.audio_url else ""
        lines.append(f"  [{r.id}] {due_fmt}{status}{rec}{alarm}{audio} — {r.content}")

    return "\n".join(lines)


# ─────────────────────────────────── DISMISS ─────────────────────────────────

async def dismiss_reminder(reminder_id: int) -> str:
    """
    Mark a reminder as dismissed (it will not fire again unless it recurs).

    Args:
        reminder_id: The numeric ID of the reminder (shown in list_reminders).
    """
    rs = _store()
    reminder = rs.get_reminder(reminder_id)
    if reminder is None:
        return f"No reminder found with ID {reminder_id}."

    if reminder.recurrence != rs.Recurrence.NONE:
        # Advance to next occurrence instead of dismissing outright
        updated = rs.advance_recurring_reminder(reminder)
        if updated:
            next_fmt = datetime.fromtimestamp(updated.due_at).strftime("%a %b %d at %I:%M %p")
            return (
                f"Reminder {reminder_id} dismissed. "
                f"Next occurrence: {next_fmt} (recurs {reminder.recurrence.value})."
            )

    rs.update_reminder_status(reminder_id, rs.ReminderStatus.DISMISSED)
    return f"Reminder {reminder_id} dismissed: \"{reminder.content}\""


# ─────────────────────────────────── SNOOZE ──────────────────────────────────

async def snooze_reminder(reminder_id: int, minutes: int = 10) -> str:
    """
    Snooze a reminder for N minutes from now.

    Args:
        reminder_id: The numeric ID of the reminder.
        minutes:     How many minutes to snooze for (default 10).
    """
    rs = _store()
    reminder = rs.get_reminder(reminder_id)
    if reminder is None:
        return f"No reminder found with ID {reminder_id}."

    if reminder.status not in (rs.ReminderStatus.PENDING, rs.ReminderStatus.FIRED, rs.ReminderStatus.SNOOZED):
        return f"Reminder {reminder_id} is {reminder.status.value} and cannot be snoozed."

    snooze_until = time.time() + minutes * 60
    rs.update_reminder_status(
        reminder_id,
        rs.ReminderStatus.SNOOZED,
        snooze_until=snooze_until,
    )
    wake_fmt = datetime.fromtimestamp(snooze_until).strftime("%I:%M %p")
    return f"Snoozed for {minutes} minutes — will remind again at {wake_fmt}."


# ─────────────────────────────────── DELETE ──────────────────────────────────

async def delete_reminder(reminder_id: int) -> str:
    """
    Permanently delete (soft-delete) a reminder.

    Args:
        reminder_id: The numeric ID of the reminder.
    """
    rs = _store()
    reminder = rs.get_reminder(reminder_id)
    if reminder is None:
        return f"No reminder found with ID {reminder_id}."

    rs.delete_reminder(reminder_id)
    return f"Reminder {reminder_id} deleted: \"{reminder.content}\""


# ─────────────────────────────────── UPDATE ──────────────────────────────────

async def update_reminder(
    reminder_id: int,
    content: Optional[str] = None,
    due_at_iso: Optional[str] = None,
    recurrence: Optional[str] = None,
    is_alarm: Optional[bool] = None,
) -> str:
    """
    Update the content, time, recurrence, or alarm flag of an existing reminder.

    Only the fields you pass will be changed — omit the ones you want to keep.

    Args:
        reminder_id:  ID of the reminder to update.
        content:      New reminder text (optional).
        due_at_iso:   New ISO-8601 due datetime (optional).
        recurrence:   New recurrence rule (optional).
        is_alarm:     Toggle alarm mode (optional).
    """
    from Tobi.config import settings  # noqa: F401 — ensures DATA_DIR exists
    rs = _store()

    reminder = rs.get_reminder(reminder_id)
    if reminder is None:
        return f"No reminder found with ID {reminder_id}."

    import sqlite3
    DB_PATH = rs.DB_PATH

    fields: list[str] = []
    values: list = []

    if content is not None:
        fields.append("content = ?")
        values.append(content)

    if due_at_iso is not None:
        try:
            due_ts = datetime.fromisoformat(due_at_iso).timestamp()
            fields.append("due_at = ?")
            values.append(due_ts)
        except (ValueError, TypeError) as e:
            return f"Could not parse due date '{due_at_iso}': {e}"

    if recurrence is not None:
        try:
            rec_val = rs.Recurrence(recurrence).value
        except ValueError:
            rec_val = rs.Recurrence.NONE.value
        fields.append("recurrence = ?")
        values.append(rec_val)

    if is_alarm is not None:
        fields.append("is_alarm = ?")
        values.append(int(is_alarm))

    if not fields:
        return "No changes specified."

    values.append(reminder_id)
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(f"UPDATE reminders SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        conn.close()
    except Exception as e:
        return f"Failed to update reminder {reminder_id}: {e}"

    updated = rs.get_reminder(reminder_id)
    due_fmt = datetime.fromtimestamp(updated.due_at).strftime("%a %b %d at %I:%M %p")
    return f"Reminder {reminder_id} updated. Due: {due_fmt}. Content: \"{updated.content}\""


# ──────────────────────────── MARK FIRED (internal) ──────────────────────────

async def mark_reminder_fired(reminder_id: int) -> str:
    """
    Internal: mark a reminder as fired after it has been delivered.
    Advances recurring reminders automatically.
    """
    rs = _store()
    reminder = rs.get_reminder(reminder_id)
    if reminder is None:
        return f"Reminder {reminder_id} not found."

    if reminder.recurrence != rs.Recurrence.NONE:
        updated = rs.advance_recurring_reminder(reminder)
        if updated:
            next_fmt = datetime.fromtimestamp(updated.due_at).strftime("%a %b %d at %I:%M %p")
            return f"Recurring reminder {reminder_id} fired. Next: {next_fmt}."

    rs.update_reminder_status(reminder_id, rs.ReminderStatus.FIRED, last_fired_at=time.time())
    return f"Reminder {reminder_id} marked as fired."


# ──────────────────────────── TOOL SCHEMAS ───────────────────────────────────
# These are the Claude tool-use JSON schemas for the functions above.
# Imported by tools_schema.py and merged into TOOL_SCHEMAS.

REMINDER_TOOL_SCHEMAS = [
    {
        "name": "create_reminder",
        "description": (
            "Create a reminder or alarm for a specific date and time. "
            "Use whenever the user says 'remind me to…', 'set a reminder for…', "
            "'set an alarm for…', 'don't let me forget…', or similar. "
            "You MUST resolve relative date phrases ('Friday', 'tomorrow at 9am', "
            "'in 20 minutes') to an absolute ISO-8601 datetime before calling this. "
            "Use the current date/time injected in the system prompt as your anchor."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "What to remind the user about (plain text, concise).",
                },
                "due_at_iso": {
                    "type": "string",
                    "description": (
                        "Absolute ISO-8601 datetime for when to fire the reminder "
                        "(e.g. '2026-09-05T09:00:00'). "
                        "Resolve ALL relative phrases before calling."
                    ),
                },
                "is_alarm": {
                    "type": "boolean",
                    "description": (
                        "True for a full wake alarm (bypasses silent mode where possible). "
                        "False (default) for a soft notification."
                    ),
                    "default": False,
                },
                "recurrence": {
                    "type": "string",
                    "enum": ["none", "daily", "weekly", "weekdays", "monthly"],
                    "description": "Repeat pattern. Default 'none'.",
                    "default": "none",
                },
                "playback_mode": {
                    "type": "string",
                    "enum": ["tobi_voice", "own_voice"],
                    "description": (
                        "How to deliver the reminder. "
                        "'tobi_voice' = TOBI speaks the text via TTS (default). "
                        "'own_voice'  = play back the user's original voice recording "
                        "(only useful when a recording is attached via the audio upload API)."
                    ),
                    "default": "tobi_voice",
                },
            },
            "required": ["content", "due_at_iso"],
        },
    },
    {
        "name": "list_reminders",
        "description": (
            "List the user's reminders. Use when the user asks 'what reminders do I have?', "
            "'show me my alarms', 'what's coming up?', or similar. "
            "Set upcoming_only=false to see all non-deleted reminders."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "upcoming_only": {
                    "type": "boolean",
                    "description": "Only show reminders due in the next `hours` hours (default true).",
                    "default": True,
                },
                "hours": {
                    "type": "integer",
                    "description": "Look-ahead window in hours when upcoming_only=true (default 48).",
                    "default": 48,
                },
            },
        },
    },
    {
        "name": "dismiss_reminder",
        "description": (
            "Dismiss a reminder so it will not fire again. "
            "For recurring reminders, advances to the next occurrence instead of deleting. "
            "Use when the user says 'dismiss reminder X', 'cancel that reminder', "
            "or 'got it' after a reminder fires."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reminder_id": {
                    "type": "integer",
                    "description": "Numeric ID of the reminder (from list_reminders).",
                },
            },
            "required": ["reminder_id"],
        },
    },
    {
        "name": "snooze_reminder",
        "description": (
            "Snooze a reminder for N more minutes. "
            "Use when the user says 'snooze', 'remind me again in 10 minutes', "
            "'give me a bit more time', etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reminder_id": {
                    "type": "integer",
                    "description": "Numeric ID of the reminder.",
                },
                "minutes": {
                    "type": "integer",
                    "description": "Minutes to snooze for (default 10).",
                    "default": 10,
                },
            },
            "required": ["reminder_id"],
        },
    },
    {
        "name": "delete_reminder",
        "description": (
            "Permanently remove a reminder. Use when the user explicitly asks to "
            "delete or remove a reminder (not just dismiss or snooze it)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reminder_id": {
                    "type": "integer",
                    "description": "Numeric ID of the reminder.",
                },
            },
            "required": ["reminder_id"],
        },
    },
    {
        "name": "update_reminder",
        "description": (
            "Change the content, time, recurrence, or alarm mode of an existing reminder. "
            "Pass only the fields you want to change — the rest stay the same. "
            "Use when the user says 'move that reminder to Thursday', "
            "'change reminder 3 to daily', etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reminder_id": {
                    "type": "integer",
                    "description": "Numeric ID of the reminder.",
                },
                "content": {
                    "type": "string",
                    "description": "New reminder text (optional).",
                },
                "due_at_iso": {
                    "type": "string",
                    "description": "New ISO-8601 due datetime (optional).",
                },
                "recurrence": {
                    "type": "string",
                    "enum": ["none", "daily", "weekly", "weekdays", "monthly"],
                    "description": "New recurrence rule (optional).",
                },
                "is_alarm": {
                    "type": "boolean",
                    "description": "Toggle alarm mode on/off (optional).",
                },
            },
            "required": ["reminder_id"],
        },
    },
]

# Registry slice — merged into TOOL_REGISTRY in tools_schema.py
REMINDER_TOOL_REGISTRY = {
    "create_reminder": create_reminder,
    "list_reminders": list_reminders,
    "dismiss_reminder": dismiss_reminder,
    "snooze_reminder": snooze_reminder,
    "delete_reminder": delete_reminder,
    "update_reminder": update_reminder,
}
