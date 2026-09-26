from datetime import datetime
import os
import sqlite3
import sys


# Database Operations Class


class TaskDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, "data", "planner.db")
        else:
            self.db_path = db_path

    def _get_connection(self):
        folder = os.path.dirname(self.db_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def setup_tables(self):
        t_table = (
            "CREATE TABLE IF NOT EXISTS tasks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "title TEXT NOT NULL, "
            "description TEXT, "
            "task_type TEXT NOT NULL CHECK (task_type IN ('outdoor', 'indoor')), "
            "priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')), "
            "deadline TEXT, "
            "status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'rescheduled', 'completed', 'cancelled')), "
            "original_date TEXT, "
            "scheduled_date TEXT, "
            "created_at TEXT NOT NULL, "
            "updated_at TEXT NOT NULL"
            ");"
        )
        f_table = (
            "CREATE TABLE IF NOT EXISTS forecasts ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "location TEXT NOT NULL, "
            "forecast_date TEXT NOT NULL, "
            "temperature_c REAL, "
            "condition TEXT, "
            "wind_speed_kph REAL, "
            "rain_probability REAL, "
            "fetched_at TEXT NOT NULL, "
            "UNIQUE(location, forecast_date)"
            ");"
        )
        l_table = (
            "CREATE TABLE IF NOT EXISTS logs ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "task_id INTEGER, "
            "action TEXT NOT NULL, "
            "details TEXT, "
            "timestamp TEXT NOT NULL, "
            "FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL"
            ");"
        )
        
        c = self._get_connection()
        try:
            cur = c.cursor()
            cur.execute(t_table)
            cur.execute(f_table)
            cur.execute(l_table)
            c.commit()
        finally:
            c.close()


# Singleton database instance for functional compatibility
_DB = TaskDatabase()


def _timestamp():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _log_event(conn, task_id, action, details):
    conn.execute(
        "INSERT INTO logs (task_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
        (task_id, action, details, _timestamp())
    )



# Module Level API Interface


def init_db():
    _DB.setup_tables()


def add_task(title, task_type, description="", priority="medium", deadline=None, scheduled_date=None):
    if task_type not in ["outdoor", "indoor"]:
        raise ValueError("Invalid task_type: must be 'outdoor' or 'indoor'")

    ts = _timestamp()
    query = (
        "INSERT INTO tasks "
        "(title, description, task_type, priority, deadline, status, original_date, scheduled_date, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)"
    )
    
    conn = _DB._get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (title, description, task_type, priority, deadline, scheduled_date, scheduled_date, ts, ts))
        tid = cur.lastrowid
        _log_event(conn, tid, "created", f"Task '{title}' created")
        conn.commit()
        return tid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_tasks(status=None, task_type=None):
    clauses = []
    params = []

    if status:
        clauses.append("status = ?")
        params.append(status)
    if task_type:
        clauses.append("task_type = ?")
        params.append(task_type)

    base = "SELECT * FROM tasks"
    if clauses:
        base += " WHERE " + " AND ".join(clauses)
        
    base += " ORDER BY CASE WHEN scheduled_date IS NULL THEN 1 ELSE 0 END, scheduled_date ASC, priority DESC"

    conn = _DB._get_connection()
    try:
        cur = conn.cursor()
        cur.execute(base, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def get_task(task_id):
    conn = _DB._get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    finally:
        conn.close()


def update_task(task_id, **fields):
    valid_keys = {'title', 'description', 'task_type', 'priority', 'deadline', 'status', 'scheduled_date'}
    updates = {k: v for k, v in fields.items() if k in valid_keys}

    if not updates:
        return False

    updates['updated_at'] = _timestamp()
    assignments = [f"{k} = ?" for k in updates.keys()]
    values = list(updates.values())
    values.append(task_id)

    sql = f"UPDATE tasks SET {', '.join(assignments)} WHERE id = ?"

    conn = _DB._get_connection()
    try:
        conn.execute(sql, values)
        _log_event(conn, task_id, "updated", f"Fields changed: {list(fields.keys())}")
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def reschedule_task(task_id, new_date, reason=""):
    conn = _DB._get_connection()
    try:
        conn.execute(
            "UPDATE tasks SET scheduled_date = ?, status = 'rescheduled', updated_at = ? WHERE id = ?",
            (new_date, _timestamp(), task_id)
        )
        _log_event(conn, task_id, "rescheduled", f"Moved to {new_date}. Reason: {reason}")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def complete_task(task_id):
    conn = _DB._get_connection()
    try:
        conn.execute(
            "UPDATE tasks SET status = 'completed', updated_at = ? WHERE id = ?",
            (_timestamp(), task_id)
        )
        _log_event(conn, task_id, "completed", "Task marked complete")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_task(task_id):
    conn = _DB._get_connection()
    try:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        _log_event(conn, None, "deleted", f"Task {task_id} deleted")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()



# Weather Cache


def save_forecast(location, forecast_date, temperature_c, condition, wind_speed_kph, rain_probability):
    stmt = (
        "INSERT INTO forecasts (location, forecast_date, temperature_c, condition, wind_speed_kph, rain_probability, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(location, forecast_date) DO UPDATE SET "
        "temperature_c = excluded.temperature_c, "
        "condition = excluded.condition, "
        "wind_speed_kph = excluded.wind_speed_kph, "
        "rain_probability = excluded.rain_probability, "
        "fetched_at = excluded.fetched_at"
    )
    conn = _DB._get_connection()
    try:
        conn.execute(stmt, (location, forecast_date, temperature_c, condition, wind_speed_kph, rain_probability, _timestamp()))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_forecast(location, forecast_date):
    conn = _DB._get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM forecasts WHERE location = ? AND forecast_date = ?",
            (location, forecast_date)
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    finally:
        conn.close()


def get_forecast_range(location, start_date, end_date):
    conn = _DB._get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM forecasts WHERE location = ? AND forecast_date BETWEEN ? AND ? ORDER BY forecast_date",
            (location, start_date, end_date)
        )
        rows = cur.fetchall()
        if not rows:
            return []
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()



# Logging API


def get_logs(task_id=None, limit=100):
    query = "SELECT * FROM logs"
    binds = []

    if task_id is not None:
        query += " WHERE task_id = ?"
        binds.append(task_id)

    query += " ORDER BY timestamp DESC LIMIT ?"
    binds.append(limit)

    conn = _DB._get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, binds)
        rows = cur.fetchall()
        if not rows:
            return []
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        init_db()
        print(f"Initialized database schema at {_DB.db_path}")