#!/bin/bash

# stop celery
celery -A rdf_differ.services.celery.celery_worker control shutdown
pkill -f gunicorn