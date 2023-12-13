#!/bin/bash
set -o allexport; source bash/.env; set +o allexport

# run ui server
gunicorn --timeout ${RDF_DIFFER_GUNICORN_TIMEOUT} --workers ${RDF_DIFFER_GUNICORN_UI_WORKERS} --bind 0.0.0.0:${RDF_DIFFER_UI_PORT} --reload rdf_differ.entrypoints.ui.run:app --log-file ${RDF_DIFFER_UI_LOGS} --log-level ${RDF_DIFFER_LOG_LEVEL} --daemon