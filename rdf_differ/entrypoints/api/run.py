#!/usr/bin/python3

# flask_app.py
# Date:  28/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com
import logging

from rdf_differ.entrypoints.api import app

if __name__ == '__main__':
    app.run()

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
