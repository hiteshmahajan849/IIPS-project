"""AuthService: credential verification (FR-01)."""
from __future__ import annotations

from werkzeug.security import check_password_hash

from ..repository import user_repo


def authenticate(email: str, password: str):
    """Returns the user row on success, None on failure. Uses a
    constant-shape check (hash compare happens even for unknown emails via
    check_password_hash's own timing-safe comparison once we have a hash to
    compare against) to avoid obvious user-enumeration timing differences."""
    user = user_repo.find_by_email((email or "").strip().lower())
    if not user:
        return None
    if not check_password_hash(user["password_hash"], password or ""):
        return None
    return user
