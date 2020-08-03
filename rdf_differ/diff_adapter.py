"""
diff_adapter.py
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


class AbstractDiffAdapter(ABC):
    """
        An abstract class that return information about the available diffs.
    """

    @abstractmethod
    def delete_dataset(self, dataset_name: str) -> tuple:
        """
            Delete the dataset from the Fuseki store
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: text and status of the deleted dataset
        :rtype: text, int
        """

    @abstractmethod
    def list_datasets(self) -> tuple:
        """
            Get the list of the dataset names from the Fuseki store.
        :return: the list of the dataset names
        :rtype: list, int
        """

    @abstractmethod
    def diff_description(self, dataset_name: str) -> tuple:
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
        :rtype: dict, int
        """

    @abstractmethod
    def count_deleted_triples(self, dataset_name: str) -> tuple:
        """
            Get number of inserted triples in the given dataset
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: inserted triples count
        :rtype: int, int
        """

    @abstractmethod
    def count_inserted_triples(self, dataset_name: str) -> tuple:
        """
            Get number of inserted triples in the given dataset
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: inserted triples count
        :rtype: int, int
        """


SKOS_HISTORY_PREFIXES = """
prefix skos-history: <http://purl.org/skos-history/>
prefix dc: <http://purl.org/dc/elements/1.1/>
prefix dcterms: <http://purl.org/dc/terms/>
prefix dsv: <http://purl.org/iso25964/DataSet/Versioning#>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix sd: <http://www.w3.org/ns/sparql-service-description#>
prefix skos: <http://www.w3.org/2004/02/skos/core#>
prefix void: <http://rdfs.org/ns/void#>
prefix xhv: <http://www.w3.org/1999/xhtml/vocab#>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
"""

QUERY_DATASET_DESCRIPTION1 = """
SELECT ?datasetURI ?versionDescriptionGraph
WHERE {
  GRAPH ?g {
    ?s skos-history:isVersionHistoryOf ?datasetURI . 
  }  
} 
"""

QUERY_DATASET_DESCRIPTION = """
SELECT ?versionHistoryGraph (?identifier AS ?datasetVersion) (str(?vhrDate) AS ?date) ?currentVersionGraph ?schemeURI \
?versionNamedGraph ?versionId
WHERE {
  # parameters
  VALUES ( ?versionHistoryGraph ) {
    ( undef )
  }
  GRAPH ?versionHistoryGraph {
    ?vhr dsv:hasVersionHistorySet ?vhs .
    OPTIONAL {
        ?vhr dc:date ?vhrDate .
    }
    OPTIONAL {
        ?vhr dc:identifier ?identifier
    }
    OPTIONAL {
        ?vhr skos-history:usingNamedGraph/sd:name ?versionNamedGraph .
        bind ( replace(str(?versionNamedGraph), "(.*[\\\\/#])(.*)", "$2") as ?versionId) 
    }
    OPTIONAL {
      ?vhs dsv:currentVersionRecord ?currentRecord .
      ?currentRecord skos-history:usingNamedGraph/sd:name ?currentVersionGraph .
      FILTER ( ?vhr = ?currentRecord )
    }
    OPTIONAL {
        ?versionHistoryGraph skos-history:isVersionHistoryOf ?schemeURI .
    }
  }
}
ORDER BY ?date ?datasetVersion
"""

QUERY_INSERTIONS_COUNT = """
SELECT ?insertionsGraph ?triplesInInsertionGraph ?versionGraph
WHERE {
  graph ?versionGraph {
    ?insertionsGraph a skos-history:SchemeDeltaInsertions .
  }
  {
    select ?insertionsGraph (count(*) as ?triplesInInsertionGraph)    
    {
      graph ?insertionsGraph {?s ?p ?o}
    } group by ?insertionsGraph 
  }
}
"""

QUERY_DELETIONS_COUNT = """
SELECT ?deletionsGraph ?triplesInDeletionGraph ?versionGraph
WHERE {
  graph ?versionGraph {
    ?deletionsGraph a skos-history:SchemeDeltaDeletions .
  }
  {
    select ?deletionsGraph (count(*) as ?triplesInDeletionGraph)    
    {
      graph ?deletionsGraph {?s ?p ?o}
    } group by ?deletionsGraph 
  }
}
"""


class FusekiException(Exception):
    """
        An exception when Fuseki server interaction has failed.
    """


class FusekiDiffAdapter(AbstractDiffAdapter):

    def __init__(self, triplestore_service_url: str):
        self.triplestore_service_url = triplestore_service_url

    def count_inserted_triples(self, dataset_name: str) -> tuple:
        """
            Get number of inserted triples in the given dataset
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: inserted triples count
        :rtype: int, int
        """
        query_result, status = self.execute_query(dataset_name=dataset_name,
                                                  sparql_query=SKOS_HISTORY_PREFIXES + QUERY_INSERTIONS_COUNT)
        return self._extract_insertion_count(query_result), status

    def count_deleted_triples(self, dataset_name: str) -> tuple:
        """
            Get number of deleted triples in the given dataset.
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: deleted triples count
        :rtype: int, int
        """
        query_result, status = self.execute_query(dataset_name=dataset_name,
                                                  sparql_query=SKOS_HISTORY_PREFIXES + QUERY_DELETIONS_COUNT)
        return self._extract_deletion_count(query_result), status

    def diff_description(self, dataset_name: str) -> tuple:
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
        :rtype: dict, int
        """
        query_result, status = self.execute_query(dataset_name=dataset_name,
                                                  sparql_query=SKOS_HISTORY_PREFIXES + QUERY_DATASET_DESCRIPTION)

        return self._extract_dataset_description(response=query_result, dataset_id=dataset_name,
                                                 query_url=self.make_sparql_endpoint(dataset_name)), status

    def delete_dataset(self, dataset_name: str) -> tuple:
        """
            Delete the dataset from the Fuseki store
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: text and status of the deleted dataset
        :rtype: text, int
        """
        response = requests.delete(urljoin(self.triplestore_service_url, f"/$/datasets/{dataset_name}"),
                                   auth=HTTPBasicAuth('admin', 'admin'))

        return response.text, response.status_code

    def list_datasets(self) -> tuple:
        """
            Get the list of the dataset names from the Fuseki store.
        :return: the list of the dataset names
        :rtype: list, int
        """
        response = requests.get(urljoin(self.triplestore_service_url, "/$/datasets"),
                                auth=HTTPBasicAuth('admin', 'admin'))

        if response.status_code != 200:
            return {
                       'error': f"Fuseki server request ({response.url}) got response {response.status_code}"
                   }, response.status_code

        return self._select_dataset_names_from_fuseki_response(response=response), response.status_code

    def execute_query(self, dataset_name: str, sparql_query: str) -> tuple:
        """
            Helper method to execute queries to the Fuseki store using the SPARQLWrapper.
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :param sparql_query: query to be executed
        :return: SPARQLWrapper query response
        :rtype: [json, list, text], int
        """
        endpoint = SPARQLWrapper(self.make_sparql_endpoint(dataset_name=dataset_name))

        endpoint.setQuery(sparql_query)
        endpoint.setReturnFormat(JSON)
        query = endpoint.query()

        return query.convert(), query.response.status

    def make_sparql_endpoint(self, dataset_name: str) -> str:
        """
            Helper method to create the url for querying.
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        :return: the query url
        """
        return urljoin(self.triplestore_service_url, dataset_name + "/sparql")

    @staticmethod
    def _select_dataset_names_from_fuseki_response(response) -> list:
        """
            Helper method for digging for the list of datasets.
        :param response: fuseki API response
        :return: list of the dataset names
        """
        result = loads(response.text)
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
        helper_current_version = [item['currentVersionGraph']['value'] for item in response['results']['bindings'] if
                                  'currentVersionGraph' in item and item['currentVersionGraph']['value']]

        if not response['results']['bindings']:
            return {}

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
