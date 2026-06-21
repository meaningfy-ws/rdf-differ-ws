"""FastAPI + Jinja2 web UI application.

Replaces the Flask UI. Server-rendered pages, signed-session flash messages, a static
mount for the design-system CSS, and status-class request logging.
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from rdf_differ import config
from rdf_differ.api.entrypoints._logging import add_request_logging
from rdf_differ.api.entrypoints.ui.routes import router

logger = logging.getLogger(config.RDF_DIFFER_LOGGER)
_HERE = Path(__file__).parent


def create_app() -> FastAPI:
    """Build and wire the web UI FastAPI application."""
    app = FastAPI(title="RDF Differ UI", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(SessionMiddleware, secret_key=config.RDF_DIFFER_SECRET_KEY_UI)
    app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")
    app.include_router(router)
    add_request_logging(app, logger)
    return app


app = create_app()
