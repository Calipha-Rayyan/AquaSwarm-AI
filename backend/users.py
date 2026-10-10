"""Accounts for the AquaSwarm control room.

* Passwords are stored as salted scrypt hashes, never in clear text.
* There is no open self-registration: people *request* access and an
  administrator approves them (and chooses their role).
* Password reset uses a short-lived one-time code, either e-mailed (when SMTP
  is configured) or issued by an administrator and passed on out of band.
* Roles: admin (everything), manager (approve deliveries, manage data),
  operator (record readings, confirm deliveries, run analysis).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional

from backend.database import get_connection, query_all, query_one

ROLES = ("admin", "manager", "operator")
STATUSES = ("ACTIVE", "PENDING", "DISABLED")

MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15
RESET_CODE_MINUTES = 30
RESET_CODE_MAX_TRIES = 5

_SCRYPT = (2**14, 8, 1)
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(ValueError):
    """Message is safe to show to the person signing in."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.isoformat()


# ------------------------------------------------------------------ schema
def ensure_schema() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                requested_role TEXT,
                request_note TEXT NOT NULL DEFAULT '',
                failed_logins INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                created_at TEXT NOT NULL,
                last_login_at TEXT
            );
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code_hash TEXT,
                status TEXT NOT NULL,
                tries INTEGER NOT NULL DEFAULT 0,
                requested_at TEXT NOT NULL,
                expires_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()


# ------------------------------------------------------------------ hashing
def hash_password(password: str) -> str:
    n, r, p = _SCRYPT
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=32)
    return "scrypt${}${}${}${}${}".format(
        n, r, p, base64.b64encode(salt).decode(), base64.b64encode(digest).decode()
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, digest_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode(), salt=base64.b64decode(salt_b64),
            n=int(n), r=int(r), p=int(p), dklen=32,
        )
        return hmac.compare_digest(digest, base64.b64decode(digest_b64))
    except Exception:
        return False


_DUMMY_HASH = hash_password("not-a-real-password")  # equalises timing for unknown e-mails


def validate_email(email: str) -> str:
    value = (email or "").strip().lower()
    if not _EMAIL.match(value) or len(value) > 254:
        raise ValueError("Enter a valid e-mail address.")
    return value


def validate_password(password: str) -> None:
    if len(password or "") < 10:
        raise ValueError("Password must be at least 10 characters.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValueError("Password must contain both letters and numbers.")
    if len(password) > 200:
        raise ValueError("Password is too long.")


def _clean_name(name: str) -> str:
    value = re.sub(r"\s+", " ", (name or "").strip())
    if len(value) < 2 or len(value) > 80:
        raise ValueError("Enter your full name (2–80 characters).")
    return value


# ------------------------------------------------------------------ queries
def _public(row: Optional[dict]) -> Optional[dict]:
    if row is None:
        return None
    return {k: row[k] for k in (
        "id", "email", "full_name", "role", "status", "requested_role",
        "request_note", "created_at", "last_login_at",
    )}


def get_user(user_id: int) -> Optional[dict]:
    ensure_schema()
    return _public(query_one("SELECT * FROM users WHERE id = ?", (int(user_id),)))


def has_users() -> bool:
    ensure_schema()
    return bool(query_one("SELECT id FROM users LIMIT 1"))


def list_users() -> list[dict]:
    ensure_schema()
    return [_public(r) for r in query_all("SELECT * FROM users ORDER BY status, full_name")]


def active_emails(roles: Iterable[str]) -> list[str]:
    ensure_schema()
    wanted = tuple(roles)
    marks = ",".join("?" for _ in wanted)
    rows = query_all(f"SELECT email FROM users WHERE status = 'ACTIVE' AND role IN ({marks})", wanted)
    return [r["email"] for r in rows]


def _active_admins() -> int:
    return int(query_one("SELECT COUNT(*) AS c FROM users WHERE status='ACTIVE' AND role='admin'")["c"])


# ------------------------------------------------------------------ accounts
def create_first_admin(email: str, full_name: str, password: str) -> dict:
    """First-run setup. Only works while no account exists."""
    ensure_schema()
    if has_users():
        raise ValueError("Setup is already complete.")
    email, full_name = validate_email(email), _clean_name(full_name)
    validate_password(password)
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, full_name, role, status, password_hash, created_at) "
            "VALUES (?, ?, 'admin', 'ACTIVE', ?, ?)",
            (email, full_name, hash_password(password), _iso(_now())),
        )
        conn.commit()
    return _public(query_one("SELECT * FROM users WHERE email = ?", (email,)))


def request_access(email: str, full_name: str, password: str,
                   requested_role: str = "operator", note: str = "") -> None:
    ensure_schema()
    email, full_name = validate_email(email), _clean_name(full_name)
    validate_password(password)
    role = requested_role if requested_role in ROLES and requested_role != "admin" else "operator"
    if query_one("SELECT id FROM users WHERE email = ?", (email,)):
        raise ValueError("An account or access request already exists for this e-mail.")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (email, full_name, role, status, password_hash, requested_role, "
            "request_note, created_at) VALUES (?, ?, ?, 'PENDING', ?, ?, ?, ?)",
            (email, full_name, role, hash_password(password), role, (note or "").strip()[:300], _iso(_now())),
        )
        conn.commit()
    try:  # tell administrators, when mail is configured
        from backend.notify import send_email

        admins = active_emails(("admin",))
        send_email(admins, "AquaSwarm: new access request",
                   f"{full_name} ({email}) requested {role} access. Review it under Team access.")
    except Exception:
        pass


def authenticate(email: str, password: str) -> dict:
    """Return the user, or raise AuthError with a safe message."""
    ensure_schema()
    email = (email or "").strip().lower()
    row = query_one("SELECT * FROM users WHERE email = ?", (email,))

    if row is None:
        verify_password(password or "", _DUMMY_HASH)
        raise AuthError("Invalid e-mail or password.")

    locked_until = row.get("locked_until")
    if locked_until and datetime.fromisoformat(locked_until) > _now():
        minutes = max(1, int((datetime.fromisoformat(locked_until) - _now()).total_seconds() // 60) + 1)
        raise AuthError(f"Too many failed attempts. Try again in about {minutes} minute(s).")

    if not verify_password(password or "", row["password_hash"]):
        failures = int(row["failed_logins"]) + 1
        lock = _iso(_now() + timedelta(minutes=LOCKOUT_MINUTES)) if failures >= MAX_FAILED_LOGINS else None
        with get_connection() as conn:
            conn.execute("UPDATE users SET failed_logins = ?, locked_until = ? WHERE id = ?",
                         (0 if lock else failures, lock, row["id"]))
            conn.commit()
        raise AuthError("Invalid e-mail or password.")

    if row["status"] == "PENDING":
        raise AuthError("Your access request is waiting for administrator approval.")
    if row["status"] != "ACTIVE":
        raise AuthError("This account is disabled. Contact an administrator.")

    with get_connection() as conn:
        conn.execute("UPDATE users SET failed_logins = 0, locked_until = NULL, last_login_at = ? WHERE id = ?",
                     (_iso(_now()), row["id"]))
        conn.commit()
    return _public(query_one("SELECT * FROM users WHERE id = ?", (row["id"],)))


def approve_user(user_id: int, role: str) -> None:
    ensure_schema()
    if role not in ROLES:
        raise ValueError("Unknown role.")
    with get_connection() as conn:
        conn.execute("UPDATE users SET status='ACTIVE', role=? WHERE id=? AND status='PENDING'", (role, int(user_id)))
        conn.commit()
    row = query_one("SELECT email, full_name FROM users WHERE id = ?", (int(user_id),))
    if row:
        try:
            from backend.notify import send_email

            send_email(row["email"], "AquaSwarm access approved",
                       f"Hello {row['full_name']}, your access was approved with the {role} role.")
        except Exception:
            pass


def reject_request(user_id: int) -> None:
    ensure_schema()
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id=? AND status='PENDING'", (int(user_id),))
        conn.commit()


def set_role(user_id: int, role: str) -> None:
    ensure_schema()
    if role not in ROLES:
        raise ValueError("Unknown role.")
    target = query_one("SELECT * FROM users WHERE id = ?", (int(user_id),))
    if not target:
        raise ValueError("User not found.")
    if target["role"] == "admin" and role != "admin" and target["status"] == "ACTIVE" and _active_admins() <= 1:
        raise ValueError("At least one active administrator is required.")
    with get_connection() as conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, int(user_id)))
        conn.commit()


def set_status(user_id: int, status: str) -> None:
    ensure_schema()
    if status not in ("ACTIVE", "DISABLED"):
        raise ValueError("Status must be ACTIVE or DISABLED.")
    target = query_one("SELECT * FROM users WHERE id = ?", (int(user_id),))
    if not target:
        raise ValueError("User not found.")
    if target["role"] == "admin" and status == "DISABLED" and target["status"] == "ACTIVE" and _active_admins() <= 1:
        raise ValueError("At least one active administrator is required.")
    with get_connection() as conn:
        conn.execute("UPDATE users SET status = ?, failed_logins = 0, locked_until = NULL WHERE id = ?",
                     (status, int(user_id)))
        conn.commit()


def change_password(user_id: int, current: str, new: str) -> None:
    ensure_schema()
    row = query_one("SELECT * FROM users WHERE id = ?", (int(user_id),))
    if not row or not verify_password(current or "", row["password_hash"]):
        raise ValueError("Current password is incorrect.")
    validate_password(new)
    with get_connection() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new), int(user_id)))
        conn.commit()


# ------------------------------------------------------------------ password reset
def _new_code() -> str:
    return "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(8))


def _issue(reset_id: int) -> str:
    code = _new_code()
    with get_connection() as conn:
        conn.execute(
            "UPDATE password_resets SET code_hash = ?, status = 'ISSUED', tries = 0, expires_at = ? WHERE id = ?",
            (hash_password(code), _iso(_now() + timedelta(minutes=RESET_CODE_MINUTES)), reset_id),
        )
        conn.commit()
    return code


def request_password_reset(email: str) -> None:
    """Always succeeds from the caller's view (no account enumeration)."""
    ensure_schema()
    email = (email or "").strip().lower()
    user = query_one("SELECT * FROM users WHERE email = ? AND status = 'ACTIVE'", (email,))
    if not user:
        return
    with get_connection() as conn:
        conn.execute("DELETE FROM password_resets WHERE user_id = ? AND status IN ('REQUESTED','ISSUED')", (user["id"],))
        cur = conn.execute(
            "INSERT INTO password_resets (user_id, status, requested_at) VALUES (?, 'REQUESTED', ?)",
            (user["id"], _iso(_now())),
        )
        conn.commit()
        reset_id = int(cur.lastrowid)

    from backend.notify import configured, send_email

    if configured():
        code = _issue(reset_id)
        sent = send_email(email, "AquaSwarm password reset code",
                          f"Your one-time code is {code}. It expires in {RESET_CODE_MINUTES} minutes. "
                          "If you did not request this, ignore this message.")
        if not sent:  # keep it in the administrator queue instead
            with get_connection() as conn:
                conn.execute("UPDATE password_resets SET status='REQUESTED', code_hash=NULL, expires_at=NULL WHERE id=?",
                             (reset_id,))
                conn.commit()


def pending_resets() -> list[dict]:
    ensure_schema()
    return query_all(
        "SELECT r.id, r.requested_at, r.status, u.email, u.full_name FROM password_resets r "
        "JOIN users u ON u.id = r.user_id WHERE r.status IN ('REQUESTED','ISSUED') ORDER BY r.requested_at"
    )


def issue_reset_code(reset_id: int) -> str:
    """Administrator action: returns the clear code once, to hand over out of band."""
    ensure_schema()
    if not query_one("SELECT id FROM password_resets WHERE id = ? AND status IN ('REQUESTED','ISSUED')", (int(reset_id),)):
        raise ValueError("Reset request not found.")
    return _issue(int(reset_id))


def complete_password_reset(email: str, code: str, new_password: str) -> None:
    ensure_schema()
    validate_password(new_password)
    email = (email or "").strip().lower()
    generic = ValueError("That code is invalid or has expired.")
    user = query_one("SELECT * FROM users WHERE email = ? AND status = 'ACTIVE'", (email,))
    if not user:
        raise generic
    reset = query_one(
        "SELECT * FROM password_resets WHERE user_id = ? AND status = 'ISSUED' ORDER BY id DESC LIMIT 1", (user["id"],)
    )
    if not reset or not reset["expires_at"] or datetime.fromisoformat(reset["expires_at"]) < _now():
        raise generic
    if int(reset["tries"]) >= RESET_CODE_MAX_TRIES:
        raise ValueError("Too many attempts. Request a new code.")

    ok = verify_password((code or "").strip().upper(), reset["code_hash"])
    with get_connection() as conn:
        if not ok:
            conn.execute("UPDATE password_resets SET tries = tries + 1 WHERE id = ?", (reset["id"],))
            conn.commit()
            raise generic
        conn.execute("UPDATE users SET password_hash=?, failed_logins=0, locked_until=NULL WHERE id=?",
                     (hash_password(new_password), user["id"]))
        conn.execute("UPDATE password_resets SET status='USED', code_hash=NULL WHERE id=?", (reset["id"],))
        conn.commit()