from rdf_differ.core.domain.constants import DeltaOp
from rdf_differ.loader.adapters import sparql_queries as q
from rdf_differ.loader.domain.model import BlankNodePolicy


def test_clear_graph():
    assert q.clear_graph("http://x/g") == "CLEAR SILENT GRAPH <http://x/g>"


def test_delta_update_targets_and_minus():
    sparql = q.delta_update(
        "http://x/d/ins", "http://x/new", "http://x/old", BlankNodePolicy.EXCLUDE
    )
    assert "GRAPH <http://x/d/ins> { ?s ?p ?o }" in sparql
    assert "graph <http://x/new> { ?s ?p ?o }" in sparql
    assert "minus { graph <http://x/old> { ?s ?p ?o } }" in sparql


def test_delta_update_exclude_has_bnode_filter():
    sparql = q.delta_update("t", "m", "s", BlankNodePolicy.EXCLUDE)
    assert "filter isIRI(?s)" in sparql
    assert "isLiteral(?o)" in sparql


def test_delta_update_document_only_has_no_filter():
    sparql = q.delta_update("t", "m", "s", BlankNodePolicy.DOCUMENT_ONLY)
    assert "filter isIRI(?s)" not in sparql


def test_delta_part_uses_correct_class():
    ins = q.delta_part_update("h", "d", "d/ins", "d/ins/ng", DeltaOp.INSERTIONS)
    assert "skos-history:SchemeDeltaInsertions" in ins
    dele = q.delta_part_update("h", "d", "d/del", "d/del/ng", DeltaOp.DELETIONS)
    assert "skos-history:SchemeDeltaDeletions" in dele


def test_version_record_omits_date_when_absent():
    with_date = q.version_record_update("h", "rec", "vg", "ng", "id-1", "2020-01-01")
    assert 'dc:date "2020-01-01"^^xsd:date' in with_date
    no_date = q.version_record_update("h", "rec", "vg", "ng", "id-1", None)
    assert "dc:date" not in no_date
    assert 'dc:identifier "id-1"' in no_date


def test_literal_escaping():
    sparql = q.service_description_update("s", "dd", "http://e", 'wei"rd')
    assert 'wei\\"rd' in sparql
