#!/usr/bin/python3

# flask_app.py
# Date:  28/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com
import logging

from rdf_differ.api.entrypoints.api import app, connexion_app

# `connexion_app` is the Connexion 3 ASGI application — serve it with an ASGI server, e.g.
# `gunicorn -k uvicorn.workers.UvicornWorker rdf_differ.api.entrypoints.api.run:connexion_app`.
# Serving the bare Flask `app` would bypass Connexion's routing/validation middleware.
# `app` is kept only to wire Flask's logger to gunicorn's.

if __name__ == "__main__":
    connexion_app.run()
else:
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
