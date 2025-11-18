import json
import os
import subprocess
import parse
from pathlib import Path

import pytest
from pytest_bdd import given, when, then, scenario, parsers

SCRIPT_PATH = "../../bash/rdf-differ.sh"
BASE_URL = os.environ.get("RDF_DIFFER_BASE_URL", "http://localhost:4030")
SAVED_REPORT = "../test_data/owl/ePO_sample-4.0.0-upd_diff-report.json"
REUSE_SAVED_REPORT = os.environ.get(
    "RDF_DIFFER_REUSE_SAVED_REPORT", "true"
).lower() in ["1", "true", "yes"]

# trick to run diffing only once and not for all scenarios
_diff_cache = {}


@scenario("../features/owl_diff.feature", "Diffing example resources in the OWL sample")
def test_owl_diff_feature():
    pass


@pytest.fixture
def ctx(tmp_path):
    """Context fixture to store state between steps."""
    return {"tmpdir": tmp_path}


@given("the test prefixes are defined")
def prefixes(ctx):
    # Hardcoded prefixes for converting between the feature file
    # and the diff reports which are RDF/JSON with no prefixes
    ctx["prefixes"] = {
        "epo": "http://data.europa.eu/a4g/ontology#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    }
    return ctx["prefixes"]


@given(parsers.parse('the OWL files "{old}" and "{new}"'))
def owl_files(ctx, old, new):
    # store absolute paths
    ctx["old"] = str(Path(old))
    ctx["new"] = str(Path(new))
    return ctx


@when("the diff is run")
def run_diff(ctx):
    script = os.path.abspath(os.path.join(os.path.dirname(__file__), SCRIPT_PATH))
    outdir = str(ctx["tmpdir"])
    old = ctx["old"]
    new = ctx["new"]
    profile = "owl-core-en-only"

    # we keep a record of already run diffs to speed up tests (we set the cache at the end of this function)
    key = (old, new)
    if key in _diff_cache:
        ctx["report"] = _diff_cache[key]
        return

    if REUSE_SAVED_REPORT:
        # use pre-existing report -- for faster testing/debugging of this test skipping the building of the report
        report_file = Path(
            os.path.abspath(os.path.join(os.path.dirname(__file__), SAVED_REPORT))
        )
    else:
        # run full workflow producing JSON output into temporary dir -- this should be the normal way
        # WARNING: as this runs an async call, sometimes this can fail due to race conditions
        # (the Celery task queue may be empty if called too fast or too late)
        result = subprocess.run(
            [
                script,
                "--base-url",
                BASE_URL,
                "--old",
                old,
                "--new",
                new,
                "--ap",
                profile,
                "--template",
                "json",
                "--output",
                outdir,
                "full",
            ],
            capture_output=False,
            text=True,
        )

        assert (
            result.returncode == 0
        ), f"Diff script failed: {result.stderr}\n{result.stdout}"
        report_file = Path(outdir) / "diff.json"

    assert report_file.exists(), f"Report file not found: {report_file}"
    with open(report_file) as fh:
        report = json.load(fh)
        ctx["report"] = report
        _diff_cache[key] = report


def expand(prefixed, prefixes):
    if prefixed is None:
        return None
    if ":" not in prefixed:
        return prefixed
    p, local = prefixed.split(":", 1)
    if p not in prefixes:
        raise ValueError(f"Unknown prefix: {p}")
    return prefixes[p] + local


def camel_to_snake(name: str) -> str:
    # Convert camelCase or mixed to snake_case (prefLabel -> pref_label)
    out = ""
    for ch in name:
        if ch.isupper():
            out += "_" + ch.lower()
        else:
            out += ch
    return out


# this is only possible in Behave (e.g. {parent:NullableString})
# @parse.with_pattern(r'.*')
# def parse_nullable_string(text):
#     return text
# register_type(NullableString=parse_nullable_string)


# pytest-bdd currently lacks support for optional parameters (empty cells in the feature) in parse, so we use a regex trick
# @then(parsers.parse('the report should contain the change for "{type}","{instance}","{operation}","{parent}","{new_value}"'))
@then(
    parsers.re(
        r'the report should contain the change for "(?P<type>[^"]*)","(?P<instance>[^"]*)","(?P<operation>[^"]*)","(?P<parent>[^"]*)","(?P<new_value>[^"]*)"'
    )
)
def assert_report_contains(ctx, type, instance, operation, parent, new_value):
    report = ctx.get("report")
    prefixes = ctx.get("prefixes")

    assert report is not None, "Report not found in context"

    # empty strings in table become '', map them to None
    parent = parent.strip() or None
    new_value = new_value.strip() or None

    if type == "class" and operation == "added":
        key = "added_instance_class.rq"
        assert key in report, f"Missing key {key} in report"
        full_instance = expand(instance, prefixes)
        bindings = report[key].get("results", {}).get("bindings", [])
        assert any(
            b.get("instance", {}).get("value") == full_instance for b in bindings
        ), f"Added class {full_instance} not found in {key}"

    elif type in ("data_property", "object_property") and operation == "changed":
        # instance here is the property (prefixed), parent is the class instance
        prop_prefix, prop_local = instance.split(":", 1)
        prop_snake = camel_to_snake(prop_local)
        key = f"changed_property_class_{prop_snake}.rq"
        assert key in report, f"Missing key {key} in report"
        full_parent = expand(parent, prefixes)
        bindings = report[key].get("results", {}).get("bindings", [])
        # find binding for the parent instance
        binding = None
        for b in bindings:
            if b.get("instance", {}).get("value") == full_parent:
                binding = b
                break
        assert binding is not None, f"No binding for parent {full_parent} in {key}"
        # check oldProperty and newProperty values
        expected_old = expand(instance, prefixes)
        expected_new = expand(new_value, prefixes)
        assert (
            binding.get("oldProperty", {}).get("value") == expected_old
        ), f"oldProperty mismatch: expected {expected_old}, got {binding.get('oldProperty', {}).get('value')}"
        assert (
            binding.get("newProperty", {}).get("value") == expected_new
        ), f"newProperty mismatch: expected {expected_new}, got {binding.get('newProperty', {}).get('value')}"

    elif type in ("data_property", "object_property") and operation == "added":
        key = f"added_instance_{'datatype_property' if type=='data_property' else 'object_property'}.rq"
        assert key in report, f"Missing key {key} in report"
        full_instance = expand(instance, prefixes)
        bindings = report[key].get("results", {}).get("bindings", [])
        assert any(
            b.get("instance", {}).get("value") == full_instance for b in bindings
        ), f"Added property {full_instance} not found in {key}"

    else:
        raise AssertionError(
            f"Unsupported combination: type={type}, operation={operation}"
        )
