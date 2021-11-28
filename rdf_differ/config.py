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
from distutils.util import strtobool

TEMPLATES_FOLDER_PATH = Path(__file__).parents[1] / 'resources' / 'templates'

RDF_DIFFER_FILENAME = os.environ.get('RDF_DIFFER_FILENAME', 'file')

if os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION') \
        and Path(os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION')).exists() \
        and any(Path(os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION')).iterdir()):
    APPLICATION_PROFILES_ROOT_FOLDER = os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION')
else:
    APPLICATION_PROFILES_ROOT_FOLDER = TEMPLATES_FOLDER_PATH

RDF_DIFFER_UI_PORT = os.environ.get('RDF_DIFFER_UI_PORT', 8030)

RDF_DIFFER_API_PORT = os.environ.get('RDF_DIFFER_API_PORT', 4030)
RDF_DIFFER_API_LOCATION = os.environ.get('RDF_DIFFER_API_LOCATION', 'http://localhost')
RDF_DIFFER_API_SERVICE = str(RDF_DIFFER_API_LOCATION) + ":" + str(RDF_DIFFER_API_PORT)

RDF_DIFFER_FUSEKI_LOCATION = os.environ.get('RDF_DIFFER_FUSEKI_LOCATION', 'http://localhost')
RDF_DIFFER_FUSEKI_PORT = os.environ.get('RDF_DIFFER_FUSEKI_PORT', 3030)
RDF_DIFFER_FUSEKI_SERVICE = f'{RDF_DIFFER_FUSEKI_LOCATION}:{RDF_DIFFER_FUSEKI_PORT}'

RDF_DIFFER_FUSEKI_USERNAME = os.environ.get('RDF_DIFFER_FUSEKI_USERNAME', 'admin')
RDF_DIFFER_FUSEKI_PASSWORD = os.environ.get('RDF_DIFFER_FUSEKI_PASSWORD', 'admin')

RDF_DIFFER_REDIS_LOCATION = os.environ.get('RDF_DIFFER_REDIS_LOCATION', 'redis://localhost')
RDF_DIFFER_REDIS_PORT = os.environ.get('RDF_DIFFER_REDIS_PORT', 6379)
RDF_DIFFER_REDIS_SERVICE = f'{RDF_DIFFER_REDIS_LOCATION}:{RDF_DIFFER_REDIS_PORT}'

RDF_DIFFER_SECRET_KEY_UI = os.environ.get('RDF_DIFFER_SECRET_KEY_UI', 'secret key ui')
RDF_DIFFER_SECRET_KEY_API = os.environ.get('RDF_DIFFER_SECRET_KEY_API', 'secret key api')

RDF_DIFFER_LOGGER = 'gunicorn.error'

RDF_DIFFER_TIME_FORMAT = os.environ.get('RDF_DIFFER_TIME_FORMAT', '%d-%b-%YT%H:%M:%S')
RDF_DIFFER_TIMEZONE = os.environ.get('RDF_DIFFER_TIMEZONE', 'Europe/Paris')

RDF_DIFFER_FILE_DB = os.environ.get('RDF_DIFFER_FILE_DB', str(Path(__file__).parents[1] / 'db'))
RDF_DIFFER_REPORTS_DB = os.environ.get('RDF_DIFFER_REPORT_DB', str(Path(__file__).parents[1] / 'reports'))

SHOW_SWAGGER_UI = strtobool(os.environ.get('SHOW_SWAGGER_UI', 'true'))
