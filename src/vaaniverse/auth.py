"""Simple token-based authentication for VaaniverseAI.

Uses SHA-256 hashed passwords and a signed cookie/token for session
management.  No external auth provider required.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from typing import Dict, Optional

from . import database as db

# Secret key for signing tokens — auto-generated on first run
SECRET_KEY = os.environ.get('VAANIVERSE_SECRET', secrets.token_hex(32))

# Token expiry (seconds) — default 7 days
TOKEN_EXPIRY = int(os.environ.get('VAANIVERSE_TOKEN_EXPIRY', 60 * 60 * 24 * 7))


# ---------------------------------------------------------------------------
# Password hashing (SHA-256 + salt — lightweight, no bcrypt dependency)
# ---------------------------------------------------------------------------

def _hash_password(password: str, salt: Optional[str] = None) -> str:
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}${hashed}"


def _verify_password(password: str, stored: str) -> bool:
    salt, expected = stored.split('$', 1)
    actual = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return hmac.compare_digest(actual, expected)


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

def _make_token(user_id: int) -> str:
    """Create a signed token: user_id.timestamp.signature."""
    ts = str(int(time.time()))
    payload = f"{user_id}.{ts}"
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), 'sha256').hexdigest()[:32]
    return f"{payload}.{sig}"


def _verify_token(token: str) -> Optional[int]:
    """Verify token and return user_id if valid, else None."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        uid_s, ts_s, sig = parts
        # Check signature
        payload = f"{uid_s}.{ts_s}"
        expected = hmac.new(SECRET_KEY.encode(), payload.encode(), 'sha256').hexdigest()[:32]
        if not hmac.compare_digest(sig, expected):
            return None
        # Check expiry
        ts = int(ts_s)
        if time.time() - ts > TOKEN_EXPIRY:
            return None
        return int(uid_s)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register(username: str, password: str, email: str = '') -> Dict:
    """Register a new user. Returns {'ok': True, 'token': ...} or error."""
    if not username or len(username) < 3:
        return {'ok': False, 'error': 'Username must be at least 3 characters'}
    if not password or len(password) < 4:
        return {'ok': False, 'error': 'Password must be at least 4 characters'}

    pw_hash = _hash_password(password)
    uid = db.create_user(username, pw_hash, email)
    if uid is None:
        return {'ok': False, 'error': 'Username or email already taken'}

    token = _make_token(uid)
    return {'ok': True, 'token': token, 'user': {'id': uid, 'username': username}}


def login(username: str, password: str) -> Dict:
    """Authenticate user. Returns {'ok': True, 'token': ...} or error."""
    user = db.get_user_by_username(username)
    if user is None:
        return {'ok': False, 'error': 'Invalid username or password'}
    if not _verify_password(password, user['password']):
        return {'ok': False, 'error': 'Invalid username or password'}

    token = _make_token(user['id'])
    return {
        'ok': True,
        'token': token,
        'user': {'id': user['id'], 'username': user['username']},
    }


def get_current_user(token: str) -> Optional[Dict]:
    """Validate token and return user info, or None."""
    uid = _verify_token(token)
    if uid is None:
        return None
    return db.get_user_by_id(uid)
