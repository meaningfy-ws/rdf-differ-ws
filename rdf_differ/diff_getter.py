"""
diff_getter.py
Date:  23/07/2020
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com 
"""
import json
import urllib
from typing import List, Tuple
from abc import ABC, abstractmethod

import requests
from SPARQLWrapper import SPARQLWrapper, JSON
from requests.auth import HTTPBasicAuth


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
    def dataset_description(self, dataset_name: str) -> Tuple[str, str]:
        """
            Return the dataset description.
        :type dataset_name: the name of the desired dataset
        :return:
        """

    @abstractmethod
    def loaded_versions(self, dataset_name: str) -> List[str]:
        """
            Return the version ids that have been loaded.

        :type dataset_name: the name of the desired dataset
        :return:
        """

    @abstractmethod
    def count_deleted_triples(self, dataset_name: str, old_version_id: str, new_version_id: str) -> int:
        """
            Return the number of triples that have been deleted in the new version of the dataset.
        :type dataset_name: the name of the desired dataset
        :param old_version_id:
        :param new_version_id:
        :return:
        """

    @abstractmethod
    def count_inserted_triples(self, dataset_name: str) -> int:
        """
            Return the number of triples that have been inserted in the new version of the dataset.
        :type dataset_name: the name of the desired dataset
        :return:
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
SELECT ?versionHistoryGraph (?vhr AS ?versionHistoryRecord) (?identifier AS ?datasetVersion) (str(?vhrDate) AS ?date) ?current ?schemeURI ?versionNamedGraph ?versionId
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
        bind ( replace(str(?versionNamedGraph), "(.*[\\/#])(.*)", "$2") as ?versionId) 
    }
    OPTIONAL {
      ?vhs dsv:currentVersionRecord ?current
      FILTER ( ?vhr = ?current )
    }
    OPTIONAL {
    	?versionHistoryGraph skos-history:isVersionHistoryOf ?schemeURI .
    }
  }
}
ORDER BY ?date
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


class FusekiDiffGetter(AbstractDiffGetter):

    def count_inserted_triples(self, dataset_name: str) -> int:
        query_result = self.execute_query(dataset_name=dataset_name,
                                          sparql_query=SKOS_HISTORY_PREFIXES + QUERY_INSERTIONS_COUNT)
        return int(self._extract_insertion_count(query_result))

    def count_deleted_triples(self, dataset_name: str) -> int:
        query_result = self.execute_query(dataset_name=dataset_name,
                                          sparql_query=SKOS_HISTORY_PREFIXES + QUERY_DELETIONS_COUNT)
        return int(self._extract_deletion_count(query_result))

    def loaded_versions(self, dataset_name: str) -> List[str]:
        pass

    def dataset_description(self, dataset_name: str) -> str:
        query_result = self.execute_query(dataset_name=dataset_name,
                                          sparql_query=SKOS_HISTORY_PREFIXES + QUERY_DATASET_DESCRIPTION)

        return self._extract_dataset_description(response=query_result)

    def execute_query(self, dataset_name: str, sparql_query: str) -> dict:
        endpoint = SPARQLWrapper(self.make_sparql_endpoint(dataset_name=dataset_name))

        endpoint.setQuery(sparql_query)
        endpoint.setReturnFormat(JSON)
        return endpoint.query().convert()

    def list_datasets(self) -> List[str]:
        response = requests.get(urllib.parse.urljoin(self.triplestore_service_url, "/$/datasets"),
                                auth=HTTPBasicAuth('admin', 'admin'))

        if response.status_code != 200:
            raise Exception(f"Fuseki server request ({response.url}) got response {response.status_code}")

        return self._select_dataset_names_from_fuseki_response(response=response)

    def __init__(self, triplestore_service_url: str):
        self.triplestore_service_url = triplestore_service_url

    def make_sparql_endpoint(self, dataset_name: str):
        return urllib.parse.urljoin(self.triplestore_service_url, dataset_name + "/sparql")

    def _select_dataset_names_from_fuseki_response(self, response):
        """
            digging for the list of datasets
        :param response: fuseki API response
        :return:
        """
        result = json.loads(response.text)
        return [d_item['ds.name'] for d_item in result['datasets']]

    def _extract_dataset_description(self, response: dict) -> str:
        """
            digging for the single expected datasetURI
        :param response: sparql query result
        :return:
        """
        return response['results']['bindings'][0]['datasetURI']['value']

    def _extract_insertion_count(self, response: dict) -> str:
        """
            digging for the single expected datasetURI
        :param response: sparql query result
        :return:
        """
        return response['results']['bindings'][0]['triplesInInsertionGraph']['value']

    def _extract_deletion_count(self, response: dict) -> str:
        """
            digging for the single expected datasetURI
        :param response: sparql query result
        :return:
        """
        return response['results']['bindings'][0]['triplesInDeletionGraph']['value']
