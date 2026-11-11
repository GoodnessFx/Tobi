"""
Content pipeline tracker for Tobi.

Tracks content across Vibe District (streetwear) and the KDP/B&N
self-publishing catalog. Shows what's in progress, published, and next.
"""
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger("Tobi.tools.content_pipeline")

DB_PATH = str(Path(__file__).parent.parent.parent / "data" / "Tobi_content.db")


def _init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venture TEXT NOT NULL,
            title TEXT NOT NULL,
            content_type TEXT DEFAULT 'product',
            status TEXT DEFAULT 'idea',
            platform TEXT,
            price REAL DEFAULT 0,
            cost REAL DEFAULT 0,
            revenue REAL DEFAULT 0,
            publish_date TEXT,
            notes TEXT,
            created_at REAL DEFAULT (strftime('%s','now')),
            updated_at REAL DEFAULT (strftime('%s','now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS revenue_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            source TEXT,
            logged_at REAL DEFAULT (strftime('%s','now')),
            FOREIGN KEY (content_id) REFERENCES content_items(id)
        )
    """)
    conn.commit()
    conn.close()


_init_db()


@dataclass
class ContentItem:
    id: int
    venture: str
    title: str
    content_type: str = "product"
    status: str = "idea"
    platform: str = ""
    price: float = 0
    cost: float = 0
    revenue: float = 0
    publish_date: str = ""
    notes: str = ""
    created_at: float = 0
    updated_at: float = 0

    def to_dict(self):
        return asdict(self)


def add_content(venture: str, title: str, content_type: str = "product",
                status: str = "idea", platform: str = "", price: float = 0,
                cost: float = 0, notes: str = "") -> ContentItem:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO content_items (venture, title, content_type, status, platform, price, cost, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (venture, title, content_type, status, platform, price, cost, notes),
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return ContentItem(id=item_id, venture=venture, title=title, content_type=content_type,
                       status=status, platform=platform, price=price, cost=cost, notes=notes)


def get_content_by_venture(venture: str) -> list[ContentItem]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM content_items WHERE venture = ? ORDER BY updated_at DESC", (venture,)).fetchall()
    conn.close()
    return [ContentItem(*r) for r in rows]


def get_content_by_status(status: str) -> list[ContentItem]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM content_items WHERE status = ? ORDER BY updated_at DESC", (status,)).fetchall()
    conn.close()
    return [ContentItem(*r) for r in rows]


def update_content_status(content_id: int, status: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE content_items SET status = ?, updated_at = ? WHERE id = ?",
                 (status, time.time(), content_id))
    conn.commit()
    changed = conn.total_changes > 0
    conn.close()
    return changed


def log_revenue(content_id: int, amount: float, currency: str = "USD", source: str = ""):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO revenue_log (content_id, amount, currency, source) VALUES (?, ?, ?, ?)",
        (content_id, amount, currency, source),
    )
    conn.execute("UPDATE content_items SET revenue = revenue + ? WHERE id = ?", (amount, content_id))
    conn.commit()
    conn.close()


def get_pipeline_summary() -> dict:
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM content_items").fetchone()[0]
    by_status = {}
    for status in ("idea", "in_progress", "published", "archived"):
        count = conn.execute("SELECT COUNT(*) FROM content_items WHERE status = ?", (status,)).fetchone()[0]
        by_status[status] = count
    by_venture = {}
    for row in conn.execute("SELECT venture, COUNT(*), SUM(revenue) FROM content_items GROUP BY venture"):
        by_venture[row[0]] = {"count": row[1], "revenue": row[2] or 0}
    total_revenue = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM revenue_log").fetchone()[0]
    conn.close()

    return {
        "total_items": total,
        "by_status": by_status,
        "by_venture": by_venture,
        "total_revenue": total_revenue,
    }


async def get_content_brief() -> str:
    """Build a content pipeline brief."""
    summary = get_pipeline_summary()
    parts = [f"Content pipeline: {summary['total_items']} items total"]

    for venture, data in summary.get("by_venture", {}).items():
        parts.append(f"  {venture}: {data['count']} items, ${data['revenue']:,.2f} revenue")

    for status, count in summary.get("by_status", {}).items():
        if count > 0:
            parts.append(f"  {status}: {count}")

    parts.append(f"Total revenue tracked: ${summary['total_revenue']:,.2f}")
    return "\n".join(parts)
