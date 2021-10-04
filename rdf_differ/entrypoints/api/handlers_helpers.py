#!/usr/bin/python3

# handlers_helpers.py
# Date: 7/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
import json
from pathlib import Path

from rdf_differ import config


def generate_report_builder_config(template_location, dataset: dict):
    config_dict = json.loads((Path(template_location) / "config.json").read_bytes())
    config_dict["conf"]["default_endpoint"] = dataset['query_url']
    return config_dict
