from rdf_differ.core.domain.constants import DeltaOp
from rdf_differ.loader.domain.uris import UriBuilder


def test_base_derived_from_scheme():
    assert UriBuilder("http://zbw.eu/stw").base == "http://zbw.eu/stw/version"


def test_base_handles_trailing_slash_on_scheme():
    assert UriBuilder("http://zbw.eu/stw/").base == "http://zbw.eu/stw/version"


def test_explicit_base_overrides_and_strips_slash():
    b = UriBuilder("http://zbw.eu/stw", base_version_iri="http://x/v/")
    assert b.base == "http://x/v"


def test_version_and_record_and_named_graph_iris():
    b = UriBuilder("http://zbw.eu/stw")
    assert b.version_graph("9.0") == "http://zbw.eu/stw/version/9.0"
    assert b.version_named_graph_node("9.0") == "http://zbw.eu/stw/version/9.0/ng"
    # design ADR-3: record uses {base}/record/{id} (with slash)
    assert b.record("9.0") == "http://zbw.eu/stw/version/record/9.0"
    assert b.history_graph() == "http://zbw.eu/stw/version"
    assert b.history_named_graph_node() == "http://zbw.eu/stw/version/ng"


def test_delta_iris():
    b = UriBuilder("http://zbw.eu/stw")
    assert b.delta("8.14", "9.0") == "http://zbw.eu/stw/version/8.14/delta/9.0"
    assert (
        b.delta_op_graph("8.14", "9.0", DeltaOp.INSERTIONS)
        == "http://zbw.eu/stw/version/8.14/delta/9.0/insertions"
    )
    assert b.delta_op_named_graph_node("8.14", "9.0", DeltaOp.DELETIONS) == (
        "http://zbw.eu/stw/version/8.14/delta/9.0/deletions/ng"
    )


def test_version_ids_are_percent_encoded():
    b = UriBuilder("http://x/s")
    assert b.version_graph("a b/c") == "http://x/s/version/a%20b%2Fc"


def test_service_description_iris():
    b = UriBuilder("http://x/s")
    assert b.service() == "http://x/s/version/sparql-service"
    assert b.service_description() == "http://x/s/version/sparql-service/dd"
