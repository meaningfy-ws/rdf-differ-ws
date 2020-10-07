#!/usr/bin/python3

# handlers_helpers.py
# Date: 7/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com


def generate_report_builder_config(dataset: dict, title: str = "Dataset Diff Report"):
    return {
        "template": "main.html",
        "conf":
            {
                "default_endpoint": dataset['query_url'],
                "title": title,
                "type": "report"
            }
    }
