"""
skos_history_wrapper.py
Date: 06/07/2020
Author: Mihai Coșleț
Email: coslet.mihai@gmail.com
"""
import os
from urllib.parse import urljoin
from rdflib.util import guess_format

from rdf_differ import defaults
from rdf_differ.defaults import PUT_URI_BASE, QUERY_URI_BASE
from rdf_differ.utils import INPUT_MIME_TYPES


class SKOSHistoryRunner:
    """

    """

    def __init__(self, dataset: str, scheme_uri: str, versions: list):
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
        self.dataset = dataset
        self.scheme_uri = scheme_uri
        self.versions = versions

        self.basedir = None
        self.filename = None
        self.endpoint = None

        self._read_envs()

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

    @property
    def input_file_mime(self) -> str:
        file_format = guess_format(self.filename, INPUT_MIME_TYPES)
        # breakpoint()
        if file_format is None:
            raise Exception('File type not supported.')

        return file_format

    def generate(self):
        return self.bash.format(
            dataset=self.dataset,
            scheme_uri=self.scheme_uri,
            versions='({} {})'.format(*self.versions),
            basedir=self.basedir,
            filename=self.filename,
            put_uri=self.put_uri,
            update_uri=self.update_uri,
            query_uri=self.query_uri,
            input_type=self.input_file_mime
        )

    def _read_envs(self):
        """
        Method for reading properties for the skos-history bash config file.
        :return:
        """
        self.basedir = os.environ.get('BASEDIR', defaults.BASEDIR)
        self.filename = os.environ.get('FILENAME', defaults.FILENAME)
        self.endpoint = os.environ['ENDPOINT']
