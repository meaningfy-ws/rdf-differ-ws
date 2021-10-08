#!/usr/bin/python3

# __init__.py
# Date:  17/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Module for configuring and exposing the connexion api server using the Flask framework for API
"""

import connexion

from rdf_differ.config import RDF_DIFFER_SECRET_KEY_API, SHOW_SWAGGER_UI

connexion_app = connexion.FlaskApp(__name__, specification_dir='openapi',
                                   options={"swagger_ui": SHOW_SWAGGER_UI})
connexion_app.add_api('openapi.yaml')

app = connexion_app.app
app.config['SECRET_KEY'] = RDF_DIFFER_SECRET_KEY_API
