#!/usr/bin/python3

# commands.py
# Date:  16/09/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

from werkzeug.datastructures import FileStorage
from pathlib import Path

from rdf_differ.entrypoints.api.handlers import create_diff


def run_create(dataset, dataset_uri, old_path, new_path, old_version='old', new_version='new'):
    old = FileStorage(open(old_path, 'rb'))
    new = FileStorage(open(new_path, 'rb'))
    body = {
        'dataset_id': dataset,
        'dataset_uri': dataset_uri,
        'old_version_id': old_version,
        'new_version_id': new_version,
    }
    return body, old, new


def populate_fuseki():
    dataset_list = [
        {
            'dataset': 'subdiv',
            'dataset_uri': 'http://publications.europa.eu/resource/authority/subdivision',
            'old': Path(__file__).parents[1] / 'tests/test_data/subdivisions_sh_ds/data/v1/subdivisions-skos.rdf',
            'new': Path(__file__).parents[1] / 'tests/test_data/subdivisions_sh_ds/data/v2/subdivisions-skos.rdf'
        },
        {
            'dataset': 'eurovoc-fragment',
            'dataset_uri': 'http://eurovoc.europa.eu/100141',
            'old': Path(__file__).parents[1] / 'tests/test_data/eurovoc/old.rdf',
            'new': Path(__file__).parents[1] / 'tests/test_data/eurovoc/new.rdf',
        },
        {
            'dataset': 'countries-fragment',
            'dataset_uri': 'http://publications.europa.eu/resource/authority/country',
            'old': Path(__file__).parents[1] / 'tests/test_data/country/old-countries-skos-ap-act.rdf',
            'new': Path(__file__).parents[1] / 'tests/test_data/country/new-countries-skos-ap-act.rdf',
        },
        {
            'dataset': 'cob-fragment',
            'dataset_uri': 'http://publications.europa.eu/resource/authority/corporate-body/',
            'old': Path(__file__).parents[1] / 'tests/test_data/cob/old-corporatebodies-skos-ap-act.rdf',
            'new': Path(__file__).parents[1] / 'tests/test_data/cob/new-corporatebodies-skos-ap-act.rdf',
        },
        {
            'dataset': 'treaty-fragment',
            'dataset_uri': 'http://publications.europa.eu/resource/authority/treaty/',
            'old': Path(__file__).parents[1] / 'tests/test_data/treaty/old-treaties-skos-ap-act.rdf',
            'new': Path(__file__).parents[1] / 'tests/test_data/treaty/new-treaties-skos-ap-act.rdf',
        },
    ]

    for dataset in dataset_list:
        print(f"populating with {dataset['dataset']}")
        create_diff(*run_create(dataset['dataset'],
                                dataset['dataset_uri'],
                                dataset['old'],
                                dataset['new']))


if __name__ == '__main__':
    populate_fuseki()
