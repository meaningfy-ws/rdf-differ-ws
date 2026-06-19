"""Click CLI entrypoint for the RDF Loading Module (DEC-6).

This is a thin entrypoint: it only parses arguments, reads the YAML config, wires
the composition root (settings + store factory + blank-node strategy + loader),
runs the service flow, and formats output/exit codes. No business logic lives
here. Known domain errors map to stable exit codes (proposal.md "User-facing
errors"); unexpected errors surface a traceback and exit 1.
"""

import sys
from pathlib import Path

import click
import yaml

from rdf_differ.loader.adapters.graph_store import GraphStoreError
from rdf_differ.loader.adapters.graph_store_provider import build_graph_store
from rdf_differ.loader.adapters.settings import StoreSettings
from rdf_differ.loader.adapters.skolemizer import strategy_for
from rdf_differ.loader.domain.model import (
    ConfigError,
    Engine,
    GraphLoadError,
    UnsupportedFormatError,
    ValidationError,
    build_version_store_config,
)
from rdf_differ.loader.services.diff_service import write_artifacts
from rdf_differ.loader.services.loader import VersionStoreLoader, validate_store

# Domain exception → CLI exit code (proposal.md "User-facing errors").
_EXIT_CODES: dict[type[Exception], int] = {
    ConfigError: 2,
    UnsupportedFormatError: 2,
    GraphLoadError: 3,
    GraphStoreError: 4,
    ValidationError: 5,
}

_IN_MEMORY_ENGINES = {Engine.OXIGRAPH, Engine.RDFLIB}


@click.group()
def cli() -> None:
    """rdf-diff command-line interface."""


@cli.command("load")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the YAML load/diff configuration.",
)
@click.option(
    "--engine",
    "engine_name",
    type=click.Choice([e.value for e in Engine]),
    default=None,
    help="Override the store engine declared in the config.",
)
@click.option(
    "--report",
    is_flag=True,
    default=False,
    help="Render the in-memory full report (requires the eds4jinja2 enhancement).",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(file_okay=False),
    default=None,
    help="Directory for in-memory diff artifacts (in-memory engines only).",
)
@click.option(
    "--endpoint",
    "endpoint",
    default=None,
    help="Override the remote store base endpoint (remote engine only).",
)
def load(
    config_path: str,
    engine_name: str | None,
    report: bool,
    out_dir: str | None,
    endpoint: str | None,
) -> None:
    """Load versions and build the skos-history four-graph delta store."""
    try:
        _run_load(config_path, engine_name, report, out_dir, endpoint)
    except tuple(_EXIT_CODES) as exc:
        click.echo(str(exc), err=True)
        sys.exit(_EXIT_CODES[type(exc)])
    except Exception:
        raise


def _run_load(
    config_path: str,
    engine_name: str | None,
    report: bool,
    out_dir: str | None,
    endpoint: str | None,
) -> None:
    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    if engine_name is not None:
        data = {**data, "engine": engine_name}
    config = build_version_store_config(data)

    settings = _build_settings(endpoint)
    store = build_graph_store(config.engine, settings)
    strategy = strategy_for(config.blank_node_policy, base_iri=config.scheme_uri or "")

    loader = VersionStoreLoader(
        store, blank_node_strategy=strategy, query_endpoint=settings.query_endpoint
    )
    result = loader.run(config)
    validate_store(config, store)

    if config.engine in _IN_MEMORY_ENGINES:
        out = out_dir or "."
        write_artifacts(store, config, result, out)
        click.echo((Path(out) / "result.json").read_text(encoding="utf-8"))
    else:
        click.echo(result.model_dump_json(indent=2))

    if report:
        click.echo(
            "in-memory reporting requires the eds4jinja2 enhancement and is not yet "
            "available; diff artifacts were still produced (DEC-5 fallback)."
        )


def _build_settings(endpoint: str | None) -> StoreSettings:
    if endpoint is None:
        return StoreSettings()
    return StoreSettings(
        data_endpoint_override=f"{endpoint}/data",
        update_endpoint_override=f"{endpoint}/update",
        query_endpoint_override=f"{endpoint}/query",
    )
