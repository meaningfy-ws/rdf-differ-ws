"""Unit tests for the ``rdf-diff load`` CLI entrypoint."""

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from rdf_differ.loader.entrypoints.cli import cli

SCHEME = "http://ex/scheme"

V1_TTL = """@prefix ex: <http://ex/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
<http://ex/scheme> a skos:ConceptScheme .
ex:a a skos:Concept ; skos:inScheme <http://ex/scheme> ; skos:prefLabel "A" .
"""

V2_TTL = """@prefix ex: <http://ex/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
<http://ex/scheme> a skos:ConceptScheme .
ex:a a skos:Concept ; skos:inScheme <http://ex/scheme> ; skos:prefLabel "A" .
ex:b a skos:Concept ; skos:inScheme <http://ex/scheme> ; skos:prefLabel "B" .
"""


def _write_config(tmp_path: Path, engine: str | None = None, versions: int = 2) -> Path:
    v1 = tmp_path / "v1.ttl"
    v1.write_text(V1_TTL, encoding="utf-8")
    specs = [{"id": "v1", "file": str(v1)}]
    if versions >= 2:
        v2 = tmp_path / "v2.ttl"
        v2.write_text(V2_TTL, encoding="utf-8")
        specs.append({"id": "v2", "file": str(v2)})

    data: dict = {"dataset_id": "demo", "scheme_uri": SCHEME, "versions": specs}
    if engine is not None:
        data["engine"] = engine

    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(yaml.safe_dump(data), encoding="utf-8")
    return cfg


def _assert_result_passed(out_dir: Path) -> None:
    result_file = out_dir / "result.json"
    assert result_file.exists()
    payload = json.loads(result_file.read_text(encoding="utf-8"))
    assert payload["dataset_id"] == "demo"


def test_load_oxigraph_writes_artifacts(tmp_path):
    cfg = _write_config(tmp_path, engine="oxigraph")
    out = tmp_path / "out_ox"
    runner = CliRunner()

    result = runner.invoke(
        cli, ["load", "--config", str(cfg), "--engine", "oxigraph", "--out", str(out)]
    )

    assert result.exit_code == 0, result.output
    _assert_result_passed(out)


def test_load_rdflib_writes_artifacts(tmp_path):
    cfg = _write_config(tmp_path, engine="rdflib")
    out = tmp_path / "out_rdflib"
    runner = CliRunner()

    result = runner.invoke(
        cli, ["load", "--config", str(cfg), "--engine", "rdflib", "--out", str(out)]
    )

    assert result.exit_code == 0, result.output
    _assert_result_passed(out)


def test_engine_flag_overrides_config_engine(tmp_path):
    # Config declares remote, but --engine oxigraph overrides → in-memory run.
    cfg = _write_config(tmp_path, engine="remote")
    out = tmp_path / "out_override"
    runner = CliRunner()

    result = runner.invoke(
        cli, ["load", "--config", str(cfg), "--engine", "oxigraph", "--out", str(out)]
    )

    assert result.exit_code == 0, result.output
    _assert_result_passed(out)


def test_bad_config_one_version_exits_2(tmp_path):
    cfg = _write_config(tmp_path, engine="oxigraph", versions=1)
    runner = CliRunner()

    result = runner.invoke(
        cli, ["load", "--config", str(cfg), "--engine", "oxigraph", "--out", str(tmp_path / "x")]
    )

    assert result.exit_code == 2


def test_report_flag_prints_fallback_message(tmp_path):
    cfg = _write_config(tmp_path, engine="oxigraph")
    out = tmp_path / "out_report"
    runner = CliRunner()

    result = runner.invoke(
        cli, ["load", "--config", str(cfg), "--engine", "oxigraph", "--out", str(out), "--report"]
    )

    assert result.exit_code == 0, result.output
    assert "eds4jinja2" in result.output
    _assert_result_passed(out)
