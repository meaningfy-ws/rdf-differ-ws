"""
skos_history_wrapper.py
Date: 06/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
import os
from urllib.parse import urljoin

from rdf_differ import defaults
from rdf_differ.defaults import PUT_URI_BASE, QUERY_URI_BASE


class SKOSHistoryRunner:
    """

    """

    def __init__(self):
        """

        """

        self.bash = """
            # !/bin/bash
    
            DATASET = {dataset}
            SCHEMEURI = {scheme_uri}
    
            VERSIONS = {versions}
            BASEDIR = {basedir}
            FILENAME = {filename}
    
            PUT_URI = {put_uri}
            UPDATE_URI = {update_uri}
            QUERY_URI = {query_uri}
    
            INPUT_MIME_TYPE = {input_type}
        """
        self.dataset = None
        self.scheme_uri = None
        self.versions = None

        self.basedir = None
        self.filename = None
        self.endpoint = None

        self.input_type = None

        self.read_envs()

    def read_envs(self):
        """
        Method for reading properties for the skos-history bash config file.
        :return:
        """
        self.basedir = os.environ.get('BASEDIR', defaults.BASEDIR)
        self.filename = os.environ.get('FILENAME', defaults.FILENAME)
        self.endpoint = os.environ['ENDPOINT']

    @property
    def put_uri(self) -> str:
        """
        Build the PUT URI
        :return: str
            PUT URI
        """
        return urljoin(self.endpoint, '/'.join([self.dataset, PUT_URI_BASE]))

    @property
    def update_uri(self) -> str:
        """
        Build the update URI
        :return: str
            UPDATE URI
        """
        return urljoin(self.endpoint, self.dataset)

    @property
    def query_uri(self) -> str:
        """
        Build the query URI
        :return: str
            query URI
        """
        return urljoin(self.endpoint, '/'.join([self.dataset, QUERY_URI_BASE]))
