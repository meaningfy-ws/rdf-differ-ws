"""Command line entry point for profiling SPARQL queries."""

from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import defaultdict
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urljoin

import requests

from rdf_differ import config
from rdf_differ.adapters.diff_adapter import FusekiDiffAdapter, FusekiException
from rdf_differ.adapters.skos_history_wrapper import SKOSHistoryRunner
from rdf_differ.adapters.sparql import SPARQLRunner
from rdf_differ.utils.file_utils import INPUT_MIME_TYPES

DEFAULT_TIMEOUT = 60


@dataclass
class QueryRunResult:
    """Container for storing details about one query execution."""

    file_path: Path
    query: str
    status: str
    duration: float | None = None
    error: str | None = None


def discover_query_files(profile_name: str) -> list[Path]:
    """Return all query files for the given application profile."""

    profile_root = Path(config.APPLICATION_PROFILES_ROOT_FOLDER) / profile_name
    queries_dir = profile_root / "queries"

    if not queries_dir.exists() or not queries_dir.is_dir():
        raise FileNotFoundError(
            f"Profile '{profile_name}' does not contain a 'queries' directory at {queries_dir}."
        )

    query_files = sorted(path for path in queries_dir.glob("*.rq") if path.is_file())

    if not query_files:
        raise FileNotFoundError(f"No SPARQL query files found in {queries_dir}.")

    return query_files


def run_queries(
    query_files: Iterable[Path],
    execute_query: Callable[[str], None],
    timeout: float,
    printer: Callable[[str], None] = print,
    timer: Callable[[], float] = time.perf_counter,
) -> list[QueryRunResult]:
    """Execute each query and collect profiling information."""

    results: list[QueryRunResult] = []

    for query_path in query_files:
        query_text = query_path.read_text(encoding="utf-8")
        printer(f"Executing {query_path.name} ...")
        start_time = timer()
        result = QueryRunResult(file_path=query_path, query=query_text, status="PENDING")

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(execute_query, query_text)

            try:
                future.result(timeout=timeout)
            except FuturesTimeoutError:
                future.cancel()
                result.status = "TIMEOUT"
                result.duration = None
                result.error = f"Timed out after {timeout} seconds"
                printer(f"  -> TIMEOUT after {timeout} seconds")
            except Exception as exc:  # pragma: no cover - defensive
                result.status = "FAILED"
                result.duration = None
                result.error = str(exc)
                printer(f"  -> FAILED ({exc})")
            else:
                end_time = timer()
                duration = end_time - start_time
                result.status = "SUCCESS"
                result.duration = duration
                printer(f"  -> {duration:.3f}s")

        results.append(result)

    return results


def summarise_results(results: Iterable[QueryRunResult]) -> dict:
    """Build basic statistics for the profiled queries."""

    items = list(results)
    completed = [item for item in items if item.duration is not None]

    summary: defaultdict[str, object] = defaultdict(lambda: None)

    summary["query_count"] = len(items)

    if completed:
        total_time = sum(item.duration for item in completed if item.duration is not None)
        summary["total_time"] = total_time
        summary["average_time"] = total_time / len(completed)
        summary["longest"] = max(completed, key=lambda item: item.duration or -1)
        summary["shortest"] = min(completed, key=lambda item: item.duration or float("inf"))
    else:
        summary["total_time"] = 0.0
        summary["average_time"] = None
        summary["longest"] = None
        summary["shortest"] = None

    return dict(summary)


def export_results_to_csv(results: Iterable[QueryRunResult], destination: Path) -> None:
    """Persist profiling results to a CSV file."""

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["query_file", "status", "query_time_seconds", "query"])

        for item in results:
            duration = "" if item.duration is None else f"{item.duration:.6f}"
            writer.writerow([item.file_path.name, item.status, duration, item.query])


def ensure_dataset_exists(adapter: FusekiDiffAdapter, dataset_name: str) -> None:
    """Create the dataset if it is not already present."""

    try:
        if dataset_name in adapter.list_datasets():
            return
    except FusekiException:
        # fall through to attempt creation
        pass

    try:
        adapter.create_dataset(dataset_name)
    except FusekiException as exc:
        if "already exists" not in str(exc):
            raise


def _guess_content_type(file_path: Path) -> str:
    return INPUT_MIME_TYPES.get(file_path.suffix.lstrip(".").lower(), "application/octet-stream")


def upload_file_to_dataset(endpoint: str, dataset_name: str, file_path: Path) -> None:
    """Upload a file to the dataset default graph."""

    url = urljoin(endpoint.rstrip("/"), f"{dataset_name}/data")
    headers = {"Content-Type": _guess_content_type(file_path)}

    with file_path.open("rb") as handle:
        response = requests.post(
            url,
            params={"default": ""},
            data=handle,
            headers=headers,
            auth=requests.auth.HTTPBasicAuth(
                config.RDF_DIFFER_FUSEKI_USERNAME, config.RDF_DIFFER_FUSEKI_PASSWORD
            ),
        )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Failed to upload '{file_path}' to dataset '{dataset_name}' (status {response.status_code})."
        )


def create_delta_graphs(
    endpoint: str,
    dataset_name: str,
    dataset_uri: str,
    old_file: Path,
    new_file: Path,
    old_version_id: str,
    new_version_id: str,
) -> None:
    """Execute the SKOS History wrapper to generate delta graphs."""

    with TemporaryDirectory() as temp_dir:
        runner = SKOSHistoryRunner(
            dataset=dataset_name,
            scheme_uri=dataset_uri,
            old_version_file=str(old_file),
            new_version_file=str(new_file),
            old_version_id=old_version_id,
            new_version_id=new_version_id,
            basedir=temp_dir,
            endpoint=endpoint,
        )
        runner.run()


def parse_arguments(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile SPARQL queries for a given application profile."
    )

    parser.add_argument("profile", help="Name of the application profile to profile")
    parser.add_argument("old_file", nargs="?", help="Optional old RDF version to preload")
    parser.add_argument("new_file", nargs="?", help="Optional new RDF version to preload")
    parser.add_argument(
        "--endpoint",
        default=config.RDF_DIFFER_FUSEKI_SERVICE,
        help="Fuseki service endpoint (default: %(default)s)",
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="Dataset name to use for profiling (defaults to the profile name)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="Timeout in seconds for each query (default: %(default)s)",
    )
    parser.add_argument("--csv-output", help="Optional CSV file to store profiling information")
    parser.add_argument(
        "--create-delta-graphs",
        action="store_true",
        help="Use the SKOS History wrapper to generate delta graphs before profiling",
    )
    parser.add_argument(
        "--dataset-uri",
        default="http://example.com/dataset",
        help="Dataset URI used when generating delta graphs",
    )
    parser.add_argument(
        "--old-version-id",
        default="old",
        help="Old version identifier used when generating delta graphs",
    )
    parser.add_argument(
        "--new-version-id",
        default="new",
        help="New version identifier used when generating delta graphs",
    )

    return parser.parse_args(args=args)


def main(cli_args: list[str] | None = None) -> int:  # noqa: C901  TODO: decompose the CLI flow
    args = parse_arguments(cli_args)

    dataset_name = args.dataset or args.profile.replace(" ", "_")
    endpoint = args.endpoint.rstrip("/")

    try:
        query_files = discover_query_files(args.profile)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    adapter = FusekiDiffAdapter(endpoint, requests, SPARQLRunner())

    try:
        ensure_dataset_exists(adapter, dataset_name)
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"Failed to ensure dataset exists: {exc}", file=sys.stderr)
        return 1

    old_file = Path(args.old_file) if args.old_file else None
    new_file = Path(args.new_file) if args.new_file else None

    if args.create_delta_graphs and (not old_file or not new_file):
        print("--create-delta-graphs requires both old and new files", file=sys.stderr)
        return 1

    if old_file and not old_file.exists():
        print(f"Old file '{old_file}' does not exist", file=sys.stderr)
        return 1

    if new_file and not new_file.exists():
        print(f"New file '{new_file}' does not exist", file=sys.stderr)
        return 1

    if args.create_delta_graphs and old_file and new_file:
        print("Generating delta graphs using SKOS History ...")
        try:
            create_delta_graphs(
                endpoint,
                dataset_name,
                args.dataset_uri,
                old_file,
                new_file,
                args.old_version_id,
                args.new_version_id,
            )
        except Exception as exc:  # pragma: no cover - depends on external tool
            print(f"Failed to generate delta graphs: {exc}", file=sys.stderr)
            return 1
    else:
        for file_path in filter(None, [old_file, new_file]):
            try:
                upload_file_to_dataset(endpoint, dataset_name, file_path)
                print(f"Uploaded {file_path} to dataset '{dataset_name}'.")
            except Exception as exc:  # pragma: no cover - network dependent
                print(f"Failed to upload {file_path}: {exc}", file=sys.stderr)
                return 1

    def execute(query_text):
        return adapter.execute_query(dataset_name=dataset_name, sparql_query=query_text)

    print("Starting query profiling...")
    results = run_queries(query_files, execute, timeout=args.timeout)

    summary = summarise_results(results)

    print("\nProfiling summary:")
    print(f"  Profile: {args.profile}")
    print(f"  Dataset: {dataset_name}")
    print(f"  Endpoint: {endpoint}")
    print(f"  Queries ran: {summary.get('query_count', 0)}")
    if old_file:
        print(f"  Old file: {old_file}")
    if new_file:
        print(f"  New file: {new_file}")

    total_time = summary.get("total_time")
    if total_time is not None:
        print(f"  Total time: {total_time:.3f}s")

    avg_time = summary.get("average_time")
    if avg_time is not None:
        print(f"  Average time: {avg_time:.3f}s")
    else:
        print("  Average time: N/A")

    longest = summary.get("longest")
    if longest:
        print(f"  Longest query: {longest.file_path.name} ({longest.duration:.3f}s)")
    else:
        print("  Longest query: N/A")

    shortest = summary.get("shortest")
    if shortest:
        print(f"  Shortest query: {shortest.file_path.name} ({shortest.duration:.3f}s)")
    else:
        print("  Shortest query: N/A")

    if args.csv_output:
        try:
            export_results_to_csv(results, Path(args.csv_output))
        except Exception as exc:  # pragma: no cover - filesystem errors rare
            print(f"Failed to write CSV output: {exc}", file=sys.stderr)
            return 1
        else:
            print(f"  CSV report written to {args.csv_output}")

    failures = [item for item in results if item.status != "SUCCESS"]
    if failures:
        print(f"\nCompleted with {len(failures)} non-successful queries.")
        return 2

    print("\nAll queries executed successfully.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI hook
    sys.exit(main())
