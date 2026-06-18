from rdflib import Graph

from rdf_differ.adapters.loading.skolemizer import SkolemiseStrategy, strategy_for
from rdf_differ.domain.loading.blank_nodes import BlankNodePolicy, BlankNodeStrategy

DATA = b"@prefix ex: <http://ex/> . ex:a ex:p _:b . _:b ex:q ex:c ."


def _skolemised(data: bytes) -> bytes:
    return SkolemiseStrategy().transform(data, content_type="text/turtle", base_iri="http://ex/s")


def test_is_a_blank_node_strategy():
    assert isinstance(SkolemiseStrategy(), BlankNodeStrategy)
    assert SkolemiseStrategy().policy is BlankNodePolicy.SKOLEMISE


def test_replaces_blank_nodes_with_wellknown_genid_iris():
    out = _skolemised(DATA).decode()
    g = Graph()
    g.parse(data=out, format="turtle")
    # no blank nodes remain; the skolem IRIs use the W3C .well-known/genid path
    assert not any(t for s, p, o in g for t in (s, o) if str(type(t).__name__) == "BNode")
    assert "/.well-known/genid/" in out
    assert "http://ex/s/.well-known/genid/" in out


def test_deterministic_across_runs():
    assert _skolemised(DATA) == _skolemised(DATA)


def test_strategy_for_returns_skolemiser_or_identity():
    assert isinstance(strategy_for(BlankNodePolicy.SKOLEMISE), SkolemiseStrategy)
    assert strategy_for(BlankNodePolicy.EXCLUDE).policy is BlankNodePolicy.EXCLUDE
