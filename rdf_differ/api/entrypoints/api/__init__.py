"""REST API entrypoint package (FastAPI).

The application is built in ``app.py`` and served via ``run.py``. Kept import-light
so importing the package has no side effects beyond exposing ``app``.
"""

from rdf_differ.api.entrypoints.api.app import app

__all__ = ["app"]
