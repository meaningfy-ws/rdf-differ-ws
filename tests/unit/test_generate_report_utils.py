#!/usr/bin/python3

# test_generate_report_utils.py
# Date:  24/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com
from utils.generate_report_utils import generate_config_content


def test_generate_config_content():
    endpoint = 'http://test.endpoint'

    config_content = generate_config_content(endpoint)

    assert config_content['template'] == 'main.html'
    assert config_content['conf']['default_endpoint'] == 'http://test.endpoint'
    assert config_content['conf']['title'] == 'Dataset Diff Report'
    assert config_content['conf']['type'] == 'report'
