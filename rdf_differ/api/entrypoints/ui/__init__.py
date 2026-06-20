"""Web UI entrypoint package (FastAPI + Jinja2).

The application is built in ``app.py`` and served via ``run.py``.
"""

from rdf_differ.api.entrypoints.ui.app import app

__all__ = ["app"]
