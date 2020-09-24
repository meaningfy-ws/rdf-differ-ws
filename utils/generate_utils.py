#!/usr/bin/python3

# generate_utils.py
# Date:  24/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Module description

"""
from pathlib import Path

DIFF_TEMPLATE_LOCATION = Path(__file__).parents[1] / 'resources/eds_templates/diff_report'


def generate_config_content(endpoint: str):
    return {
        "template": "main.html",
        "conf":
            {
                "default_endpoint": endpoint,
                "title": "Dataset Diff Report",
                "type": "report"
            }
    }
