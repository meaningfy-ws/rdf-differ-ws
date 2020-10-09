#!/usr/bin/python3

# __init__.py
# Date:  17/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com


"""
Module for configuring the Flask server for UI
"""

from flask import Flask
from flask_bootstrap import Bootstrap
from rdf_differ.config import RDF_DIFFER_SECRET_KEY_UI

app = Flask(__name__)
Bootstrap(app)

app.config['SECRET_KEY'] = RDF_DIFFER_SECRET_KEY_UI

from . import views
