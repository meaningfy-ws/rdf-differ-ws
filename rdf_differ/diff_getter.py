"""
diff_getter.py
Date:  23/07/2020
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com 
"""
from json import loads
from abc import ABC, abstractmethod
from typing import List, Tuple
from urllib.parse import urljoin

import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from requests.auth import HTTPBasicAuth

from rdf_differ.config import SKOS_HISTORY_PREFIXES, QUERY_DATASET_DESCRIPTION, QUERY_INSERTIONS_COUNT, \
    QUERY_DELETIONS_COUNT


class AbstractDiffGetter(ABC):
    """
        An abstract class that return information about the available diffs.
    """

    @abstractmethod
    def list_datasets(self) -> List[str]:
        """
            Return a list of available dataset names
        :return:
        """

    @abstractmethod
    def diff_description(self, dataset_name: str) -> Tuple[str, str]:
        """
            Return the dataset description.
        :type dataset_name: the name of the desired dataset
        :return:
        """

    @abstractmethod
    def count_deleted_triples(self, dataset_name: str) -> int:
        """
            Return the number of triples that have been deleted in the new version of the dataset.
        :type dataset_name: the name of the desired dataset
        :return:
        """

    @abstractmethod
    def count_inserted_triples(self, dataset_name: str) -> int:
        """
            Return the number of triples that have been inserted in the new version of the dataset.
        :type dataset_name: the name of the desired dataset
        :return:
        """


class FusekiException(Exception):
    """
        An exception when Fuseki server interaction has failed.
    """


class FusekiDiffGetter(AbstractDiffGetter):

    def __init__(self, triplestore_service_url: str):
        self.triplestore_service_url = triplestore_service_url

    def count_inserted_triples(self, dataset_name: str) -> int:
        query_result = self.execute_query(dataset_name=dataset_name,
                                          sparql_query=SKOS_HISTORY_PREFIXES + QUERY_INSERTIONS_COUNT)
        return int(self._extract_insertion_count(query_result))

    def count_deleted_triples(self, dataset_name: str) -> int:
        query_result = self.execute_query(dataset_name=dataset_name,
                                          sparql_query=SKOS_HISTORY_PREFIXES + QUERY_DELETIONS_COUNT)
        return int(self._extract_deletion_count(query_result))

    def diff_description(self, dataset_name: str) -> dict:
        """
            Provide a generic description
        :param dataset_name:
        :return:
            * datasetURI = dataset/scheme URI,
            * version history graph = the graph that stores the structure of the calculated diffs
            * current version graph = the graph that corresponds to the latest version of the dataset,
            * datasetVersions = list of loaded dataset versions as declared by the datasets themselves,
            * versionIds = list of versionIds as provided in the configurations file
            * versionNamedGraphs = named graphs where the versions of datasets are loaded
        """
        query_result = self.execute_query(dataset_name=dataset_name,
                                          sparql_query=SKOS_HISTORY_PREFIXES + QUERY_DATASET_DESCRIPTION)

        return self._extract_dataset_description(response=query_result)

    def execute_query(self, dataset_name: str, sparql_query: str) -> dict:
        endpoint = SPARQLWrapper(self.make_sparql_endpoint(dataset_name=dataset_name))

        endpoint.setQuery(sparql_query)
        endpoint.setReturnFormat(JSON)
        return endpoint.query().convert()

    def list_datasets(self) -> List[str]:
        response = requests.get(urljoin(self.triplestore_service_url, "/$/datasets"),
                                auth=HTTPBasicAuth('admin', 'admin'))

        if response.status_code != 200:
            raise FusekiException(f"Fuseki server request ({response.url}) got response {response.status_code}")

        return self._select_dataset_names_from_fuseki_response(response=response)

    def make_sparql_endpoint(self, dataset_name: str):
        return urljoin(self.triplestore_service_url, dataset_name + "/sparql")

    @staticmethod
    def _select_dataset_names_from_fuseki_response(response):
        """
            digging for the list of datasets
        :param response: fuseki API response
        :return:
        """
        result = loads(response.text)
        return [d_item['ds.name'] for d_item in result['datasets']]

    @staticmethod
    def _extract_dataset_description(response: dict) -> dict:
        """
            digging for:
            * datasetURI = dataset/scheme URI,
            * version history graph = the graph that stores the structure of the calculated diffs
            * current version graph = the graph that corresponds to the latest version of the dataset,
            * datasetVersions = list of loaded dataset versions as declared by the datasets themselves,
            * versionIds = list of versionIds as provided in the configurations file
            * versionNamedGraphs = named graphs where the versions of datasets are loaded
        :param response: sparql query result
        :return:
        """
        helper_current_version = [item['currentVersionGraph']['value'] for item in response['results']['bindings'] if
                                  'currentVersionGraph' in item and item['currentVersionGraph']['value']]

        return {
            'datasetURI': response['results']['bindings'][0]['schemeURI']['value'],
            'versionHistoryGraph': response['results']['bindings'][0]['versionHistoryGraph']['value'],
            'currentVersionGraph': helper_current_version[0] if helper_current_version else None,
            'datasetVersions': [item['datasetVersion']['value'] for item in response['results']['bindings']],
            'versionIds': [item['versionId']['value'] for item in response['results']['bindings']],
            'versionNamedGraphs': [item['versionNamedGraph']['value'] for item in response['results']['bindings']]
        }

    @staticmethod
    def _extract_insertion_count(response: dict) -> str:
        """/home/mihai/code/meaningfy/rdf-differ/rdf_differ/diff_getter.py
            digging for the single expected datasetURI
        :param response: sparql query result
        :return:
        """
        return response['results']['bindings'][0]['triplesInInsertionGraph']['value']

    @staticmethod
    def _extract_deletion_count(response: dict) -> str:
        """
            digging for the single expected datasetURI
        :param response: sparql query result
        :return:
        """
        return response['results']['bindings'][0]['triplesInDeletionGraph']['value']
