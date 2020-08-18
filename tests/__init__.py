import pathlib

TEST_FOLDER = pathlib.Path.cwd()
SUBDIVISIONS_DATA_FOLDER = TEST_FOLDER / "test_data/subdivisions_sh_ds/data"
SUBDIVISIONS_CONFIG = TEST_FOLDER / "test_data/subdivisions_sh_ds/subdiv.config"
SUBDIVISIONS_CONFIG_INCORRECT = TEST_FOLDER / "test_data/subdivisions_sh_ds/incorrect.subdiv.config"
DUMMY_DATASET_DIFF_DESCRIPTION = {
    "head": {
        "vars": ["versionHistoryGraph", "datasetVersion", "date", "currentVersionGraph", "schemeURI",
                 "versionNamedGraph", "versionId"]
    },
    "results": {
        "bindings": [
            {
                "versionHistoryGraph": {"type": "uri",
                                        "value": "http://publications.europa.eu/resource/authority/subdivision/version"},
                "datasetVersion": {"type": "literal", "value": "20171213-0"},
                "schemeURI": {"type": "uri",
                              "value": "http://publications.europa.eu/resource/authority/subdivision"},
                "versionNamedGraph": {"type": "uri",
                                      "value": "http://publications.europa.eu/resource/authority/subdivision/version/v1"},
                "versionId": {"type": "literal", "value": "v1"}
            },
            {
                "versionHistoryGraph": {"type": "uri",
                                        "value": "http://publications.europa.eu/resource/authority/subdivision/version"},
                "datasetVersion": {"type": "literal", "value": "20190220-0"},
                "currentVersionGraph": {"type": "uri",
                                        "value": "http://publications.europa.eu/resource/authority/subdivision/version/v2"},
                "schemeURI": {"type": "uri",
                              "value": "http://publications.europa.eu/resource/authority/subdivision"},
                "versionNamedGraph": {"type": "uri",
                                      "value": "http://publications.europa.eu/resource/authority/subdivision/version/v2"},
                "versionId": {"type": "literal", "value": "v2"}
            }
        ]
    }
}
DUMMY_DATASET_DELETED_COUNT = {'head': {'vars': ['insertionsGraph', 'triplesInInsertionGraph', 'versionGraph']},
                               'results': {'bindings': [{'insertionsGraph': {'type': 'uri',
                                                                             'value': 'http://publications.europa.eu/resource/authority/subdivision/version/v1/delta/v2/insertions'},
                                                         'triplesInDeletionGraph': {'type': 'literal',
                                                                                    'datatype': 'http://www.w3.org/2001/XMLSchema#integer',
                                                                                    'value': '3'},
                                                         'versionGraph': {'type': 'uri',
                                                                          'value': 'http://publications.europa.eu/resource/authority/subdivision/version'}}]}}
DUMMY_DATASET_INSERTED_COUNT = {'head': {'vars': ['insertionsGraph', 'triplesInInsertionGraph', 'versionGraph']},
                                'results': {'bindings': [{'insertionsGraph': {'type': 'uri',
                                                                              'value': 'http://publications.europa.eu/resource/authority/subdivision/version/v1/delta/v2/insertions'},
                                                          'triplesInInsertionGraph': {'type': 'literal',
                                                                                      'datatype': 'http://www.w3.org/2001/XMLSchema#integer',
                                                                                      'value': '387'},
                                                          'versionGraph': {'type': 'uri',
                                                                           'value': 'http://publications.europa.eu/resource/authority/subdivision/version'}}]}}
