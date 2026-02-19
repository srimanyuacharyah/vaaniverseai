"""Lightweight SQLite database for user accounts and creation history."""
from __future__ import annotations

import os
import sqlite3
import json
import datetime
from typing import Dict, List, Optional
from pathlib import Path

DB_PATH = os.environ.get('VAANIVERSE_DB', './vaaniverse.db')


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            email       TEXT    UNIQUE,
            password    TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            type        TEXT    NOT NULL,
            title       TEXT    DEFAULT '',
            data        TEXT    DEFAULT '{}',
            audio_path  TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def create_user(username: str, password_hash: str, email: str = '') -> Optional[int]:
    """Insert a new user. Returns user id or None on duplicate."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        conn.commit()
        uid = cur.lastrowid
        conn.close()
        return uid
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_user_by_username(username: str) -> Optional[Dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(uid: int) -> Optional[Dict]:
    conn = _get_conn()
    row = conn.execute("SELECT id, username, email, created_at FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# History CRUD
# ---------------------------------------------------------------------------

def save_history(
    user_id: int,
    entry_type: str,
    title: str = '',
    data: Optional[Dict] = None,
    audio_path: str = '',
) -> int:
    """Save a creation to history. Returns the history entry id."""
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO history (user_id, type, title, data, audio_path) VALUES (?, ?, ?, ?, ?)",
        (user_id, entry_type, title, json.dumps(data or {}), audio_path),
    )
    conn.commit()
    hid = cur.lastrowid
    conn.close()
    return hid


def get_history(user_id: int, limit: int = 50) -> List[Dict]:
    """Get recent history for a user."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d['data'] = json.loads(d['data'])
        except Exception:
            pass
        result.append(d)
    return result


def delete_history_item(item_id: int, user_id: int) -> bool:
    """Delete a history item (only if owned by user)."""
    conn = _get_conn()
    cur = conn.execute(
        "DELETE FROM history WHERE id = ? AND user_id = ?",
        (item_id, user_id),
    )
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


# Auto-init on import
init_db()
