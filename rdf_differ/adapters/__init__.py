#!/usr/bin/python3

# __init__.py
# Date: 11/08/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com


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
QUERY_DATASET_DESCRIPTION = """
SELECT ?versionHistoryGraph (?identifier AS ?datasetVersion) ?currentVersionGraph ?schemeURI \
?versionNamedGraph ?versionId ?description ?created
WHERE {
  # parameters
  VALUES ( ?versionHistoryGraph ) {
    ( undef )
  }
  GRAPH ?versionHistoryGraph {
    ?vhr dsv:hasVersionHistorySet ?vhs .
    OPTIONAL {
        ?vhs dcterms:description ?description
    }
    OPTIONAL {
        ?vhs dcterms:created ?created
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
QUERY_INSERT_DESCRIPTION = """
INSERT 
{
   GRAPH ?versionHistoryGraph {    
     ?vhs dcterms:description ?description;
      dcterms:created ?currentTime .
  }
}
WHERE {
  # parameters
  VALUES ( ?description ) {
    ( "~description~"@en )
  }
  GRAPH ?versionHistoryGraph {    
     ?vhs a dsv:VersionHistorySet .
    
    BIND (now() as ?currentTime)
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