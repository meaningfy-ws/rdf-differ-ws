#!/usr/bin/python3

# rdf_converter.py
# Date:  31/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

""" """
from rdflib.tools.rdfpipe import parse_and_serialize


def convert_test_data(input_file, output_file, input_format='', additional_bindings=None):
    ns_binding = {
        'skos': 'http://www.w3.org/2004/02/skos/core#',
        'skosxl': 'http://www.w3.org/2008/05/skos-xl#',
        'dct': 'http://purl.org/dc/terms/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'euvoc': 'http://publications.europa.eu/ontology/euvoc#',
        'lemon': 'http://lemon-model.net/lemon#',
        'lexinfo': 'http://www.lexinfo.net/ontology/2.0/lexinfo#',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'rdf': 'http://www.w3.org/2002/07/owl#',
        'xsd': 'http://www.w3.org/2001/XMLSchema#',

        'domain': 'http://eurovoc.europa.eu/domain',
        'notation': 'http://publications.europa.eu/resource/authority/notation-type',
        'label': 'http://publications.europa.eu/resource/authority/label-type',
        'context': 'http://publications.europa.eu/resource/authority/use-context',
        'status': 'http://publications.europa.eu/resource/authority/concept-status/',

        'p1': 'http://inexistent/domain/',
    }

    if additional_bindings:
        ns_binding = {**ns_binding, **additional_bindings}

    guess = not input_format

    parse_and_serialize(input_files=[input_file], input_format=input_format, guess=guess,
                        outfile=output_file, output_format='ttl', ns_bindings=ns_binding)
