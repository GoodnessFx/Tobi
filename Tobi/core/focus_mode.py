"""
Focus mode for Tobi.

One toggle that mutes the intel engine and notifications for a set block,
so the always-on part doesn't become always distracting.
"""
import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger("Tobi.core.focus_mode")

# Global focus state
_focus_active = False
_focus_end_time: float = 0
_focus_task: Optional[asyncio.Task] = None
_focus_callback = None


def is_focus_active() -> bool:
    """Check if focus mode is currently active."""
    global _focus_active, _focus_end_time
    if _focus_active and time.time() > _focus_end_time:
        _focus_active = False
        logger.info("Focus mode expired.")
    return _focus_active


def start_focus(minutes: int = 25) -> dict:
    """Start focus mode for N minutes."""
    global _focus_active, _focus_end_time
    _focus_active = True
    _focus_end_time = time.time() + minutes * 60
    logger.info("Focus mode started for %d minutes.", minutes)
    return {
        "active": True,
        "end_time": _focus_end_time,
        "minutes": minutes,
        "message": f"Focus mode ON for {minutes} minutes. Notifications paused.",
    }


def stop_focus() -> dict:
    """Stop focus mode early."""
    global _focus_active
    _focus_active = False
    logger.info("Focus mode stopped manually.")
    return {"active": False, "message": "Focus mode OFF. Notifications resumed."}


def get_focus_status() -> dict:
    """Get current focus mode status."""
    active = is_focus_active()
    remaining = 0
    if active:
        remaining = max(0, int((_focus_end_time - time.time()) / 60))
    return {
        "active": active,
        "remaining_minutes": remaining,
        "end_time": _focus_end_time,
    }
