#!/usr/bin/python3

# __init__.py
# Date:  07/08/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

__docformat__ = "restructuredtext en"

# The format of the __version__ line is matched by a regex in setup.py and /docs/conf.py
__version__ = "0.2.0"
__date__ = "2023-10-20"

import logging

from eds4jinja2.adapters.file_ds import FileDataSource
from eds4jinja2.adapters.local_sparql_ds import RDFFileDataSource
from eds4jinja2.adapters.namespace_handler import NamespaceInventory
from eds4jinja2.adapters.remote_sparql_ds import RemoteSPARQLEndpointDataSource
from eds4jinja2.adapters.tabular_utils import add_relative_figures, replace_strings_in_tabular
from eds4jinja2.builders.jinja_builder import build_eds_environment, inject_environment_globals

# Making usage of this library more convenient
__all__ = ["build_eds_environment",
           "inject_environment_globals",
           "FileDataSource",
           "RemoteSPARQLEndpointDataSource",
           "RDFFileDataSource",
           "add_relative_figures",
           "replace_strings_in_tabular",
           "NamespaceInventory"
           ]

# hard coding the log level and format
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
