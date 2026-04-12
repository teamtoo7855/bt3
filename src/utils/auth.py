from __future__ import annotations

from flask import session


def get_current_user():
    """Return the currently logged-in username (or None)."""
    if not session.get("logged_in"):
        return None
    return session.get("username")
