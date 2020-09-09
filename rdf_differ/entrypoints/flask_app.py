#!/usr/bin/python3

# flask_app.py
# Date:  28/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

import connexion

connexion_app = connexion.FlaskApp(__name__, specification_dir='openapi')
connexion_app.add_api('openapi.yaml')

app = connexion_app.app

if __name__ == '__main__':
    app.run()
