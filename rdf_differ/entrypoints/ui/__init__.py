#!/usr/bin/python3

# __init__.py
# Date:  17/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Module description

"""

from flask import Flask
from flask_bootstrap import Bootstrap

from rdf_differ.config import FLASK_SECRET_KEY

app = Flask(__name__)
Bootstrap(app)

app.config['SECRET_KEY'] = FLASK_SECRET_KEY

from rdf_differ.entrypoints.ui import views
