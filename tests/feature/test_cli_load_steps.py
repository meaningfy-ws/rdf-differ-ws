"""Steps for cli_load.feature — the rdf-diff CLI.

Infra-free: click CliRunner driving the in-memory rdflib engine over sample OWL data.
"""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from pytest_bdd import given, parsers, scenarios, then, when

from rdf_differ.loader.entrypoints.cli import cli

scenarios("cli_load.feature")

_OWL = Path(__file__).resolve().parents[1] / "test_data" / "owl"


@pytest.fixture
def context(tmp_path):
    return {"runner": CliRunner(), "tmp": tmp_path, "out": tmp_path / "out", "result": None}


def _write_config(context, old_file, new_file):
    config_path = context["tmp"] / "load.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "dataset_id": "ds",
                "scheme_uri": "http://example.org/scheme",
                "versions": [
                    {"id": "v1", "file": str(old_file)},
                    {"id": "v2", "file": str(new_file)},
                ],
            }
        )
    )
    context["config"] = config_path


@given("a load configuration for the sample OWL versions")
def _config_ok(context):
    _write_config(context, _OWL / "ePO_sample-4.0.0.orig.ttl", _OWL / "ePO_sample-4.0.0.upd.ttl")


@given("a load configuration pointing at a missing version file")
def _config_missing(context):
    _write_config(context, context["tmp"] / "missing-old.ttl", context["tmp"] / "missing-new.ttl")


@when('I run "load" with the rdflib engine and an output directory')
def _run_load(context):
    context["result"] = context["runner"].invoke(
        cli,
        [
            "load",
            "--config",
            str(context["config"]),
            "--engine",
            "rdflib",
            "--out",
            str(context["out"]),
        ],
    )


@when('I run "load" with no config option')
def _run_no_config(context):
    context["result"] = context["runner"].invoke(cli, ["load", "--engine", "rdflib"])


@then("the command exits successfully")
def _exit_ok(context):
    assert context["result"].exit_code == 0, context["result"].output


@then("the command exits with an error")
def _exit_error(context):
    assert context["result"].exit_code != 0


@then(parsers.parse('a "{name}" artifact is written'))
def _artifact_written(context, name):
    assert (context["out"] / name).is_file()
