import json
import uuid
from app.models.database import get_db


def create_session(requirement):
    session_id = str(uuid.uuid4())[:12]
    name = requirement[:80] if len(requirement) > 80 else requirement
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions (id, name, status) VALUES (?, ?, ?)",
        (session_id, name, "active")
    )
    conn.execute(
        "INSERT INTO iterations (session_id, iteration_number, trigger) VALUES (?, ?, ?)",
        (session_id, 1, "initial")
    )
    conn.commit()
    conn.close()
    return {"id": session_id, "name": name, "status": "active", "iteration": 1}


def get_session(session_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        conn.close()
        return None
    session = dict(row)

    # Get iteration count
    iter_row = conn.execute(
        "SELECT MAX(iteration_number) as max_iter FROM iterations WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    session["iteration_count"] = iter_row["max_iter"] or 1

    # Get artifact count
    art_row = conn.execute(
        "SELECT COUNT(*) as count FROM artifacts WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    session["artifact_count"] = art_row["count"]

    # Get pipeline stages for latest iteration
    stages = conn.execute(
        """SELECT * FROM pipeline_stages
           WHERE session_id = ? AND iteration_number = ?
           ORDER BY id""",
        (session_id, session["iteration_count"])
    ).fetchall()
    session["stages"] = [dict(s) for s in stages]

    # Get board state for latest iteration
    board_row = conn.execute(
        "SELECT board_json FROM board_states WHERE session_id = ? AND iteration_number = ?",
        (session_id, session["iteration_count"])
    ).fetchone()
    session["board_state"] = json.loads(board_row["board_json"]) if board_row else None

    conn.close()
    return session


def list_sessions():
    conn = get_db()
    rows = conn.execute(
        """SELECT s.*,
                  (SELECT MAX(iteration_number) FROM iterations WHERE session_id = s.id) as iteration_count,
                  (SELECT COUNT(*) FROM artifacts WHERE session_id = s.id) as artifact_count
           FROM sessions s
           ORDER BY s.created_at DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_session_status(session_id, status):
    conn = get_db()
    conn.execute(
        "UPDATE sessions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, session_id)
    )
    conn.commit()
    conn.close()


def create_iteration(session_id, trigger="feedback", feedback_text=None):
    conn = get_db()
    # Get current max iteration
    row = conn.execute(
        "SELECT MAX(iteration_number) as max_iter FROM iterations WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    next_iter = (row["max_iter"] or 0) + 1

    conn.execute(
        "INSERT INTO iterations (session_id, iteration_number, trigger, feedback_text) VALUES (?, ?, ?, ?)",
        (session_id, next_iter, trigger, feedback_text)
    )
    conn.commit()
    conn.close()
    return next_iter


def get_session_requirement(session_id):
    """Get the original requirement (session name) for a session."""
    conn = get_db()
    row = conn.execute("SELECT name FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return row["name"] if row else None
