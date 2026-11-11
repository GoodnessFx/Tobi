"""
Always-on intel engine for Tobi.

Scheduled background jobs that pull news, blockchain/crypto/forex updates,
and niche trends on a set interval, store them, and surface only what's
actually relevant. Respects focus mode (no active fetching during focus blocks).
"""
import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("Tobi.core.intel_engine")

STATE_DIR = Path(__file__).parent.parent.parent / "data" / "intel"
STATE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_INTERVALS = {
    "crypto": 3600,        # every hour
    "forex": 7200,         # every 2 hours
    "news": 1800,          # every 30 min
    "trending": 3600,      # every hour
    "jobs": 21600,         # 3x a day
}

# Results are stored here between checks so the brief can read them
_results = {}


def _save_state():
    """Persist intel results to disk so they survive restarts."""
    try:
        path = STATE_DIR / "intel_state.json"
        path.write_text(json.dumps(_results, indent=2, default=str))
    except Exception as e:
        logger.debug("Intel state save failed: %s", e)


def _load_state():
    """Load previously stored intel results."""
    global _results
    try:
        path = STATE_DIR / "intel_state.json"
        if path.exists():
            _results = json.loads(path.read_text())
    except Exception as e:
        logger.debug("Intel state load failed: %s", e)


def get_latest(category: str) -> dict:
    """Get the latest stored intel for a category."""
    entry = _results.get(category, {})
    return {
        "category": category,
        "data": entry.get("data", ""),
        "collected_at": entry.get("collected_at", 0),
        "age_seconds": time.time() - entry.get("collected_at", 0) if entry.get("collected_at") else None,
    }


def get_all_latest() -> dict:
    """Get all stored intel results."""
    return {
        category: get_latest(category)
        for category in DEFAULT_INTERVALS
    }


async def _collect(category: str) -> Optional[str]:
    """Collect intel for a given category. Returns the data string or None."""
    try:
        if category == "crypto":
            from Tobi.tools.market_intel import get_crypto_prices
            return await get_crypto_prices()
        elif category == "forex":
            from Tobi.tools.market_intel import get_forex_rates
            return await get_forex_rates()
        elif category == "news":
            from Tobi.tools.market_intel import get_ai_tech_news
            return await get_ai_tech_news(10)
        elif category == "trending":
            from Tobi.tools.social_media import get_social_brief
            return await get_social_brief()
        elif category == "jobs":
            from Tobi.tools.job_search import get_daily_job_brief
            return await get_daily_job_brief()
    except Exception as e:
        logger.warning("Intel collection failed for %s: %s", category, e)
        return None
    return None


class IntelEngine:
    """Background intel collection loop."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._intervals = dict(DEFAULT_INTERVALS)
        self._last_run: dict[str, float] = {}

    def start(self):
        """Start the intel engine background loop."""
        if self._running:
            return
        self._running = True
        _load_state()
        self._task = asyncio.create_task(self._loop())
        logger.info("Intel engine started. Categories: %s", ", ".join(self._intervals.keys()))

    def stop(self):
        """Stop the intel engine."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        _save_state()
        logger.info("Intel engine stopped.")

    def set_interval(self, category: str, seconds: int):
        """Change the collection interval for a category."""
        if category in self._intervals:
            self._intervals[category] = seconds
            logger.info("Intel category %s interval set to %ds.", category, seconds)

    def get_status(self) -> dict:
        """Get intel engine status."""
        return {
            "running": self._running,
            "categories": {
                cat: {
                    "interval_s": self._intervals[cat],
                    "last_run": self._last_run.get(cat, 0),
                    "age_seconds": time.time() - self._last_run.get(cat, 0)
                    if self._last_run.get(cat) else None,
                    "stored": bool(_results.get(cat, {}).get("data")),
                }
                for cat in self._intervals
            },
        }

    async def _loop(self):
        """Main background loop."""
        await asyncio.sleep(60)  # initial delay

        while self._running:
            try:
                # Check if focus mode is active
                try:
                    from Tobi.core.focus_mode import is_focus_active
                    if is_focus_active():
                        await asyncio.sleep(300)  # slow poll during focus
                        continue
                except ImportError:
                    pass

                now = time.time()
                for category, interval in self._intervals.items():
                    last = self._last_run.get(category, 0)
                    if now - last >= interval:
                        self._last_run[category] = now
                        logger.info("Intel: collecting %s...", category)
                        data = await _collect(category)
                        if data:
                            _results[category] = {
                                "data": data,
                                "collected_at": time.time(),
                            }
                        await asyncio.sleep(1)  # rate limit between categories
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Intel engine loop error: %s", e)

            await asyncio.sleep(60)


# Singleton
intel_engine = IntelEngine()