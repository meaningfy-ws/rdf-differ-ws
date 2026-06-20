#!/usr/bin/python3

"""Uvicorn/Gunicorn entrypoint for the REST API.

Serve the FastAPI ASGI app with an ASGI server, e.g.
``gunicorn -k uvicorn.workers.UvicornWorker rdf_differ.api.entrypoints.api.run:app``.
"""

from rdf_differ.api.entrypoints.api.app import app

__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8030)
