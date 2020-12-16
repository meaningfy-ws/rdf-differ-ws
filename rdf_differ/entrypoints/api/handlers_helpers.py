#!/usr/bin/python3

# handlers_helpers.py
# Date: 7/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
import json
from pathlib import Path

from rdf_differ import config


def generate_report_builder_config(dataset: dict):
    config_dict = json.loads((Path(config.RDF_DIFFER_REPORT_TEMPLATE_LOCATION) / "config.json").read_bytes())
    config_dict["conf"]["default_endpoint"] = dataset['query_url']
    return config_dict
