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

# TODO: this shall be deprecated because now we shall rely on the APManager
TEMPLATES_FOLDER_PATH = Path(__file__).parents[1] / 'resources' / 'templates'

# # TODO: this is teh discovery path
# APPLICATION_PROFILE_ROOT_FOLDER = Path(os.environ.get('RDF_DIFFER_APPLICATION_PROFILE_ROOT_FOLDER', '...'))


RDF_DIFFER_FILENAME = os.environ.get('RDF_DIFFER_FILENAME', 'file')

if os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION') \
        and Path(os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION')).exists() \
        and any(Path(os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION')).iterdir()):
    RDF_DIFFER_REPORT_TEMPLATE_LOCATION = os.environ.get('RDF_DIFFER_TEMPLATE_LOCATION')
else:
    RDF_DIFFER_REPORT_TEMPLATE_LOCATION = TEMPLATES_FOLDER_PATH

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

RDF_DIFFER_APPLICATION_PROFILES_LIST = os.listdir(TEMPLATES_FOLDER_PATH)


