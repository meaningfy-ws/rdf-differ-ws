#!/usr/bin/python3

# flask_app.py
# Date:  28/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

import connexion

from rdf_differ.config import RDF_DIFFER_API_PORT

app = connexion.FlaskApp(__name__, specification_dir='openapi')
app.add_api('openapi.yaml')
app.run(port=RDF_DIFFER_API_PORT)
