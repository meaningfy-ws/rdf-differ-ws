#!/bin/bash

# stop celery
celery -A rdf_differ.adapters.celery.celery_worker control shutdown
pkill -f gunicorn