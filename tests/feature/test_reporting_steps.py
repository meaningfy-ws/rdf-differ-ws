"""Steps for reporting.feature — application-profile discovery.

Infra-free: exercises ApplicationProfileManager over tests/test_data/sample_ap_config.
"""

from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from rdf_differ.reporting.services.ap_manager import ApplicationProfileManager

scenarios("reporting.feature")

_SAMPLE_AP_ROOT = Path(__file__).resolve().parents[1] / "test_data" / "sample_ap_config"


@pytest.fixture
def ctx():
    return {"root": _SAMPLE_AP_ROOT, "result": None, "error": None}


def _manager(ctx, application_profile=None):
    return ApplicationProfileManager(
        application_profile=application_profile, root_folder=ctx["root"]
    )


@given("the application profiles root is the sample AP config")
def _root(ctx):
    assert ctx["root"].is_dir()


@when("I list the application profiles")
def _list_aps(ctx):
    ctx["result"] = _manager(ctx).list_aps()


@when(parsers.parse('I list the template variants of "{ap}"'))
def _list_variants(ctx, ap):
    ctx["result"] = _manager(ctx, ap).list_template_variants()


@when(parsers.parse('I build the queries dict of "{ap}"'))
def _queries_dict(ctx, ap):
    ctx["result"] = _manager(ctx, ap).get_queries_dict()


@when(parsers.parse('I request the queries folder of "{ap}"'))
def _queries_folder(ctx, ap):
    try:
        ctx["result"] = _manager(ctx, ap).get_queries_folder()
    except Exception as exception:
        ctx["error"] = exception


@then(parsers.parse('the profiles include "{first}" and "{second}"'))
def _profiles_include(ctx, first, second):
    assert first in ctx["result"]
    assert second in ctx["result"]


@then(parsers.parse('the variants include "{first}" and "{second}"'))
def _variants_include(ctx, first, second):
    assert first in ctx["result"]
    assert second in ctx["result"]


@then("the queries dict is not empty")
def _queries_not_empty(ctx):
    assert isinstance(ctx["result"], dict)
    assert ctx["result"]


@then("a lookup error is raised")
def _lookup_error(ctx):
    assert isinstance(ctx["error"], LookupError)


@then("a file-not-found error is raised")
def _file_not_found(ctx):
    assert isinstance(ctx["error"], FileNotFoundError)
