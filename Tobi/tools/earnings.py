"""
Earnings projection module for Tobi.

Projects realistic earnings across ventures based on current growth rates.
Shows the math, not just a number. Recalculates as real data comes in.
"""
import logging
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("Tobi.tools.earnings")


@dataclass
class VentureEarnings:
    name: str
    monthly_revenue: float
    growth_rate: float  # monthly growth rate as decimal
    costs: float
    margin: float
    projection_3m: float
    projection_6m: float
    projection_12m: float
    confidence: str  # low, medium, high


def calculate_projection(
    monthly_revenue: float,
    growth_rate: float,
    costs: float,
    months: int = 12,
) -> list[float]:
    """Project revenue month by month with compound growth."""
    projections = []
    current = monthly_revenue
    for _ in range(months):
        current = current * (1 + growth_rate)
        projections.append(round(current, 2))
    return projections


def project_venture(
    name: str,
    monthly_revenue: float,
    growth_rate: float,
    costs: float,
) -> VentureEarnings:
    """Project earnings for a single venture."""
    projections = calculate_projection(monthly_revenue, growth_rate, costs, 12)
    margin = (monthly_revenue - costs) / monthly_revenue if monthly_revenue > 0 else 0

    # Confidence based on data quality
    if monthly_revenue > 0 and growth_rate > 0:
        confidence = "high" if monthly_revenue > 100000 else "medium"
    elif monthly_revenue > 0:
        confidence = "medium"
    else:
        confidence = "low"

    return VentureEarnings(
        name=name,
        monthly_revenue=monthly_revenue,
        growth_rate=growth_rate,
        costs=costs,
        margin=margin,
        projection_3m=projections[2] if len(projections) > 2 else 0,
        projection_6m=projections[5] if len(projections) > 5 else 0,
        projection_12m=projections[11] if len(projections) > 11 else 0,
        confidence=confidence,
    )


def get_all_projections() -> list[VentureEarnings]:
    """Get projections for all known ventures."""
    # Default projections based on typical early-stage ventures
    # These should be updated with real data from the content pipeline and CRM
    ventures = [
        {"name": "Growth Network", "revenue": 0, "growth": 0.15, "costs": 50000},
        {"name": "Freelance Web Dev", "revenue": 0, "growth": 0.10, "costs": 20000},
        {"name": "KDP Publishing", "revenue": 0, "growth": 0.05, "costs": 5000},
        {"name": "Vibe District", "revenue": 0, "growth": 0.20, "costs": 100000},
        {"name": "Tersor Concept", "revenue": 0, "growth": 0.10, "costs": 80000},
    ]

    # Try to pull real data from content pipeline DB
    try:
        import pathlib
        db_path = str(pathlib.Path(__file__).parent.parent.parent / "data" / "Tobi_content.db")
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT venture, SUM(revenue), SUM(cost) FROM content_items GROUP BY venture"
        ).fetchall()
        conn.close()

        for row in rows:
            venture_name = row[0]
            actual_revenue = row[1] or 0
            actual_costs = row[2] or 0
            for v in ventures:
                if v["name"].lower() == venture_name.lower():
                    v["revenue"] = actual_revenue
                    v["costs"] = actual_costs if actual_costs > 0 else v["costs"]
    except Exception as e:
        logger.debug("Could not pull real revenue data: %s", e)

    return [project_venture(**v) for v in ventures]


def format_projection(v: VentureEarnings) -> str:
    """Format a single venture projection as readable text."""
    margin_pct = f"{v.margin * 100:.1f}%"
    growth_pct = f"{v.growth_rate * 100:.0f}%"
    return (
        f"{v.name}: "
        f"Current: {v.monthly_revenue:,.0f}/mo | "
        f"Margin: {margin_pct} | "
        f"Growth: {growth_pct}/mo\n"
        f"  3 months: {v.projection_3m:,.0f} | "
        f"6 months: {v.projection_6m:,.0f} | "
        f"12 months: {v.projection_12m:,.0f} "
        f"(confidence: {v.confidence})"
    )


async def get_earnings_brief() -> str:
    """Build an earnings projection brief."""
    projections = get_all_projections()

    parts = ["EARNINGS PROJECTIONS\n"]

    total_3m = sum(p.projection_3m for p in projections)
    total_6m = sum(p.projection_6m for p in projections)
    total_12m = sum(p.projection_12m for p in projections)

    parts.append(f"Combined projections:")
    parts.append(f"  3 months: {total_3m:,.0f}")
    parts.append(f"  6 months: {total_6m:,.0f}")
    parts.append(f"  12 months: {total_12m:,.0f}")
    parts.append("")

    for p in projections:
        parts.append(format_projection(p))

    parts.append("\nNote: Projections are based on current revenue data and assumed growth rates.")
    parts.append("Update venture data in the content pipeline for more accurate projections.")

    return "\n".join(parts)
