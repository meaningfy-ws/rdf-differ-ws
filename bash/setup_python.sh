#!/bin/bash
set -o allexport; source bash/.env; set +o allexport

python3.8 -m venv env
source env/bin/activate
pip install -r requirements/prod.txt