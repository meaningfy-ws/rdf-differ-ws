#!/usr/bin/python3

# config.py
# Date: 20/07/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

import os

FILENAME = os.environ.get('FILENAME', 'file')
ENDPOINT = os.environ.get('ENDPOINT', 'http://localhost:3030')

RDF_DIFFER_API_PORT = os.environ.get('RDF_DIFFER_API_PORT', 3040),

FUSEKI_USERNAME = os.environ.get('FUSEKI_USERNAME', 'admin')
FUSEKI_PASSWORD = os.environ.get('FUSEKI_PASSWORD', 'admin')
