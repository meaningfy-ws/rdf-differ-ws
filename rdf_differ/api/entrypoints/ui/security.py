"""CSRF protection for the UI's state-changing forms (EPIC api-ui-fastapi-modernization).

A per-session token is stored in the signed session (Starlette ``SessionMiddleware``),
rendered as a hidden field in every form, and verified on every POST with a constant-time
compare. No extra dependency — replaces the CSRF guard Flask-WTF used to provide.
"""

import hmac
import secrets

from fastapi import HTTPException, Request, status

_CSRF_KEY = "csrf_token"


def ensure_csrf_token(request: Request) -> str:
    """Return the session CSRF token, creating one on first use."""
    token = request.session.get(_CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[_CSRF_KEY] = token
    return token


def validate_csrf(request: Request, submitted: str) -> None:
    """Reject the request unless the submitted token matches the session token."""
    expected = request.session.get(_CSRF_KEY, "")
    if not expected or not submitted or not hmac.compare_digest(expected, submitted):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid or missing CSRF token")
