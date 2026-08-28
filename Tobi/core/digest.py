"""
Tobi Daily Digest & Wake Briefing Generator  (Phase 0)

Two entry points:

  build_digest(brain)        — full structured digest for the dashboard/API,
                               returned as a dict with sections the UI renders.

  build_wake_briefing(brain) — ultra-short spoken briefing (< 120 words) read
                               aloud by TTS immediately after the morning alarm
                               is dismissed.  Covers date, top 3 priorities,
                               and any reminders due before noon.

Both are async, return quickly (no LLM call for the wake brief), and are
deliberately self-contained so they work even when the brain is half-asleep
at startup.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Tobi.core.brain import TobiBrain

logger = logging.getLogger("Tobi.core.digest")


# ─────────────────────────────────── helpers ─────────────────────────────────

def _ordinal(n: int) -> str:
    """Return '1st', '2nd', '3rd', '4th', …"""
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}{['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]}"


def _friendly_due(ts: float) -> str:
    """Human-friendly relative time label for a reminder timestamp."""
    now = datetime.now()
    due = datetime.fromtimestamp(ts)
    delta_mins = int((ts - time.time()) / 60)

    if delta_mins < 0:
        return "overdue"
    if delta_mins == 0:
        return "right now"
    if delta_mins < 60:
        return f"in {delta_mins} min"

    if due.date() == now.date():
        return f"today at {due.strftime('%I:%M %p').lstrip('0')}"
    if due.date() == (now + timedelta(days=1)).date():
        return f"tomorrow at {due.strftime('%I:%M %p').lstrip('0')}"

    return due.strftime("%a %b %-d at %I:%M %p")


def _get_top_facts(brain: "TobiBrain", limit: int = 10) -> list[dict]:
    """Return the highest-confidence user facts as plain dicts."""
    try:
        facts = brain.memory.facts.get_all(min_confidence=0.4)
        # Sort by effective_confidence descending, then recency
        facts.sort(key=lambda f: (f.effective_confidence, f.last_reinforced), reverse=True)
        return [
            {
                "category": f.category,
                "subject": f.subject,
                "value": f.value,
                "confidence": round(f.effective_confidence, 2),
            }
            for f in facts[:limit]
        ]
    except Exception as e:
        logger.debug("Facts fetch failed: %s", e)
        return []


def _get_high_priority_sqlite_tasks(limit: int = 5) -> list[dict]:
    """Pull high-priority open tasks from the SQLite task table."""
    try:
        from Tobi.memory.sqlite_store import get_open_tasks
        tasks = get_open_tasks()
        high = [t for t in tasks if t.get("priority", 0) >= 4]
        return high[:limit] if high else tasks[:limit]
    except Exception as e:
        logger.debug("Task fetch failed: %s", e)
        return []


def _get_upcoming_reminders_section(hours: int = 24) -> list[dict]:
    """Reminders due in the next N hours, as plain dicts."""
    try:
        from Tobi.memory.reminders_store import get_upcoming_reminders
        reminders = get_upcoming_reminders(hours=hours)
        return [
            {
                "id": r.id,
                "content": r.content,
                "due_at": r.due_at,
                "due_label": _friendly_due(r.due_at),
                "is_alarm": r.is_alarm,
                "recurrence": r.recurrence.value,
            }
            for r in reminders
        ]
    except Exception as e:
        logger.debug("Reminders fetch failed: %s", e)
        return []


def _get_stale_goals(brain: "TobiBrain", stale_days: int = 7) -> list[dict]:
    """
    Goals or skill-gaps that haven't been touched in `stale_days` days.
    Used to generate drift nudges in the digest.
    """
    try:
        cutoff = time.time() - stale_days * 86400
        facts = brain.memory.facts.get_by_category("goal") + \
                brain.memory.facts.get_by_category("skill_gap")
        stale = [
            {
                "subject": f.subject,
                "value": f.value,
                "days_since": int((time.time() - f.last_reinforced) / 86400),
            }
            for f in facts
            if f.last_reinforced < cutoff and f.effective_confidence >= 0.3
        ]
        stale.sort(key=lambda x: x["days_since"], reverse=True)
        return stale[:5]
    except Exception as e:
        logger.debug("Stale goals fetch failed: %s", e)
        return []


# ──────────────────────────────── full digest ────────────────────────────────

async def build_digest(brain: "TobiBrain") -> dict:
    """
    Build the full daily digest.

    Returns a structured dict the dashboard can render directly.
    Sections:
      - date_label   : "Friday, August 28"
      - greeting     : time-appropriate greeting string
      - priorities   : top 3 high-priority tasks / goals
      - reminders    : upcoming reminders (next 24 h)
      - drift_nudges : goals/skills untouched > 7 days
      - facts_summary: top known facts (for debug/display)
      - generated_at : unix timestamp
    """
    now = datetime.now()
    hour = now.hour

    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    elif 17 <= hour < 21:
        greeting = "Good evening"
    else:
        greeting = "Still up?"

    date_label = f"{now.strftime('%A')}, {now.strftime('%B')} {_ordinal(now.day)}"

    # --- priorities: merge sqlite tasks + high-confidence goals ---
    tasks = _get_high_priority_sqlite_tasks(limit=5)
    goals = []
    try:
        goal_facts = brain.memory.facts.get_by_category("goal")
        goal_facts.sort(key=lambda f: f.effective_confidence, reverse=True)
        goals = [
            {"type": "goal", "content": f.value, "subject": f.subject}
            for f in goal_facts[:3]
        ]
    except Exception:
        pass

    priorities = []
    for t in tasks[:3]:
        priorities.append({
            "type": "task",
            "content": t.get("title", ""),
            "project": t.get("project", ""),
            "due": t.get("due_date", ""),
            "priority": t.get("priority", 3),
        })
    # Fill remaining slots from goals if tasks < 3
    for g in goals:
        if len(priorities) >= 3:
            break
        priorities.append(g)

    reminders = _get_upcoming_reminders_section(hours=24)
    drift_nudges = _get_stale_goals(brain, stale_days=7)
    facts_summary = _get_top_facts(brain, limit=8)

    # --- LLM-generated insight line (fast tier, optional) ---
    insight = ""
    try:
        if priorities or drift_nudges:
            ctx_parts = []
            if priorities:
                ctx_parts.append("Top priorities: " + "; ".join(p["content"] for p in priorities))
            if drift_nudges:
                ctx_parts.append(
                    "Stale goals (days since touched): "
                    + "; ".join(f"{d['value']} ({d['days_since']}d)" for d in drift_nudges[:3])
                )
            prompt = (
                "In ONE sentence (max 25 words), give a sharp, honest coaching insight "
                "for today based on this context. Be direct, not motivational-poster-y.\n\n"
                + "\n".join(ctx_parts)
            )
            insight = await brain.llm.complete(prompt, tier="fast")
            insight = insight.strip().rstrip(".")
    except Exception as e:
        logger.debug("Digest insight generation failed (non-critical): %s", e)

    return {
        "date_label": date_label,
        "greeting": greeting,
        "priorities": priorities,
        "reminders": reminders,
        "drift_nudges": drift_nudges,
        "facts_summary": facts_summary,
        "insight": insight,
        "generated_at": time.time(),
        "stats": {
            "total_reminders": len(reminders),
            "stale_goals": len(drift_nudges),
            "open_tasks": len(tasks),
        },
    }


# ────────────────────────── wake briefing (short TTS) ────────────────────────

async def build_wake_briefing(brain: "TobiBrain") -> dict:
    """
    Build the ultra-short morning wake briefing.

    Target: < 120 words, spoken aloud by TTS after the alarm dismisses.
    No LLM call — pure data assembly so it fires instantly.

    Returns:
        {
          "text":        str  — full briefing text for TTS
          "date_label":  str
          "priorities":  list[str]
          "reminders":   list[dict]   — only those due before noon today
          "word_count":  int
        }
    """
    now = datetime.now()
    today_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)

    date_label = f"{now.strftime('%A')}, {now.strftime('%B')} {_ordinal(now.day)}"

    # Top 3 priorities (titles only, no LLM)
    tasks = _get_high_priority_sqlite_tasks(limit=3)
    priority_labels = [t.get("title", "") for t in tasks if t.get("title")]

    # Also pull high-confidence goals if fewer than 3 tasks
    if len(priority_labels) < 3:
        try:
            goal_facts = brain.memory.facts.get_by_category("goal")
            goal_facts.sort(key=lambda f: f.effective_confidence, reverse=True)
            for f in goal_facts:
                if len(priority_labels) >= 3:
                    break
                priority_labels.append(f.value)
        except Exception:
            pass

    # Reminders due before noon today only
    morning_reminders = []
    try:
        from Tobi.memory.reminders_store import get_upcoming_reminders
        upcoming = get_upcoming_reminders(hours=24)
        morning_reminders = [
            r for r in upcoming
            if datetime.fromtimestamp(r.due_at) <= today_noon
        ]
    except Exception as e:
        logger.debug("Morning reminders fetch failed: %s", e)

    # ── Assemble spoken text ──────────────────────────────────────────────────
    parts: list[str] = [f"Good morning. Today is {date_label}."]

    if priority_labels:
        if len(priority_labels) == 1:
            parts.append(f"Your top priority is: {priority_labels[0]}.")
        else:
            listed = ", ".join(priority_labels[:-1]) + f", and {priority_labels[-1]}"
            parts.append(f"Your top {len(priority_labels)} priorities are: {listed}.")
    else:
        parts.append("No high-priority tasks flagged yet.")

    if morning_reminders:
        if len(morning_reminders) == 1:
            r = morning_reminders[0]
            parts.append(
                f"One reminder before noon: {r.content}, "
                f"{_friendly_due(r.due_at)}."
            )
        else:
            parts.append(
                f"You have {len(morning_reminders)} reminders before noon. "
                f"First up: {morning_reminders[0].content}, "
                f"{_friendly_due(morning_reminders[0].due_at)}."
            )
    else:
        parts.append("No reminders before noon.")

    parts.append("What do you want to tackle first?")

    text = " ".join(parts)
    word_count = len(text.split())

    return {
        "text": text,
        "date_label": date_label,
        "priorities": priority_labels,
        "reminders": [
            {
                "id": r.id,
                "content": r.content,
                "due_label": _friendly_due(r.due_at),
                "is_alarm": r.is_alarm,
            }
            for r in morning_reminders
        ],
        "word_count": word_count,
        "generated_at": time.time(),
    }
