from rdf_differ.loader.domain.model import (
    all_delta_pairs,
    consecutive_pairs,
    direct_to_current_pairs,
)


def test_consecutive_pairs():
    assert consecutive_pairs(["a", "b", "c"]) == [("a", "b"), ("b", "c")]


def test_two_versions_single_pair_no_direct_to_current():
    assert all_delta_pairs(["a", "b"]) == [("a", "b")]
    assert direct_to_current_pairs(["a", "b"]) == []


def test_direct_to_current_excludes_penultimate():
    # versions a,b,c,d -> latest=d, penultimate=c; direct-to-current = a->d, b->d (not c->d)
    assert direct_to_current_pairs(["a", "b", "c", "d"]) == [("a", "d"), ("b", "d")]


def test_all_pairs_consecutive_plus_direct_to_current_deduped():
    pairs = all_delta_pairs(["a", "b", "c", "d"], compute_direct_to_current=True)
    assert pairs == [("a", "b"), ("a", "d"), ("b", "c"), ("b", "d"), ("c", "d")]


def test_all_pairs_direct_to_current_disabled():
    assert all_delta_pairs(["a", "b", "c", "d"], compute_direct_to_current=False) == [
        ("a", "b"),
        ("b", "c"),
        ("c", "d"),
    ]


def test_three_versions_direct_to_current():
    # a,b,c -> latest=c, penultimate=b; direct-to-current = a->c only
    assert direct_to_current_pairs(["a", "b", "c"]) == [("a", "c")]
    assert all_delta_pairs(["a", "b", "c"]) == [("a", "b"), ("a", "c"), ("b", "c")]
