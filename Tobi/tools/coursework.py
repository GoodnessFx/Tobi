"""
Coursework tracker for Tobi.

Syncs with Oduduwa University schedule. Tracks assignments, deadlines,
exams, and academic progress.
"""
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger("Tobi.tools.coursework")

DB_PATH = str(Path(__file__).parent.parent.parent / "data" / "Tobi_academic.db")


def _init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            lecturer TEXT,
            semester TEXT,
            credits INTEGER DEFAULT 3,
            created_at REAL DEFAULT (strftime('%s','now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY,
            course_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            due_timestamp REAL,
            status TEXT DEFAULT 'pending',
            grade TEXT,
            priority INTEGER DEFAULT 3,
            notes TEXT,
            created_at REAL DEFAULT (strftime('%s','now')),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            title TEXT NOT NULL,
            exam_date TEXT,
            exam_timestamp REAL,
            location TEXT,
            notes TEXT,
            created_at REAL DEFAULT (strftime('%s','now')),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)
    conn.commit()
    conn.close()


_init_db()


@dataclass
class Course:
    id: int
    code: str
    name: str
    lecturer: str = ""
    semester: str = ""
    credits: int = 3

    def to_dict(self):
        return asdict(self)


@dataclass
class Assignment:
    id: int
    course_id: int
    title: str
    description: str = ""
    due_date: str = ""
    due_timestamp: float = 0
    status: str = "pending"
    grade: str = ""
    priority: int = 3
    notes: str = ""

    def to_dict(self):
        return asdict(self)


def add_course(code: str, name: str, lecturer: str = "", semester: str = "", credits: int = 3) -> Course:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO courses (code, name, lecturer, semester, credits) VALUES (?, ?, ?, ?, ?)",
        (code, name, lecturer, semester, credits),
    )
    conn.commit()
    course_id = cursor.lastrowid
    conn.close()
    return Course(id=course_id, code=code, name=name, lecturer=lecturer, semester=semester, credits=credits)


def add_assignment(course_id: int, title: str, due_date: str = "", description: str = "",
                   priority: int = 3, notes: str = "") -> Assignment:
    due_ts = 0
    if due_date:
        try:
            from datetime import datetime
            due_ts = datetime.fromisoformat(due_date).timestamp()
        except Exception:
            pass

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "INSERT INTO assignments (course_id, title, description, due_date, due_timestamp, priority, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (course_id, title, description, due_date, due_ts, priority, notes),
    )
    conn.commit()
    assignment_id = cursor.lastrowid
    conn.close()
    return Assignment(id=assignment_id, course_id=course_id, title=title, description=description,
                      due_date=due_date, due_timestamp=due_ts, priority=priority, notes=notes)


def get_upcoming_assignments(days: int = 14) -> list[Assignment]:
    cutoff = time.time() + days * 86400
    now = time.time()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT * FROM assignments WHERE due_timestamp > ? AND due_timestamp < ? AND status != 'completed' ORDER BY due_timestamp",
        (now, cutoff),
    ).fetchall()
    conn.close()
    return [Assignment(*r) for r in rows]


def get_overdue_assignments() -> list[Assignment]:
    now = time.time()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT * FROM assignments WHERE due_timestamp < ? AND due_timestamp > 0 AND status != 'completed' ORDER BY due_timestamp",
        (now,),
    ).fetchall()
    conn.close()
    return [Assignment(*r) for r in rows]


def update_assignment_status(assignment_id: int, status: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE assignments SET status = ? WHERE id = ?", (status, assignment_id))
    conn.commit()
    changed = conn.total_changes > 0
    conn.close()
    return changed


def get_all_courses() -> list[Course]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM courses ORDER BY code").fetchall()
    conn.close()
    return [Course(*r) for r in rows]


async def get_academic_brief() -> str:
    """Build an academic brief: upcoming assignments, overdue items, exams."""
    parts = []

    upcoming = get_upcoming_assignments(7)
    if upcoming:
        lines = [f"- {a.title} (Course #{a.course_id}) due {a.due_date}" for a in upcoming]
        parts.append(f"Due this week ({len(upcoming)}):\n" + "\n".join(lines))
    else:
        parts.append("No assignments due this week.")

    overdue = get_overdue_assignments()
    if overdue:
        lines = [f"- {a.title} (OVERDUE since {a.due_date})" for a in overdue]
        parts.append(f"Overdue ({len(overdue)}):\n" + "\n".join(lines))

    courses = get_all_courses()
    if courses:
        course_list = ", ".join(f"{c.code} ({c.name})" for c in courses)
        parts.append(f"Courses: {course_list}")

    return "\n\n".join(parts) if parts else "No academic data tracked yet. Add your courses and assignments."
