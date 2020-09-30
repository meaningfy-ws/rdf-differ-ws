#!/usr/bin/python3

# config.py
# Date:  18/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Configuration for the current Flask project.
"""
import os

RDF_DIFF_API_ENDPOINT = os.environ.get('RDF_DIFF_API_ENDPOINT', 'http://rdf-differ-api:3040')
