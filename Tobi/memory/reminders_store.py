"""
Tobi Reminders Store

Persistent SQLite-backed storage for reminders with:
- Natural-language content and structured due_at timestamp
- Optional voice audio recording URL (own-voice playback)
- Playback mode: 'own_voice' | 'tobi_voice'
- Alarm mode flag (fires native alarm vs. soft notification)
- Recurrence patterns (none, daily, weekly, weekdays)
- Status lifecycle: pending → snoozed → fired → dismissed | deleted

The reminders table lives in the same Tobi_memory.db file as tasks/notes
so we get a single SQLite connection pool and consistent WAL behaviour.
"""
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from Tobi.config import settings

logger = logging.getLogger("Tobi.memory.reminders")

DB_PATH = settings.DATA_DIR / "Tobi_memory.db"

# Audio clip files are stored here
AUDIO_DIR = settings.DATA_DIR / "reminder_audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class PlaybackMode(str, Enum):
    OWN_VOICE = "own_voice"   # Play the raw voice recording back to the user
    TOBI_VOICE = "tobi_voice" # Generate fresh TTS from the reminder text


class ReminderStatus(str, Enum):
    PENDING = "pending"
    SNOOZED = "snoozed"
    FIRED = "fired"
    DISMISSED = "dismissed"
    DELETED = "deleted"


class Recurrence(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    WEEKDAYS = "weekdays"   # Mon–Fri only
    MONTHLY = "monthly"


@dataclass
class Reminder:
    """A single reminder record."""
    content: str                                     # What to remind about
    due_at: float                                    # Unix timestamp
    id: int = 0
    audio_url: Optional[str] = None                  # Path to recorded audio (relative to AUDIO_DIR)
    playback_mode: PlaybackMode = PlaybackMode.TOBI_VOICE
    is_alarm: bool = False                           # Full alarm vs. soft notification
    recurrence: Recurrence = Recurrence.NONE
    status: ReminderStatus = ReminderStatus.PENDING
    snooze_until: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    last_fired_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "due_at": self.due_at,
            "due_at_iso": datetime.fromtimestamp(self.due_at).isoformat(),
            "audio_url": self.audio_url,
            "playback_mode": self.playback_mode.value,
            "is_alarm": self.is_alarm,
            "recurrence": self.recurrence.value,
            "status": self.status.value,
            "snooze_until": self.snooze_until,
            "created_at": self.created_at,
            "last_fired_at": self.last_fired_at,
        }

    def is_due(self) -> bool:
        """True if this reminder should fire right now."""
        if self.status not in (ReminderStatus.PENDING, ReminderStatus.SNOOZED):
            return False
        if self.status == ReminderStatus.SNOOZED and self.snooze_until:
            return time.time() >= self.snooze_until
        return time.time() >= self.due_at

    def next_occurrence(self) -> Optional[float]:
        """Compute the next due_at after firing, based on recurrence rule."""
        base = datetime.fromtimestamp(self.due_at)
        if self.recurrence == Recurrence.DAILY:
            return (base + timedelta(days=1)).timestamp()
        if self.recurrence == Recurrence.WEEKLY:
            return (base + timedelta(weeks=1)).timestamp()
        if self.recurrence == Recurrence.MONTHLY:
            # Advance one month (handles month-length edge cases)
            month = base.month + 1
            year = base.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            try:
                return base.replace(year=year, month=month).timestamp()
            except ValueError:
                # e.g., Jan 31 → Feb 28
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                return base.replace(year=year, month=month, day=last_day).timestamp()
        if self.recurrence == Recurrence.WEEKDAYS:
            next_dt = base + timedelta(days=1)
            # Skip Saturday (5) and Sunday (6)
            while next_dt.weekday() >= 5:
                next_dt += timedelta(days=1)
            return next_dt.timestamp()
        return None


# ─────────────────────────── Schema initialisation ───────────────────────────

def init_reminders_table() -> None:
    """Add the reminders table to the shared Tobi_memory.db."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            content       TEXT    NOT NULL,
            due_at        REAL    NOT NULL,
            audio_url     TEXT,
            playback_mode TEXT    NOT NULL DEFAULT 'tobi_voice',
            is_alarm      INTEGER NOT NULL DEFAULT 0,
            recurrence    TEXT    NOT NULL DEFAULT 'none',
            status        TEXT    NOT NULL DEFAULT 'pending',
            snooze_until  REAL,
            created_at    REAL    NOT NULL DEFAULT (unixepoch()),
            last_fired_at REAL
        )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rem_due    ON reminders(due_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rem_status ON reminders(status)")

        conn.commit()
        conn.close()
        logger.info("Reminders table ready in %s", DB_PATH)
    except Exception as e:
        logger.error("Failed to initialise reminders table: %s", e)
        raise


# ─────────────────────────────── CRUD helpers ────────────────────────────────

def _row_to_reminder(row: sqlite3.Row) -> Reminder:
    return Reminder(
        id=row["id"],
        content=row["content"],
        due_at=row["due_at"],
        audio_url=row["audio_url"],
        playback_mode=PlaybackMode(row["playback_mode"]),
        is_alarm=bool(row["is_alarm"]),
        recurrence=Recurrence(row["recurrence"]),
        status=ReminderStatus(row["status"]),
        snooze_until=row["snooze_until"],
        created_at=row["created_at"],
        last_fired_at=row["last_fired_at"],
    )


def create_reminder(
    content: str,
    due_at: float,
    audio_url: Optional[str] = None,
    playback_mode: PlaybackMode = PlaybackMode.TOBI_VOICE,
    is_alarm: bool = False,
    recurrence: Recurrence = Recurrence.NONE,
) -> Reminder:
    """Insert a new reminder and return the populated Reminder object."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO reminders
            (content, due_at, audio_url, playback_mode, is_alarm, recurrence,
             status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (
            content, due_at, audio_url,
            playback_mode.value, int(is_alarm), recurrence.value,
            time.time(),
        ))
        conn.commit()
        rid = cursor.lastrowid
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (rid,))
        reminder = _row_to_reminder(cursor.fetchone())
        logger.info("Reminder created: id=%d due=%s '%s'",
                    rid, datetime.fromtimestamp(due_at).strftime("%Y-%m-%d %H:%M"), content[:60])
        return reminder
    finally:
        conn.close()


def get_reminder(reminder_id: int) -> Optional[Reminder]:
    """Fetch a single reminder by ID."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        row = cursor.fetchone()
        conn.close()
        return _row_to_reminder(row) if row else None
    except Exception as e:
        logger.error("get_reminder(%d) failed: %s", reminder_id, e)
        return None


def get_due_reminders() -> list[Reminder]:
    """Return all reminders that are due right now (pending or snoozed)."""
    try:
        now = time.time()
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM reminders
        WHERE status IN ('pending', 'snoozed')
          AND (
                (status = 'pending'  AND due_at     <= ?)
             OR (status = 'snoozed' AND snooze_until <= ?)
          )
        ORDER BY due_at ASC
        """, (now, now))
        rows = cursor.fetchall()
        conn.close()
        return [_row_to_reminder(r) for r in rows]
    except Exception as e:
        logger.error("get_due_reminders failed: %s", e)
        return []


def get_upcoming_reminders(hours: int = 24) -> list[Reminder]:
    """Return reminders due in the next N hours (pending/snoozed only)."""
    try:
        now = time.time()
        until = now + hours * 3600
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM reminders
        WHERE status IN ('pending', 'snoozed')
          AND due_at BETWEEN ? AND ?
        ORDER BY due_at ASC
        """, (now, until))
        rows = cursor.fetchall()
        conn.close()
        return [_row_to_reminder(r) for r in rows]
    except Exception as e:
        logger.error("get_upcoming_reminders failed: %s", e)
        return []


def get_all_reminders(include_deleted: bool = False) -> list[Reminder]:
    """Return all reminders, optionally excluding deleted ones."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if include_deleted:
            cursor.execute("SELECT * FROM reminders ORDER BY due_at ASC")
        else:
            cursor.execute(
                "SELECT * FROM reminders WHERE status != 'deleted' ORDER BY due_at ASC"
            )
        rows = cursor.fetchall()
        conn.close()
        return [_row_to_reminder(r) for r in rows]
    except Exception as e:
        logger.error("get_all_reminders failed: %s", e)
        return []


def update_reminder_status(
    reminder_id: int,
    status: ReminderStatus,
    snooze_until: Optional[float] = None,
    last_fired_at: Optional[float] = None,
) -> bool:
    """Update the status (and optionally snooze/fire timestamps) of a reminder."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE reminders
        SET status = ?,
            snooze_until  = COALESCE(?, snooze_until),
            last_fired_at = COALESCE(?, last_fired_at)
        WHERE id = ?
        """, (status.value, snooze_until, last_fired_at, reminder_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error("update_reminder_status(%d) failed: %s", reminder_id, e)
        return False


def advance_recurring_reminder(reminder: Reminder) -> Optional[Reminder]:
    """
    After a recurring reminder fires, advance it to the next occurrence.
    Returns the updated Reminder, or None if there is no next occurrence.
    """
    next_due = reminder.next_occurrence()
    if next_due is None:
        return None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE reminders
        SET due_at = ?, status = 'pending', snooze_until = NULL, last_fired_at = ?
        WHERE id = ?
        """, (next_due, time.time(), reminder.id))
        conn.commit()
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder.id,))
        updated = _row_to_reminder(cursor.fetchone())
        conn.close()
        logger.info("Recurring reminder %d advanced to %s",
                    reminder.id, datetime.fromtimestamp(next_due).strftime("%Y-%m-%d %H:%M"))
        return updated
    except Exception as e:
        logger.error("advance_recurring_reminder(%d) failed: %s", reminder.id, e)
        return None


def update_reminder_audio(reminder_id: int, audio_url: str, playback_mode: PlaybackMode) -> bool:
    """Attach a voice recording to a reminder (called after audio upload)."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE reminders SET audio_url = ?, playback_mode = ? WHERE id = ?
        """, (audio_url, playback_mode.value, reminder_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error("update_reminder_audio(%d) failed: %s", reminder_id, e)
        return False


def delete_reminder(reminder_id: int) -> bool:
    """Soft-delete a reminder (sets status=deleted, keeps the row for auditing)."""
    return update_reminder_status(reminder_id, ReminderStatus.DELETED)


def get_reminder_audio_path(filename: str) -> Path:
    """Return the absolute filesystem path for a stored audio file."""
    return AUDIO_DIR / filename


# ─────────────────────────── Initialise on import ────────────────────────────

try:
    init_reminders_table()
except Exception as _e:
    logger.warning("Reminders table init deferred: %s", _e)
