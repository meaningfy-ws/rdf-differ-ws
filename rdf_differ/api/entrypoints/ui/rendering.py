"""Jinja2 templating and flash-message helpers for the UI.

Kept separate from ``app.py`` so routes can import the renderer without a cycle.
Flash messages live in the signed session (Starlette ``SessionMiddleware``); they
survive the POST -> redirect -> GET pattern and are popped on render.
"""

from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from rdf_differ.api.entrypoints.ui.security import ensure_csrf_token

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

_FLASH_KEY = "_flashes"


def flash(request: Request, message: str, category: str = "info") -> None:
    """Queue a flash message for the next rendered page."""
    request.session.setdefault(_FLASH_KEY, []).append({"message": message, "category": category})


def pop_flashes(request: Request) -> list[dict]:
    """Return and clear the queued flash messages."""
    flashes: list[dict] = request.session.pop(_FLASH_KEY, [])
    return flashes


def render(request: Request, name: str, **context) -> HTMLResponse:
    """Render a template with the queued flashes injected."""
    return templates.TemplateResponse(
        request=request,
        name=name,
        context={
            "flashes": pop_flashes(request),
            "csrf_token": ensure_csrf_token(request),
            **context,
        },
    )
