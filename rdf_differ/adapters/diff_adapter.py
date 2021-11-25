#!/usr/bin/python3

# diff_adapter.py
# Date: 23/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

"""
Module for triple store adapters.

Currently implemented triple store adapters:
FusekiDiffAdapter - for the Fuseki triple store (more info here: https://jena.apache.org/documentation/fuseki2/)
"""

from abc import ABC, abstractmethod
from json import loads
from pathlib import Path
from urllib.parse import urljoin

from requests.auth import HTTPBasicAuth

from rdf_differ import config
from rdf_differ.adapters import SKOS_HISTORY_PREFIXES, QUERY_DATASET_DESCRIPTION, QUERY_INSERTIONS_COUNT, \
    QUERY_DELETIONS_COUNT
from rdf_differ.adapters.skos_history_wrapper import SKOSHistoryRunner


class AbstractDiffAdapter(ABC):
    """
        An abstract class that return information about the available diffs.
    """

    @abstractmethod
    def create_dataset(self, dataset_name: str) -> bool:
        """
            Create the dataset for the __ store
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: true if dataset was created
        """

    @abstractmethod
    def delete_dataset(self, dataset_name: str) -> bool:
        """
            Delete the dataset from the __ store
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: true if dataset was deleted
        """

    @abstractmethod
    def list_datasets(self) -> list:
        """
            Get the list of the dataset names from the __ store.
        :return: the list of the dataset names
        """

    @abstractmethod
    def create_diff(self, dataset: str, dataset_uri: str, temp_dir: Path,
                    old_version_id: str, new_version_id: str,
                    old_version_file: Path, new_version_file: Path) -> bool:
        """
            Create a dataset diff using the data from the provided files.
        :param dataset: the name used for the dataset
        :param dataset_uri: the concept scheme or dataset URI
        :param temp_dir: location for folder generation
        :param old_version_file: the location of the file to be uploaded
        :param new_version_file: the location of the file to be uploaded
        :param old_version_id: name used for diff upload
        :param new_version_id: name used for diff upload
        :return: true if diff was created
        """

    @abstractmethod
    def dataset_description(self, dataset_name: str) -> dict:
        """
            Provide a generic description of the dataset.
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return:
            diff description:
            * datasetURI = dataset/scheme URI,
            * version history graph = the graph that stores the structure of the calculated diffs
            * current version graph = the graph that corresponds to the latest version of the dataset,
            * datasetVersions = list of loaded dataset versions as declared by the datasets themselves,
            * versionIds = list of versionIds as provided in the configurations file
            * versionNamedGraphs = named graphs where the versions of datasets are loaded
        """

    @abstractmethod
    def count_deleted_triples(self, dataset_name: str) -> int:
        """
            Get number of inserted triples in the given dataset
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: inserted triples count
        """

    @abstractmethod
    def count_inserted_triples(self, dataset_name: str) -> int:
        """
            Get number of inserted triples in the given dataset
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: inserted triples count
        """


class FusekiException(Exception):
    """
        An exception when Fuseki server interaction has failed.
    """


class FusekiDiffAdapter(AbstractDiffAdapter):

    def __init__(self, triplestore_service_url: str, http_client, sparql_client):
        self.triplestore_service_url = triplestore_service_url
        self.sparql_client = sparql_client
        self.http_client = http_client

    def count_inserted_triples(self, dataset_name: str) -> int:
        """
            Get number of inserted triples in the given dataset
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: inserted triples count
        """
        query_result = self.execute_query(dataset_name=dataset_name,
                                          sparql_query=SKOS_HISTORY_PREFIXES + QUERY_INSERTIONS_COUNT)
        return self._extract_insertion_count(query_result)

    def count_deleted_triples(self, dataset_name: str) -> int:
        """
            Get number of deleted triples in the given dataset.
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: deleted triples count
        """
        query_result = self.execute_query(dataset_name=dataset_name,
                                          sparql_query=SKOS_HISTORY_PREFIXES + QUERY_DELETIONS_COUNT)
        return self._extract_deletion_count(query_result)

    def create_diff(self, dataset: str, dataset_uri: str, temp_dir: Path,
                    old_version_id: str, new_version_id: str,
                    old_version_file: Path, new_version_file: Path) -> bool:
        """
            Create a dataset diff using the data from the provided files.
        :param dataset: the name used for the dataset
        :param dataset_uri: the concept scheme or dataset URI
        :param temp_dir: location for folder generation
        :param old_version_file: the location of the file to be uploaded
        :param new_version_file: the location of the file to be uploaded
        :param old_version_id: name used for diff upload
        :param new_version_id: name used for diff upload
        :return: true if diff created successfully
        """
        SKOSHistoryRunner(dataset=dataset,
                          basedir=str(temp_dir / 'basedir'),
                          scheme_uri=dataset_uri,
                          old_version_id=old_version_id,
                          new_version_id=new_version_id,
                          old_version_file=str(old_version_file),
                          new_version_file=str(new_version_file)).run()

        return True

    def create_dataset(self, dataset_name: str) -> bool:
        """
            Create the dataset for the Fuseki store
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: true if dataset was created
        """
        if not dataset_name:
            raise ValueError('Dataset name cannot be empty.')

        data = {
            'dbType': 'tdb',  # assuming that all databases are created persistent across restart
            'dbName': dataset_name
        }

        response = self.http_client.post(urljoin(self.triplestore_service_url, f"/$/datasets"),
                                         auth=HTTPBasicAuth(config.RDF_DIFFER_FUSEKI_USERNAME,
                                                            config.RDF_DIFFER_FUSEKI_PASSWORD),
                                         data=data)

        if response.status_code == 409:
            # TODO: change exception if better one found
            raise FusekiException('A dataset with this name already exists.')

        return True

    def delete_dataset(self, dataset_name: str) -> bool:
        """
            Delete the dataset from the Fuseki store
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: true if dataset was deleted
        """
        response = self.http_client.delete(urljoin(self.triplestore_service_url, f"/$/datasets/{dataset_name}"),
                                           auth=HTTPBasicAuth(config.RDF_DIFFER_FUSEKI_USERNAME,
                                                              config.RDF_DIFFER_FUSEKI_PASSWORD))

        if response.status_code == 404:
            # TODO: change exception if better one found
            raise FusekiException('The dataset doesn\'t exist.')

        return True

    def dataset_description(self, dataset_name: str) -> dict:
        """
            Provide a generic description of the dataset.
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return:
            diff description:
            * datasetURI = dataset/scheme URI,
            * version history graph = the graph that stores the structure of the calculated diffs
            * current version graph = the graph that corresponds to the latest version of the dataset,
            * datasetVersions = list of loaded dataset versions as declared by the datasets themselves,
            * versionIds = list of versionIds as provided in the configurations file
            * versionNamedGraphs = named graphs where the versions of datasets are loaded
        """
        query_result = self.execute_query(dataset_name=dataset_name,
                                          sparql_query=SKOS_HISTORY_PREFIXES + QUERY_DATASET_DESCRIPTION)

        return self._extract_dataset_description(response=query_result, dataset_id=dataset_name,
                                                 query_url=self.make_sparql_endpoint(dataset_name))

    def list_datasets(self) -> list:
        """
            Get the list of the dataset names from the Fuseki store.
        :return: the list of the dataset names
        :rtype: list
        """
        response = self.http_client.get(urljoin(self.triplestore_service_url, "/$/datasets"),
                                        auth=HTTPBasicAuth(config.RDF_DIFFER_FUSEKI_USERNAME,
                                                           config.RDF_DIFFER_FUSEKI_PASSWORD))

        # investigate what codes can fuseki return for this endpoint
        if response.status_code != 200:
            raise FusekiException(f"Fuseki server request ({response.url}) got response {response.status_code}")

        return self._select_dataset_names_from_fuseki_response(response_text=response.text)

    def execute_query(self, dataset_name: str, sparql_query: str) -> dict:
        """
            Helper method to execute queries to the Fuseki store using the SPARQLWrapper.
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :param sparql_query: query to be executed
        :return: SPARQLWrapper query response
        """
        return self.sparql_client.execute(endpoint_url=self.make_sparql_endpoint(dataset_name),
                                          query_text=sparql_query)

    def make_sparql_endpoint(self, dataset_name: str) -> str:
        """
            Helper method to create the url for querying.
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: the query url
        """
        return urljoin(self.triplestore_service_url, dataset_name + "/sparql")

    @staticmethod
    def _select_dataset_names_from_fuseki_response(response_text) -> list:
        """
            Helper method for digging for the list of datasets.
        :param response_text:
        :return: list of the dataset names
        """
        result = loads(response_text)
        return [d_item['ds.name'] for d_item in result['datasets']]

    @staticmethod
    def _extract_dataset_description(response: dict, dataset_id: str, query_url: str) -> dict:
        """
            Helper method digging for:

        :param response: sparql query result
        :return: dataset description dict
            * dataset_id = The dataset identifier. This should be short alphanumeric string uniquely
                identifying the dataset.
            * dataset_description = The dataset description. This is a free text description fo the dataset.
            * dataset_uri = The dataset URI. For SKOS datasets this is usually the ConceptSchema URI.
            * diff_date = The date of the calculated diff.
            * old_version_id = Identifier for the older version of the dataset.
            * new_version_id = Identifier for the newer version of the dataset.
            * query_url = The url queried that returned this dataset description.

            * version_history_graph = the graph that stores the structure of the calculated diffs
            * current_version_graph = the graph that corresponds to the latest version of the dataset,
            * dataset_versions = list of loaded dataset versions as declared by the datasets themselves,
            * version_named_graphs = named graphs where the versions of datasets are loaded
        """
        if not response['results']['bindings']:
            return {}

        helper_current_version = [item['currentVersionGraph']['value'] for item in response['results']['bindings'] if
                                  'currentVersionGraph' in item and item['currentVersionGraph']['value']]

        return {
            'dataset_id': dataset_id,
            'dataset_description': None,
            'dataset_uri': response['results']['bindings'][0]['schemeURI']['value'],
            'diff_date': None,
            'old_version_id': response['results']['bindings'][0]['versionId']['value'],
            'new_version_id': response['results']['bindings'][1]['versionId']['value'],
            'query_url': query_url,

            'version_history_graph': response['results']['bindings'][0]['versionHistoryGraph']['value'],
            'current_version_graph': helper_current_version[0] if helper_current_version else None,
            'dataset_versions': [item['datasetVersion']['value'] for item in response['results']['bindings']],
            'version_named_graphs': [item['versionNamedGraph']['value'] for item in response['results']['bindings']],
        }

    @staticmethod
    def _extract_insertion_count(response: dict) -> int:
        """
            Helper method for digging for the insertion count.
        :param response: sparql query result
        :return: insertion count
        """
        return int(response['results']['bindings'][0]['triplesInInsertionGraph']['value'])

    @staticmethod
    def _extract_deletion_count(response: dict) -> int:
        """
            Helper method for digging for the deletion count.
        :param response: sparql query result
        :return: deletion count
        """
        return int(response['results']['bindings'][0]['triplesInDeletionGraph']['value'])
