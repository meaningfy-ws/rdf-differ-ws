#!/usr/bin/python3

# config.py
# Date: 20/07/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Project wide configuration file.
"""
import os
from pathlib import Path

from celery import Celery

RDF_DIFFER_FILENAME = os.environ.get('RDF_DIFFER_FILENAME', 'file')

if os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION') \
        and Path(os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION')).exists() \
        and any(Path(os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION')).iterdir()):
    RDF_DIFFER_REPORT_TEMPLATE_LOCATION = os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION')
else:
    RDF_DIFFER_REPORT_TEMPLATE_LOCATION = str(Path(__file__).parents[1] / 'resources/templates/')

RDF_DIFFER_UI_PORT = os.environ.get('RDF_DIFFER_UI_PORT', 8030)

RDF_DIFFER_API_PORT = os.environ.get('RDF_DIFFER_API_PORT', 4030)
RDF_DIFFER_API_LOCATION = os.environ.get('RDF_DIFFER_API_LOCATION', 'http://localhost')
RDF_DIFFER_API_SERVICE = str(RDF_DIFFER_API_LOCATION) + ":" + str(RDF_DIFFER_API_PORT)

RDF_DIFFER_FUSEKI_LOCATION = os.environ.get('RDF_DIFFER_FUSEKI_LOCATION', 'http://localhost')
RDF_DIFFER_FUSEKI_SERVICE = str(RDF_DIFFER_FUSEKI_LOCATION) + ":" + '3030'

RDF_DIFFER_FUSEKI_USERNAME = os.environ.get('RDF_DIFFER_FUSEKI_USERNAME', 'admin')
RDF_DIFFER_FUSEKI_PASSWORD = os.environ.get('RDF_DIFFER_FUSEKI_PASSWORD', 'admin')

RDF_DIFFER_SECRET_KEY_UI = os.environ.get('RDF_DIFFER_SECRET_KEY_UI', 'secret key ui')
RDF_DIFFER_SECRET_KEY_API = os.environ.get('RDF_DIFFER_SECRET_KEY_API', 'secret key api')

RDF_DIFFER_LOGGER = 'differ'

RDF_DIFFER_APPLICATION_PROFILES_LIST = os.listdir(RDF_DIFFER_REPORT_TEMPLATE_LOCATION)

RDF_DIFFER_FILE_DB = os.environ.get('RDF_DIFFER_FILE_DB', str(Path(__file__).parents[1] / 'db'))
RDF_DIFFER_REPORTS_DB = os.environ.get('RDF_DIFFER_REPORT_DB', str(Path(__file__).parents[1] / 'reports'))


def get_application_profile_location(application_profile):
    return f'{RDF_DIFFER_REPORT_TEMPLATE_LOCATION}/{application_profile}'


# CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
# CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_worker = Celery('rdf-differ-tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
