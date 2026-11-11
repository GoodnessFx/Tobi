"""
CRM lite module for Tobi.

Tracks clients, leads, deals, and follow-ups for Growth Network
and freelance web dev practice. Lightweight SQLite-backed.
"""
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger("Tobi.tools.crm")

DB_PATH = str(Path(__file__).parent.parent.parent / "data" / "Tobi_crm.db")


def _init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            company TEXT,
            role TEXT,
            source TEXT,
            stage TEXT DEFAULT 'lead',
            notes TEXT,
            last_contacted REAL,
            created_at REAL DEFAULT (strftime('%s','now')),
            tags TEXT DEFAULT '[]'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            title TEXT NOT NULL,
            value REAL DEFAULT 0,
            currency TEXT DEFAULT 'NGN',
            stage TEXT DEFAULT 'prospect',
            expected_close TEXT,
            notes TEXT,
            created_at REAL DEFAULT (strftime('%s','now')),
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            deal_id INTEGER,
            type TEXT NOT NULL,
            description TEXT,
            timestamp REAL DEFAULT (strftime('%s','now')),
            FOREIGN KEY (contact_id) REFERENCES contacts(id),
            FOREIGN KEY (deal_id) REFERENCES deals(id)
        )
    """)
    conn.commit()
    conn.close()


_init_db()


@dataclass
class Contact:
    id: int
    name: str
    email: str = ""
    phone: str = ""
    company: str = ""
    role: str = ""
    source: str = ""
    stage: str = "lead"
    notes: str = ""
    last_contacted: float = 0
    created_at: float = 0
    tags: str = "[]"

    def to_dict(self):
        return asdict(self)


@dataclass
class Deal:
    id: int
    contact_id: int
    title: str
    value: float = 0
    currency: str = "NGN"
    stage: str = "prospect"
    expected_close: str = ""
    notes: str = ""
    created_at: float = 0

    def to_dict(self):
        return asdict(self)


def add_contact(name: str, email: str = "", phone: str = "", company: str = "",
                role: str = "", source: str = "", notes: str = "") -> Contact:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO contacts (name, email, phone, company, role, source, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, email, phone, company, role, source, notes),
    )
    conn.commit()
    contact_id = cursor.lastrowid
    conn.close()
    return Contact(id=contact_id, name=name, email=email, phone=phone, company=company,
                   role=role, source=source, notes=notes)


def get_contact(contact_id: int) -> Optional[Contact]:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
    conn.close()
    if row:
        return Contact(*row)
    return None


def search_contacts(query: str, limit: int = 20) -> list[Contact]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT * FROM contacts WHERE name LIKE ? OR company LIKE ? OR notes LIKE ? LIMIT ?",
        (f"%{query}%", f"%{query}%", f"%{query}%", limit),
    ).fetchall()
    conn.close()
    return [Contact(*r) for r in rows]


def get_all_contacts(limit: int = 50) -> list[Contact]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM contacts ORDER BY last_contacted DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [Contact(*r) for r in rows]


def update_contact_stage(contact_id: int, stage: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE contacts SET stage = ? WHERE id = ?", (stage, contact_id))
    conn.commit()
    changed = conn.total_changes > 0
    conn.close()
    return changed


def log_activity(contact_id: int, activity_type: str, description: str, deal_id: int = 0):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO activities (contact_id, deal_id, type, description) VALUES (?, ?, ?, ?)",
        (contact_id, deal_id, activity_type, description),
    )
    conn.execute("UPDATE contacts SET last_contacted = ? WHERE id = ?", (time.time(), contact_id))
    conn.commit()
    conn.close()


def get_contact_activities(contact_id: int, limit: int = 10) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT * FROM activities WHERE contact_id = ? ORDER BY timestamp DESC LIMIT ?",
        (contact_id, limit),
    ).fetchall()
    conn.close()
    return [{"id": r[0], "contact_id": r[1], "deal_id": r[2], "type": r[3], "description": r[4], "timestamp": r[5]} for r in rows]


def add_deal(contact_id: int, title: str, value: float = 0, currency: str = "NGN",
             expected_close: str = "", notes: str = "") -> Deal:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO deals (contact_id, title, value, currency, expected_close, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (contact_id, title, value, currency, expected_close, notes),
    )
    conn.commit()
    deal_id = cursor.lastrowid
    conn.close()
    return Deal(id=deal_id, contact_id=contact_id, title=title, value=value,
                currency=currency, expected_close=expected_close, notes=notes)


def get_open_deals() -> list[Deal]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM deals WHERE stage NOT IN ('won', 'lost') ORDER BY value DESC").fetchall()
    conn.close()
    return [Deal(*r) for r in rows]


def get_crm_summary() -> dict:
    conn = sqlite3.connect(DB_PATH)
    total_contacts = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
    leads = conn.execute("SELECT COUNT(*) FROM contacts WHERE stage = 'lead'").fetchone()[0]
    clients = conn.execute("SELECT COUNT(*) FROM contacts WHERE stage = 'client'").fetchone()[0]
    active_deals = conn.execute("SELECT COUNT(*) FROM deals WHERE stage NOT IN ('won', 'lost')").fetchone()[0]
    total_deal_value = conn.execute("SELECT COALESCE(SUM(value), 0) FROM deals WHERE stage NOT IN ('won', 'lost')").fetchone()[0]
    recent_activities = conn.execute("SELECT COUNT(*) FROM activities WHERE timestamp > ?", (time.time() - 7 * 86400,)).fetchone()[0]
    conn.close()

    return {
        "total_contacts": total_contacts,
        "leads": leads,
        "clients": clients,
        "active_deals": active_deals,
        "total_deal_value": total_deal_value,
        "recent_activities_7d": recent_activities,
    }


def get_stale_contacts(days: int = 14) -> list[Contact]:
    """Get contacts not contacted in the last N days."""
    cutoff = time.time() - days * 86400
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT * FROM contacts WHERE last_contacted < ? AND last_contacted > 0 ORDER BY last_contacted LIMIT 20",
        (cutoff,),
    ).fetchall()
    conn.close()
    return [Contact(*r) for r in rows]


async def get_crm_brief() -> str:
    """Build a CRM summary brief."""
    summary = get_crm_summary()
    stale = get_stale_contacts(14)

    parts = [
        f"CRM Summary: {summary['total_contacts']} contacts ({summary['leads']} leads, {summary['clients']} clients)",
        f"Active deals: {summary['active_deals']} (total value: {summary['total_deal_value']:,.0f} {summary.get('currency', 'NGN')})",
        f"Activities this week: {summary['recent_activities_7d']}",
    ]

    if stale:
        stale_names = [f"{c.name} ({c.company})" for c in stale[:5]]
        parts.append(f"Stale contacts (>14 days): {', '.join(stale_names)}")

    return "\n".join(parts)
