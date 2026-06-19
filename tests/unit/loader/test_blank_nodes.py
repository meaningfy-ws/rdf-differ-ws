import pytest

from rdf_differ.loader.domain.model import (
    BlankNodePolicy,
    BlankNodeStrategy,
    IdentityBlankNodeStrategy,
)


def test_policy_values():
    assert {p.value for p in BlankNodePolicy} == {"exclude", "document_only", "skolemise"}


def test_identity_strategy_returns_data_unchanged():
    strat = IdentityBlankNodeStrategy(BlankNodePolicy.DOCUMENT_ONLY)
    data = b"<a> <b> <c> ."
    assert strat.transform(data, content_type="text/turtle", base_iri="http://x/") == data
    assert isinstance(strat, BlankNodeStrategy)


def test_identity_strategy_rejects_skolemise():
    with pytest.raises(ValueError, match="SKOLEMISE"):
        IdentityBlankNodeStrategy(BlankNodePolicy.SKOLEMISE)
