#!/usr/bin/python3

# config.py
# Date: 20/07/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Project wide configuration file.
"""

import os

RDF_DIFFER_FILENAME = os.environ.get('FILENAME', 'file')

RDF_DIFFER_UI_PORT = os.environ.get('RDF_DIFFER_UI_PORT', 8030)

RDF_DIFFER_API_PORT = os.environ.get('RDF_DIFFER_API_PORT', 4030)
RDF_DIFFER_API_LOCATION = os.environ.get('RDF_DIFFER_API_LOCATION', 'http://localhost')
RDF_DIFFER_API_SERVICE = str(RDF_DIFFER_API_LOCATION) + ":" + '3030'

RDF_DIFFER_ENDPOINT_PORT = os.environ.get('RDF_DIFFER_FUSEKI_SERVICE', 3030)
RDF_DIFFER_ENDPOINT_LOCATION = os.environ.get('RDF_DIFFER_FUSEKI_LOCATION', 'http://localhost')
RDF_DIFFER_ENDPOINT_SERVICE = str(RDF_DIFFER_ENDPOINT_LOCATION) + ":" + str(RDF_DIFFER_ENDPOINT_PORT)

RDF_DIFFER_FUSEKI_USERNAME = os.environ.get('RDF_DIFFER_FUSEKI_USERNAME', 'admin')
RDF_DIFFER_FUSEKI_PASSWORD = os.environ.get('RDF_DIFFER_FUSEKI_PASSWORD', 'admin')

RDF_DIFFER_SECRET_KEY_UI = os.environ.get('RDF_DIFFER_SECRET_KEY_UI', 'RDF_DIFFER_SECRET_KEY_UI')
RDF_DIFFER_SECRET_KEY_API = os.environ.get('RDF_DIFFER_SECRET_KEY_API', 'RDF_DIFFER_SECRET_KEY_API')
