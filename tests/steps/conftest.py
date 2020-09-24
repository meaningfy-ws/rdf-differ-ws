#!/usr/bin/python3

# conftest.py
# Date:  07/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com
import pytest


@pytest.fixture(scope="session")
def scenario_context():
    return {}
