"""
Shared database helper for the SCIAS Streamlit frontend.

Uses the same db/scias.db and chat_history table that orchestrator.py's
save_to_history() already writes to, so history logged from the frontend
pages and history logged from the voice pipeline show up in the same place.
"""

import sqlite3
import os
import hashlib

DB_PATH = "db/scias.db"


def save_interaction(session_id: str, agent_used: str, user_message: str, assistant_message: str):
    """Logs one user+assistant turn to chat_history."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (session_id, role, message, agent_used) VALUES (?, ?, ?, ?)",
        (session_id, "user", user_message, agent_used),
    )
    cursor.execute(
        "INSERT INTO chat_history (session_id, role, message, agent_used) VALUES (?, ?, ?, ?)",
        (session_id, "assistant", assistant_message, agent_used),
    )
    conn.commit()
    conn.close()


def load_history(limit: int = 100):
    """Returns the most recent chat_history rows, newest first."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT session_id, role, message, agent_used, rowid "
        "FROM chat_history ORDER BY rowid DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def load_session_ids(limit: int = 30):
    """Returns distinct recent session IDs, newest first, for filtering the history view."""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT session_id FROM chat_history ORDER BY rowid DESC LIMIT ?",
        (limit,),
    )
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Auth: users table for the login page
# ---------------------------------------------------------------------------

def init_users_table():
    """Creates the users table if it doesn't exist yet. Safe to call on every startup."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'farmer'
        )
        """
    )
    conn.commit()
    conn.close()


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str, role: str = "farmer"):
    """Returns True on success, False if the username already exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, _hash_password(password), role),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_user(username: str, password: str):
    """Returns {'username', 'role'} on success, None on failure."""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password_hash, role FROM users WHERE username = ?", (username,)
    )
    row = cursor.fetchone()
    conn.close()
    if row and row[0] == _hash_password(password):
        return {"username": username, "role": row[1]}
    return None