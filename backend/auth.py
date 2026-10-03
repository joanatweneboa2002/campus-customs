"""Customer accounts: password hashing, login sessions, and "who is this request from?".

Passwords are never stored, only a salted, slow hash of them (PBKDF2-HMAC-SHA256):
    pbkdf2_sha256$600000$<salt>$<hex digest>   new format: iteration count stored in the hash
    pbkdf2_sha256$<salt>$<hex digest>          legacy format already in the table (120,000 iterations)
Legacy hashes still verify, and are upgraded to the new format the next time that person logs in.
Wrong-password attempts are throttled per email to slow down password guessing.

Sessions: login returns a random token (kept in the browser). The database only stores
SHA-256(token), so a leaked database can't be used to log in as anyone.
"""

import hashlib
import hmac
import secrets
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException

from db import get_write_db
from models import CustomerInfo, PublicUser

ITERATIONS = 600_000  # OWASP's current recommendation for PBKDF2-HMAC-SHA256
LEGACY_ITERATIONS = 120_000  # what the seeded accounts were hashed with
SALT_BYTES = 16
SESSION_DAYS = 30
MAX_FAILED_LOGINS = 5  # per email, within FAILED_WINDOW
FAILED_WINDOW = timedelta(minutes=15)

_failed: dict[str, list[datetime]] = defaultdict(list)  # email -> recent failed attempts (in memory)


def _pbkdf2(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    return f"pbkdf2_sha256${ITERATIONS}${salt}${_pbkdf2(password, salt, ITERATIONS)}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time check against either the new or the legacy hash format."""
    parts = stored.split("$")
    if len(parts) == 4 and parts[0] == "pbkdf2_sha256" and parts[1].isdigit():
        _, iterations, salt, digest = parts
        return hmac.compare_digest(_pbkdf2(password, salt, int(iterations)), digest)
    if len(parts) == 3 and parts[0] == "pbkdf2_sha256":
        _, salt, digest = parts
        return hmac.compare_digest(_pbkdf2(password, salt, LEGACY_ITERATIONS), digest)
    return False


def needs_rehash(stored: str) -> bool:
    parts = stored.split("$")
    return not (len(parts) == 4 and parts[1].isdigit() and int(parts[1]) >= ITERATIONS)


# Used when the email doesn't exist, so the response takes as long as a real check
# (otherwise timing would reveal which emails have accounts).
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def _too_many_failures(email: str) -> bool:
    cutoff = datetime.now(timezone.utc) - FAILED_WINDOW
    _failed[email] = [t for t in _failed[email] if t > cutoff]
    return len(_failed[email]) >= MAX_FAILED_LOGINS


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _public(row) -> PublicUser:
    first = row["first_name"] or row["name"].split()[0]
    return PublicUser(id=row["id"], name=row["name"], first_name=first, email=row["email"])


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    with get_write_db() as conn:
        conn.execute(
            "INSERT INTO user_sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_token_hash(token), user_id, expires),
        )
    return token


def login(email: str, password: str) -> tuple[str, PublicUser]:
    email = email.strip().lower()
    if _too_many_failures(email):
        raise HTTPException(status_code=429, detail="Too many tries. Please wait 15 minutes and try again.")
    with get_write_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
    ok = verify_password(password, row["password_hash"] if row else _DUMMY_HASH)
    # Same message either way, so the form doesn't reveal which emails have accounts.
    if row is None or not ok:
        _failed[email].append(datetime.now(timezone.utc))
        raise HTTPException(status_code=401, detail="Wrong email or password")
    _failed.pop(email, None)
    if needs_rehash(row["password_hash"]):  # upgrade old/weaker hashes while we know the password
        with get_write_db() as conn:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(password), row["id"]))
    return create_session(row["id"]), _public(row)


def signup(first_name: str, last_name: str, email: str, password: str) -> tuple[str, PublicUser]:
    first, last, email = first_name.strip(), last_name.strip(), email.strip().lower()
    with get_write_db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE LOWER(email) = ?", (email,)).fetchone():
            raise HTTPException(status_code=409, detail="That email already has an account. Try logging in!")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (f"{first} {last}", email, hash_password(password), first, last),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return create_session(row["id"]), _public(row)


def logout(token: str) -> None:
    with get_write_db() as conn:
        conn.execute("DELETE FROM user_sessions WHERE token_hash = ?", (_token_hash(token),))


def user_for_token(token: str | None) -> PublicUser | None:
    if not token:
        return None
    with get_write_db() as conn:
        row = conn.execute(
            """SELECT u.* FROM user_sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > datetime('now')""",
            (_token_hash(token),),
        ).fetchone()
    return _public(row) if row else None


def bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return None


# ---------------------------------------------------------------- FastAPI dependencies


def optional_user(authorization: str | None = Header(default=None)) -> PublicUser | None:
    """Logged-in customer, or None for guests. Used by /api/chat."""
    return user_for_token(bearer_token(authorization))


def required_user(authorization: str | None = Header(default=None)) -> PublicUser:
    user = optional_user(authorization)
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in")
    return user


def customer_info(user: PublicUser) -> CustomerInfo:
    return CustomerInfo(user_id=user.id, name=user.name, first_name=user.first_name, email=user.email)
