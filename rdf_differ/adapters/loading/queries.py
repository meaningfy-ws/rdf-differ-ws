"""Parametrised SPARQL templates for the skos-history load/diff (no free strings).

Every builder takes validated IRIs (from ``UriBuilder``) and bound literal values;
nothing is f-string-concatenated from raw user input. Templates mirror
``load_versions.sh`` (``load_version``/``load_delta`` and the body), minus the
IFLA-specific triples injected into the version graphs — version graphs stay pure
data, as the four-named-graph contract requires.
"""

from rdf_differ.domain.constants import DeltaOp
from rdf_differ.domain.loading.blank_nodes import BlankNodePolicy

# `:` is the skos-history namespace, matching the legacy script's PREFIXES block.
PREFIXES = """
prefix : <http://purl.org/skos-history/>
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

# Blank-node policy → the SPARQL filter applied during delta computation (DEC-9).
# SKOLEMISE has no filter here — it is handled by rewriting RDF before load.
BLANK_NODE_FILTERS: dict[BlankNodePolicy, str] = {
    BlankNodePolicy.EXCLUDE: "  filter isIRI(?s)\n  filter (isIRI(?o) || isLiteral(?o) || isNumeric(?o))",
    BlankNodePolicy.DOCUMENT_ONLY: "",
    BlankNodePolicy.SKOLEMISE: "",
}

_OP_CLASS = {
    DeltaOp.INSERTIONS: "skos-history:SchemeDeltaInsertions",
    DeltaOp.DELETIONS: "skos-history:SchemeDeltaDeletions",
}


def _lit(value: str) -> str:
    """Escape a string for use inside a double-quoted SPARQL literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def clear_graph(graph_iri: str) -> str:
    # SILENT: clearing a not-yet-existing delta graph must not error (first run).
    return f"CLEAR SILENT GRAPH <{graph_iri}>"


def delta_update(
    target_graph: str, minuend_graph: str, subtrahend_graph: str, policy: BlankNodePolicy
) -> str:
    """``INSERT { GRAPH target { ?s ?p ?o } } WHERE { minuend MINUS subtrahend [filter] }``."""
    bnode_filter = BLANK_NODE_FILTERS[policy]
    filter_block = f"\n{bnode_filter}" if bnode_filter else ""
    return f"""{PREFIXES}
INSERT {{
  GRAPH <{target_graph}> {{ ?s ?p ?o }}
}}
WHERE {{
  graph <{minuend_graph}> {{ ?s ?p ?o }}
  minus {{ graph <{subtrahend_graph}> {{ ?s ?p ?o }} }}{filter_block}
}}"""


def service_description_update(
    service_uri: str, service_dd_uri: str, query_endpoint: str, dataset_id: str
) -> str:
    return f"""{PREFIXES}
INSERT {{
  <{service_uri}> a sd:Service ;
      sd:endpoint <{query_endpoint}> ;
      sd:defaultDataset <{service_dd_uri}> .
  <{service_dd_uri}> a sd:Dataset ;
      dcterms:title "{_lit(dataset_id)} Versions SPARQL Service" ;
      sd:defaultGraph [ a sd:Graph ; dcterms:title "{_lit(dataset_id)} Versions SPARQL Service Description" ] .
}} WHERE {{}}"""


def history_set_update(
    history_graph: str,
    scheme_uri: str,
    current_record: str,
    query_endpoint: str,
    history_ng_node: str,
) -> str:
    return f"""{PREFIXES}
INSERT {{
  graph <{history_graph}> {{
    <{history_graph}> a dsv:VersionHistorySet ;
        skos-history:isVersionHistoryOf <{scheme_uri}> ;
        dsv:currentVersionRecord <{current_record}> ;
        void:sparqlEndpoint <{query_endpoint}> ;
        skos-history:usingNamedGraph <{history_ng_node}> .
    <{history_ng_node}> a sd:NamedGraph ; sd:name <{history_graph}> .
  }}
}} WHERE {{}}"""


def version_record_update(
    history_graph: str,
    record: str,
    version_graph: str,
    version_ng_node: str,
    identifier: str,
    date: str | None,
) -> str:
    date_triple = f'\n        dc:date "{_lit(date)}"^^xsd:date ;' if date else ""
    return f"""{PREFIXES}
INSERT {{
  graph <{history_graph}> {{
    <{record}> a dsv:VersionHistoryRecord ;
        dsv:hasVersionHistorySet <{history_graph}> ;
        skos-history:usingNamedGraph <{version_ng_node}> ;{date_triple}
        dc:identifier "{_lit(identifier)}" .
    <{version_ng_node}> a sd:NamedGraph ; sd:name <{version_graph}> .
  }}
}} WHERE {{}}"""


def prev_link_update(history_graph: str, record_new: str, record_old: str) -> str:
    return f"""{PREFIXES}
INSERT {{
  graph <{history_graph}> {{ <{record_new}> xhv:prev <{record_old}> . }}
}} WHERE {{}}"""


def delta_metadata_update(
    history_graph: str, record_old: str, record_new: str, delta_uri: str
) -> str:
    return f"""{PREFIXES}
INSERT {{
  graph <{history_graph}> {{
    <{record_old}> skos-history:hasDelta <{delta_uri}> .
    <{record_new}> skos-history:hasDelta <{delta_uri}> .
    <{delta_uri}> a skos-history:SchemeDelta ;
        skos-history:deltaFrom <{record_old}> ;
        skos-history:deltaTo <{record_new}> .
  }}
}} WHERE {{}}"""


def delta_part_update(
    history_graph: str, delta_uri: str, delta_op_graph: str, delta_op_ng: str, op: DeltaOp
) -> str:
    return f"""{PREFIXES}
INSERT {{
  graph <{history_graph}> {{
    <{delta_uri}> dcterms:hasPart <{delta_op_graph}> .
    <{delta_op_graph}> a {_OP_CLASS[op]} ;
        dcterms:isPartOf <{delta_uri}> ;
        skos-history:usingNamedGraph <{delta_op_ng}> .
    <{delta_op_ng}> a sd:NamedGraph ; sd:name <{delta_op_graph}> .
  }}
}} WHERE {{}}"""


def register_named_graph_update(service_dd_uri: str, ng_node: str, graph_iri: str) -> str:
    return f"""{PREFIXES}
INSERT {{
  <{service_dd_uri}> sd:namedGraph <{ng_node}> .
  <{ng_node}> a sd:NamedGraph ; sd:name <{graph_iri}> .
}} WHERE {{}}"""


def extract_version_meta_query(version_graph: str, scheme_uri: str) -> str:
    """SELECT identifier/date straight from the loaded version data (F7).

    Mirrors the script's OPTIONAL/BIND block: ``owl:versionInfo`` (SVN strings
    skipped) or ``dcterms:hasVersion`` for the identifier; ``dcterms:modified`` or
    ``dcterms:issued`` normalised to ``yyyy-mm-dd`` for the date.
    """
    return f"""{PREFIXES}
SELECT ?identifier ?date WHERE {{
  GRAPH <{version_graph}> {{
    OPTIONAL {{ <{scheme_uri}> owl:versionInfo ?vi . FILTER (!CONTAINS(STR(?vi), "$")) }}
    OPTIONAL {{ <{scheme_uri}> dcterms:hasVersion ?hv }}
    OPTIONAL {{ <{scheme_uri}> dcterms:issued ?issued }}
    OPTIONAL {{ <{scheme_uri}> dcterms:modified ?modified }}
    BIND (STR(COALESCE(?vi, ?hv)) AS ?identifier)
    BIND (STR(COALESCE(?modified, ?issued)) AS ?someStr)
    BIND (SUBSTR(?someStr, 1, 10) AS ?date)
  }}
}} LIMIT 1"""


def count_graph_query(graph_iri: str) -> str:
    return f"SELECT (COUNT(*) AS ?c) WHERE {{ GRAPH <{graph_iri}> {{ ?s ?p ?o }} }}"


def ask_graph_nonempty_query(graph_iri: str) -> str:
    return f"ASK {{ GRAPH <{graph_iri}> {{ ?s ?p ?o }} }}"
