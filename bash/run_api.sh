#!/bin/bash
set -o allexport; source bash/.env; set +o allexport

# run celery
celery -A rdf_differ.services.celery.celery_worker worker --loglevel ${RDF_DIFFER_LOG_LEVEL} --logfile ${RDF_DIFFER_CELERY_LOGS} --detach

# run api server (Connexion 3 is ASGI → gunicorn with the UvicornWorker on the ASGI app)
gunicorn -k uvicorn.workers.UvicornWorker --timeout ${RDF_DIFFER_GUNICORN_TIMEOUT} --workers ${RDF_DIFFER_GUNICORN_API_WORKERS} --bind 0.0.0.0:${RDF_DIFFER_API_PORT} --reload rdf_differ.entrypoints.api.run:connexion_app --log-file ${RDF_DIFFER_API_LOGS} --log-level ${RDF_DIFFER_LOG_LEVEL} --daemon