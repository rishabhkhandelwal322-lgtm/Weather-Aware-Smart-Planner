"""
storage.py
-----------
SQLite storage layer for the Weather-Aware Smart Planner.

Handles all database interactions: schema creation, and CRUD
operations for tasks, cached forecasts, and activity logs.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "planner.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    description     TEXT,
    task_type       TEXT NOT NULL CHECK (task_type IN ('outdoor', 'indoor')),
    priority        TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    deadline        TEXT,                     -- ISO date string, nullable
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'rescheduled', 'completed', 'cancelled')),
    original_date   TEXT,                     -- date it was first scheduled for
    scheduled_date  TEXT,                     -- current scheduled date (may differ after reschedule)
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS forecasts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    location        TEXT NOT NULL,
    forecast_date   TEXT NOT NULL,             -- date the forecast is FOR
    temperature_c   REAL,
    condition       TEXT,                      -- e.g. 'Rain', 'Clear', 'Clouds'
    wind_speed_kph   REAL,
    rain_probability REAL,                     -- 0.0 - 1.0
    fetched_at      TEXT NOT NULL,
    UNIQUE(location, forecast_date)
);

CREATE TABLE IF NOT EXISTS logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         INTEGER,
    action          TEXT NOT NULL,             -- e.g. 'created', 'rescheduled', 'completed'
    details         TEXT,
    timestamp       TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);
"""


@contextmanager
def get_connection():
    """Context-managed SQLite connection with foreign keys enabled."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they do not already exist."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def _now():
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------- tasks ----

def add_task(title, task_type, description="", priority="medium",
             deadline=None, scheduled_date=None):
    """Insert a new task and return its id."""
    if task_type not in ("outdoor", "indoor"):
        raise ValueError("task_type must be 'outdoor' or 'indoor'")

    now = _now()
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO tasks
               (title, description, task_type, priority, deadline,
                status, original_date, scheduled_date, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
            (title, description, task_type, priority, deadline,
             scheduled_date, scheduled_date, now, now),
        )
        task_id = cursor.lastrowid
        _log(conn, task_id, "created", f"Task '{title}' created")
        return task_id


def get_tasks(status=None, task_type=None):
    """Return tasks, optionally filtered by status and/or type."""
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if task_type:
        query += " AND task_type = ?"
        params.append(task_type)
    query += " ORDER BY scheduled_date IS NULL, scheduled_date, priority DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_task(task_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row else None


def update_task(task_id, **fields):
    """Update arbitrary allowed fields on a task."""
    allowed = {"title", "description", "task_type", "priority", "deadline",
               "status", "scheduled_date"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False

    updates["updated_at"] = _now()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [task_id]

    with get_connection() as conn:
        conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        _log(conn, task_id, "updated", f"Fields changed: {list(fields.keys())}")
        return True


def reschedule_task(task_id, new_date, reason=""):
    """Convenience wrapper: move a task to a new date and mark it rescheduled."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET scheduled_date = ?, status = 'rescheduled', updated_at = ? WHERE id = ?",
            (new_date, _now(), task_id),
        )
        _log(conn, task_id, "rescheduled", f"Moved to {new_date}. Reason: {reason}")


def complete_task(task_id):
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET status = 'completed', updated_at = ? WHERE id = ?",
            (_now(), task_id),
        )
        _log(conn, task_id, "completed", "Task marked complete")


def delete_task(task_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        _log(conn, None, "deleted", f"Task {task_id} deleted")


# ----------------------------------------------------------- forecasts ----

def save_forecast(location, forecast_date, temperature_c, condition,
                   wind_speed_kph, rain_probability):
    """Insert or replace a cached forecast for a given location/date."""
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO forecasts
               (location, forecast_date, temperature_c, condition,
                wind_speed_kph, rain_probability, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(location, forecast_date) DO UPDATE SET
                 temperature_c = excluded.temperature_c,
                 condition = excluded.condition,
                 wind_speed_kph = excluded.wind_speed_kph,
                 rain_probability = excluded.rain_probability,
                 fetched_at = excluded.fetched_at""",
            (location, forecast_date, temperature_c, condition,
             wind_speed_kph, rain_probability, _now()),
        )


def get_forecast(location, forecast_date):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM forecasts WHERE location = ? AND forecast_date = ?",
            (location, forecast_date),
        ).fetchone()
        return dict(row) if row else None


def get_forecast_range(location, start_date, end_date):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM forecasts
               WHERE location = ? AND forecast_date BETWEEN ? AND ?
               ORDER BY forecast_date""",
            (location, start_date, end_date),
        ).fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------- logs ----

def _log(conn, task_id, action, details):
    """Internal helper: write a log entry using an existing open connection."""
    conn.execute(
        "INSERT INTO logs (task_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
        (task_id, action, details, _now()),
    )


def get_logs(task_id=None, limit=100):
    query = "SELECT * FROM logs"
    params = []
    if task_id is not None:
        query += " WHERE task_id = ?"
        params.append(task_id)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


if __name__ == "__main__":
    import sys
    if "--init" in sys.argv:
        init_db()
        print(f"Database initialized at {DB_PATH}")
