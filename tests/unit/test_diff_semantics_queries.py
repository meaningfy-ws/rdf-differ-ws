"""Verification gate for the diff-semantics filter relaxation (issues #142, #143).

EPIC: resolve-open-issues — Capability 3 (diff-semantics).

These tests execute the *actual* committed ``updated_property_*.rq`` template text
against a minimal in-memory ``rdflib.Dataset`` that mirrors the skos-history layout the
queries traverse (a version-history graph carrying the dsv/sh/dct/sd/xhv/dc metadata,
the old & new version graphs, and the insertions/deletions graphs).

The relaxed pairing FILTER must surface, as ``updated`` rows:
- (a) a language-tag *change*  ("text"@en -> "text"@fr)            [#142]
- (b) a language-tag *removal* ("text"@en -> "text")              [#142]
- (c) a literal -> IRI change  ("label" -> <http://ex/iri>)       [#143]
and must NOT surface an unchanged value (d).

With the OLD filter, cases (a),(b),(c) are dropped (test RED for the right reason);
with the relaxed filter they appear (GREEN).
"""
from pathlib import Path

import pytest
import rdflib

# --- locate the committed templates -----------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "resources" / "templates"

LANG_FALLBACK_QUERY = (
    TEMPLATES_DIR
    / "skos-core-lang-fallback"
    / "queries"
    / "updated_property_concept_pref_label.rq"
)

# --- namespaces used by the skos-history layout ------------------------------

EX = "http://example.org/"
CONCEPT = f"{EX}c1"

# version-history metadata graph (named so the query's `GRAPH ?versionHistoryGraph`
# block, with VALUES binding ?versionHistoryGraph to UNDEF, can match it)
VHG = f"{EX}vhg"
OLD_GRAPH = f"{EX}old"
NEW_GRAPH = f"{EX}new"
INS_GRAPH = f"{EX}insertions"
DEL_GRAPH = f"{EX}deletions"

SKOS = "http://www.w3.org/2004/02/skos/core#"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
PREF_LABEL = f"{SKOS}prefLabel"
CONCEPT_CLASS = f"{SKOS}Concept"


def _metadata_turtle() -> str:
    """The skos-history version metadata the query traverses to bind the graphs."""
    return f"""
    @prefix dsv:  <http://purl.org/iso25964/DataSet/Versioning#> .
    @prefix sd:   <http://www.w3.org/ns/sparql-service-description#> .
    @prefix sh:   <http://purl.org/skos-history/> .
    @prefix xhv:  <http://www.w3.org/1999/xhtml/vocab#> .
    @prefix dc:   <http://purl.org/dc/elements/1.1/> .
    @prefix dct:  <http://purl.org/dc/terms/> .
    @prefix ex:   <{EX}> .

    ex:versionset dsv:currentVersionRecord ex:vNew .
    ex:vNew dc:identifier "2" ;
            xhv:prev ex:vOld .
    ex:vOld dc:identifier "1" .

    ex:delta a sh:SchemeDelta ;
        sh:deltaFrom ex:fromRec ;
        sh:deltaTo   ex:toRec ;
        dct:hasPart  ex:insRecord ;
        dct:hasPart  ex:delRecord .

    ex:fromRec dc:identifier "1" ;
        sh:usingNamedGraph [ sd:name <{OLD_GRAPH}> ] .
    ex:toRec dc:identifier "2" ;
        sh:usingNamedGraph [ sd:name <{NEW_GRAPH}> ] .

    ex:delRecord a sh:SchemeDeltaDeletions ;
        sh:usingNamedGraph [ sd:name <{DEL_GRAPH}> ] .
    ex:insRecord a sh:SchemeDeltaInsertions ;
        sh:usingNamedGraph [ sd:name <{INS_GRAPH}> ] .
    """


def _build_dataset(old_value, new_value, *, changed=True) -> rdflib.Dataset:
    """Build a dataset where ``c1 skos:prefLabel`` moves from old_value to new_value.

    old_value/new_value are rdflib terms (Literal or URIRef). When ``changed`` is
    True the old value lands in the deletions graph and the new value in the
    insertions graph; when False both graphs carry the same (unchanged) value so it
    must not be reported.
    """
    ds = rdflib.Dataset(default_union=False)

    # version-history metadata graph
    ds.graph(rdflib.URIRef(VHG)).parse(data=_metadata_turtle(), format="turtle")

    concept = rdflib.URIRef(CONCEPT)
    pref = rdflib.URIRef(PREF_LABEL)
    rdf_type = rdflib.URIRef(RDF_TYPE)
    concept_cls = rdflib.URIRef(CONCEPT_CLASS)

    # old version graph: instance + old value
    g_old = ds.graph(rdflib.URIRef(OLD_GRAPH))
    g_old.add((concept, rdf_type, concept_cls))
    g_old.add((concept, pref, old_value))

    # new version graph: instance + new value
    g_new = ds.graph(rdflib.URIRef(NEW_GRAPH))
    g_new.add((concept, rdf_type, concept_cls))
    g_new.add((concept, pref, new_value))

    # delta graphs
    g_del = ds.graph(rdflib.URIRef(DEL_GRAPH))
    g_ins = ds.graph(rdflib.URIRef(INS_GRAPH))
    if changed:
        g_del.add((concept, pref, old_value))
        g_ins.add((concept, pref, new_value))
    else:
        # unchanged: value present in both delta graphs would be a false positive
        g_del.add((concept, pref, old_value))
        g_ins.add((concept, pref, new_value))
    return ds


def _run(query_text: str, ds: rdflib.Dataset):
    return list(ds.query(query_text))


@pytest.fixture(scope="module")
def query_text() -> str:
    return LANG_FALLBACK_QUERY.read_text()


# --- the three relaxation cases (#142 / #143) --------------------------------

L = rdflib.Literal
URI = rdflib.URIRef


def test_language_tag_change_is_reported(query_text):
    """#142: 'text'@en -> 'text'@fr surfaces as an update."""
    ds = _build_dataset(L("text", lang="en"), L("text", lang="fr"))
    rows = _run(query_text, ds)
    olds = {str(r.oldValue) for r in rows}
    news = {str(r.newValue) for r in rows}
    assert rows, "language-tag change produced no update row"
    assert "text" in olds and "text" in news


def test_language_tag_removal_is_reported(query_text):
    """#142: 'text'@en -> 'text' (no tag) surfaces as an update."""
    ds = _build_dataset(L("text", lang="en"), L("text"))
    rows = _run(query_text, ds)
    assert rows, "language-tag removal produced no update row"


def test_literal_to_iri_is_reported(query_text):
    """#143: 'label' (literal) -> <iri> (object) surfaces as an update."""
    ds = _build_dataset(L("label"), URI("http://ex/iri"))
    rows = _run(query_text, ds)
    assert rows, "literal->IRI change produced no update row"
    news = {str(r.newValue) for r in rows}
    assert "http://ex/iri" in news


def test_unchanged_value_is_not_reported(query_text):
    """A value identical in old & new must not be reported as updated."""
    ds = _build_dataset(L("text", lang="en"), L("text", lang="en"), changed=False)
    rows = _run(query_text, ds)
    assert not rows, f"unchanged value wrongly reported as update: {rows}"


# --- text-presence guard across ALL templates --------------------------------

RELAXED_FRAGMENT_SIMPLE = (
    "str(?oldValue) = str(?newValue)"
)


def _all_updated_property_files():
    return sorted(TEMPLATES_DIR.glob("*/queries/updated_property_*.rq"))


def test_every_template_has_the_relaxation():
    """Every updated_property_*.rq must carry the #142/#143 relaxation markers."""
    files = _all_updated_property_files()
    assert files, "no updated_property templates found"
    missing = []
    for f in files:
        txt = f.read_text()
        # both shapes must now admit a same-lexical-text and a literal<->IRI pairing
        if "str(?oldValue) = str(?newValue)" not in txt:
            missing.append(str(f))
        if "isLiteral(?oldValue) != isLiteral(?newValue)" not in txt:
            missing.append(str(f))
    assert not missing, f"templates missing relaxation: {missing}"
