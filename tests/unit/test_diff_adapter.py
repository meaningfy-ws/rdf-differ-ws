"""
test_diff_adapter.py
Date:  23/07/2020
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com 
"""

import pytest

from rdf_differ.diff_adapter import FusekiException
from tests import DUMMY_DATASET_DIFF_DESCRIPTION
from tests.conftest import helper_fuseki_service


def test_fuseki_diff_adapter_sparql_endpoint():
    fuseki_service = helper_fuseki_service(triplestore_service_url='http://localhost:3030')
    assert fuseki_service.make_sparql_endpoint(dataset_name="subdiv") == "http://localhost:3030/subdiv/sparql"
    assert fuseki_service.make_sparql_endpoint(dataset_name="/foe") == "http://localhost:3030/foe/sparql"


def test_fuseki_diff_adapter_list_datasets(fake_requests):
    fake_requests.text = """{ 
          "datasets" : [ 
              { 
                "ds.name" : "/subdiv" ,
                "ds.state" : true ,
                "ds.services" : [ 
                    { 
                      "srv.type" : "gsp-rw" ,
                      "srv.description" : "Graph Store Protocol" ,
                      "srv.endpoints" : [ "data" ]
                    } ,
                    { 
                      "srv.type" : "query" ,
                      "srv.description" : "SPARQL Query" ,
                      "srv.endpoints" : [ 
                          "" ,
                          "sparql" ,
                          "query"
                        ]
                    } ,
                    { 
                      "srv.type" : "gsp-r" ,
                      "srv.description" : "Graph Store Protocol (Read)" ,
                      "srv.endpoints" : [ "get" ]
                    } ,
                    { 
                      "srv.type" : "update" ,
                      "srv.description" : "SPARQL Update" ,
                      "srv.endpoints" : [ 
                          "update" ,
                          ""
                        ]
                    } ,
                    { 
                      "srv.type" : "upload" ,
                      "srv.description" : "File Upload" ,
                      "srv.endpoints" : [ "upload" ]
                    }
                  ]
              } ,
              { 
                "ds.name" : "/qwe" ,
                "ds.state" : true ,
                "ds.services" : [ 
                    { 
                      "srv.type" : "gsp-rw" ,
                      "srv.description" : "Graph Store Protocol" ,
                      "srv.endpoints" : [ "data" ]
                    } ,
                    { 
                      "srv.type" : "query" ,
                      "srv.description" : "SPARQL Query" ,
                      "srv.endpoints" : [ 
                          "query" ,
                          "sparql" ,
                          ""
                        ]
                    } ,
                    { 
                      "srv.type" : "gsp-r" ,
                      "srv.description" : "Graph Store Protocol (Read)" ,
                      "srv.endpoints" : [ "get" ]
                    } ,
                    { 
                      "srv.type" : "update" ,
                      "srv.description" : "SPARQL Update" ,
                      "srv.endpoints" : [ 
                          "" ,
                          "update"
                        ]
                    } ,
                    { 
                      "srv.type" : "upload" ,
                      "srv.description" : "File Upload" ,
                      "srv.endpoints" : [ "upload" ]
                    }
                  ]
              } ,
              { 
                "ds.name" : "/rty" ,
                "ds.state" : true ,
                "ds.services" : [ 
                    { 
                      "srv.type" : "gsp-rw" ,
                      "srv.description" : "Graph Store Protocol" ,
                      "srv.endpoints" : [ "data" ]
                    } ,
                    { 
                      "srv.type" : "query" ,
                      "srv.description" : "SPARQL Query" ,
                      "srv.endpoints" : [ 
                          "query" ,
                          "" ,
                          "sparql"
                        ]
                    } ,
                    { 
                      "srv.type" : "gsp-r" ,
                      "srv.description" : "Graph Store Protocol (Read)" ,
                      "srv.endpoints" : [ "get" ]
                    } ,
                    { 
                      "srv.type" : "update" ,
                      "srv.description" : "SPARQL Update" ,
                      "srv.endpoints" : [ 
                          "" ,
                          "update"
                        ]
                    } ,
                    { 
                      "srv.type" : "upload" ,
                      "srv.description" : "File Upload" ,
                      "srv.endpoints" : [ "upload" ]
                    }
                  ]
              }
            ]
        }
        """
    fake_requests.status_code = 200

    fuseki_service = helper_fuseki_service(http_requests=fake_requests)
    response_text, _ = fuseki_service.list_datasets()

    assert len(response_text) == 3
    assert '/subdiv' in response_text


def test_fuseki_diff_adapter_list_datasets_failing(fake_requests):
    fake_requests.url, fake_requests.status_code = 'http://some.url', 400
    fuseki_service = helper_fuseki_service(triplestore_service_url='http://some.url', http_requests=fake_requests)

    with pytest.raises(FusekiException) as exception:
        _ = fuseki_service.list_datasets()

    assert 'Fuseki server request (http://some.url/$/datasets) got response 400' in str(exception)


def test_fuseki_diff_adapter_dataset_description(fake_sparql_runner):
    fake_sparql_runner.return_value = DUMMY_DATASET_DIFF_DESCRIPTION

    fuseki_service = helper_fuseki_service(triplestore_service_url='http://localhost:3030',
                                           sparql_requests=fake_sparql_runner)
    response = fuseki_service.diff_description(dataset_name='/subdiv')

    assert response['dataset_id'] == '/subdiv'
    assert response['dataset_description'] is None
    assert response['dataset_uri'] == "http://publications.europa.eu/resource/authority/subdivision"
    assert response['diff_date'] is None
    assert "v1" in response['old_version_id']
    assert "v2" in response['new_version_id']
    assert response['query_url'] == 'http://localhost:3030/subdiv/sparql'

    assert response['version_history_graph'] == "http://publications.europa.eu/resource/authority/subdivision/version"
    assert response['current_version_graph'] == \
           "http://publications.europa.eu/resource/authority/subdivision/version/v2"
    assert "20171213-0" in response['dataset_versions'] and "20190220-0" in response['dataset_versions']
    assert "http://publications.europa.eu/resource/authority/subdivision/version/v1" in response['version_named_graphs']
    assert "http://publications.europa.eu/resource/authority/subdivision/version/v2" in response['version_named_graphs']


def test_fuseki_diff_adapter_dataset_description_empty(fake_sparql_runner):
    fake_sparql_runner.return_value = {
        "head": {
            "vars": ["versionHistoryGraph", "datasetVersion", "date", "currentVersionGraph", "schemeURI",
                     "versionNamedGraph", "versionId"]
        },
        "results": {
            "bindings": []
        }
    }

    fuseki_service = helper_fuseki_service(triplestore_service_url='http://localhost:3030',
                                           sparql_requests=fake_sparql_runner)
    response = fuseki_service.diff_description(dataset_name='/subdiv')

    assert response == {}


def test_fuseki_diff_adapter_diff_description_failing1(fake_sparql_runner):
    fake_sparql_runner.return_value = {}

    fuseki_service = helper_fuseki_service(triplestore_service_url='http://localhost:3030',
                                           sparql_requests=fake_sparql_runner)

    with pytest.raises(KeyError):
        fuseki_service.diff_description(dataset_name='/subdiv')


def test_fuseki_diff_adapter_count_inserted_triples_success(fake_sparql_runner):
    fake_sparql_runner.return_value = {
        "head": {
            "vars": ["insertionsGraph", "triplesInInsertionGraph"]
        },
        "results": {
            "bindings": [
                {
                    "insertionsGraph": {"type": "uri",
                                        "value": "http://publications.europa.eu/resource/authority/subdivision/version/v1/delta/v2/insertions"},
                    "triplesInInsertionGraph": {"type": "literal",
                                                "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                                                "value": "387"}
                }
            ]
        }
    }

    fuseki_service = helper_fuseki_service(triplestore_service_url='http://localhost:3030',
                                           sparql_requests=fake_sparql_runner)
    count = fuseki_service.count_inserted_triples('subdiv')

    assert 387 == count


def test_fuseki_diff_adapter_count_inserted_triples_failing(fake_sparql_runner):
    fake_sparql_runner.return_value = {
        "head": {
            "vars": ["insertionsGraph", "triplesInInsertionGraph"]
        },
        "results": {
            "bindings": []
        }
    }

    fuseki_service = helper_fuseki_service(triplestore_service_url='http://localhost:3030',
                                           sparql_requests=fake_sparql_runner)

    with pytest.raises(IndexError):
        fuseki_service.count_inserted_triples('subdiv')


def test_fuseki_diff_adapter_count_deleted_triples_success(fake_sparql_runner):
    fake_sparql_runner.return_value = {
        "head": {
            "vars": ["deletionsGraph", "triplesInDeletionGraph", "versionGraph"]
        },
        "results": {
            "bindings": [
                {
                    "deletionsGraph": {"type": "uri",
                                       "value": "http://publications.europa.eu/resource/authority/subdivision/version/v1/delta/v2/deletions"},
                    "triplesInDeletionGraph": {"type": "literal",
                                               "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                                               "value": "3"},
                    "versionGraph": {"type": "uri",
                                     "value": "http://publications.europa.eu/resource/authority/subdivision/version"}
                }
            ]
        }
    }

    fuseki_service = helper_fuseki_service(triplestore_service_url='http://localhost:3030',
                                           sparql_requests=fake_sparql_runner)
    count = fuseki_service.count_deleted_triples('subdiv')

    assert count == 3


def test_fuseki_diff_adapter_delete_dataset_success(fake_requests):
    fake_requests.text, fake_requests.status_code = '', 200
    fuseki_service = helper_fuseki_service(triplestore_service_url='http://some.url', http_requests=fake_requests)

    response = fuseki_service.delete_dataset('dataset')

    assert response == ('', 200)


def test_fuseki_diff_adapter_delete_dataset_not_found(fake_requests):
    fake_requests.text, fake_requests.status_code = '', 404
    fuseki_service = helper_fuseki_service(triplestore_service_url='http://some.url', http_requests=fake_requests)

    response = fuseki_service.delete_dataset('dataset')

    assert response == ('', 404)


def test_fuseki_diff_adapter_create_dataset_success(fake_requests):
    fake_requests.text, fake_requests.status_code = '', 200

    fuseki_service = helper_fuseki_service(triplestore_service_url='http://some.url', http_requests=fake_requests)

    response = fuseki_service.create_dataset('dataset')

    assert response == ('', 200)


def test_fuseki_diff_adapter_create_dataset_empty():
    fuseki_service = helper_fuseki_service()

    with pytest.raises(ValueError) as exception:
        _ = fuseki_service.create_dataset('')

    assert 'Dataset name cannot be empty.' in str(exception)


def test_fuseki_diff_adapter_create_dataset_already_exists(fake_requests):
    fake_requests.text, fake_requests.status_code = '', 409

    fuseki_service = helper_fuseki_service(triplestore_service_url='http://some.url', http_requests=fake_requests)

    with pytest.raises(FusekiException) as exception:
        _ = fuseki_service.create_dataset('dataset')

    assert 'A dataset with this name already exists.' in str(exception)
