"""
Weekly retro for Tobi.

Once a week, a short summary of what got done across ventures, what didn't
move, and what to drop. More useful than a daily brief for seeing progress.
"""
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger("Tobi.core.weekly_retro")


async def build_weekly_retro(brain) -> dict:
    """Build a weekly retrospective summary."""
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    week_start_str = week_start.strftime("%B %d")

    parts = []
    parts.append(f"Weekly Retro: Week of {week_start_str}")

    # 1. Conversations and tasks completed
    try:
        from Tobi.memory.sqlite_store import get_recent_memories
        memories = get_recent_memories(limit=50)
        completed = [m for m in memories if any(w in m.get("content", "").lower() for w in ["completed", "done", "finished", "deployed", "shipped"])]
        parts.append(f"\nCompleted this week: {len(completed)} items")
        for m in completed[:5]:
            content = m.get("content", "")[:100]
            parts.append(f"  - {content}")
    except Exception as e:
        logger.debug("Memory fetch failed: %s", e)

    # 2. Content pipeline status
    try:
        from Tobi.tools.content_pipeline import get_pipeline_summary
        summary = get_pipeline_summary()
        parts.append(f"\nContent pipeline: {summary['total_items']} items")
        for status, count in summary.get("by_status", {}).items():
            if count > 0:
                parts.append(f"  {status}: {count}")
    except Exception as e:
        logger.debug("Content pipeline fetch failed: %s", e)

    # 3. CRM activity
    try:
        from Tobi.tools.crm import get_crm_summary
        crm = get_crm_summary()
        parts.append(f"\nCRM: {crm['total_contacts']} contacts, {crm['active_deals']} active deals")
        parts.append(f"  Activities this week: {crm['recent_activities_7d']}")
    except Exception as e:
        logger.debug("CRM fetch failed: %s", e)

    # 4. GitHub activity
    try:
        from Tobi.tools.github_tools import get_my_repos
        repos = await get_my_repos(3)
        parts.append(f"\nGitHub activity: {repos[:200]}")
    except Exception as e:
        logger.debug("GitHub fetch failed: %s", e)

    # 5. Cost summary
    try:
        from Tobi.core.cost_tracker import get_month_summary
        costs = get_month_summary()
        parts.append(f"\nCosts this month: ${costs.get('total_cost', 0):.2f}")
    except Exception as e:
        logger.debug("Cost fetch failed: %s", e)

    # 6. Earnings projection
    try:
        from Tobi.tools.earnings import get_earnings_brief
        earnings = await get_earnings_brief()
        parts.append(f"\nEarnings outlook:\n{earnings[:300]}")
    except Exception as e:
        logger.debug("Earnings fetch failed: %s", e)

    return {
        "title": f"Weekly Retro: Week of {week_start_str}",
        "content": "\n".join(parts),
        "generated_at": time.time(),
        "week_start": week_start.isoformat(),
    }
