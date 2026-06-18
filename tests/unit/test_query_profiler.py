import time
from pathlib import Path

import pytest

from rdf_differ.entrypoints.query_profiler import (
    QueryRunResult,
    discover_query_files,
    export_results_to_csv,
    run_queries,
    summarise_results,
)


def test_discover_query_files(tmp_path, monkeypatch):
    profile_root = tmp_path / "example" / "queries"
    profile_root.mkdir(parents=True)
    file_a = profile_root / "a.rq"
    file_b = profile_root / "b.rq"
    file_a.write_text("SELECT * WHERE { ?s ?p ?o }")
    file_b.write_text("ASK { ?s ?p ?o }")

    monkeypatch.setattr(
        "rdf_differ.entrypoints.query_profiler.config.APPLICATION_PROFILES_ROOT_FOLDER",
        tmp_path,
    )

    files = discover_query_files("example")

    assert files == [file_a, file_b]


def test_run_queries_records_statuses(tmp_path):
    query_a = tmp_path / "a.rq"
    query_b = tmp_path / "b.rq"
    query_c = tmp_path / "c.rq"
    query_a.write_text("SELECT * WHERE { ?s ?p ?o }")
    query_b.write_text("ASK { ?s ?p ?o }")
    query_c.write_text("CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }")

    calls = []

    def executor(query_text: str) -> None:
        calls.append(query_text)
        if query_text == query_b.read_text():
            raise ValueError("boom")

    timer_values = iter([0.0, 0.2, 0.5, 0.8, 1.0])

    def fake_timer():
        return next(timer_values)

    messages = []
    results = run_queries(
        [query_a, query_b, query_c],
        executor,
        timeout=5,
        printer=messages.append,
        timer=fake_timer,
    )

    assert [item.status for item in results] == ["SUCCESS", "FAILED", "SUCCESS"]
    assert pytest.approx(results[0].duration, rel=1e-3) == 0.2
    assert results[1].duration is None
    assert pytest.approx(results[2].duration, rel=1e-3) == 0.2
    assert len(calls) == 3
    assert any("FAILED" in message for message in messages)


def test_run_queries_timeout_marks_result(tmp_path):
    query_path = tmp_path / "slow.rq"
    query_path.write_text("SELECT * WHERE { ?s ?p ?o }")

    def slow_executor(_: str) -> None:
        time.sleep(0.05)

    result = run_queries([query_path], slow_executor, timeout=0.001)[0]

    assert result.status == "TIMEOUT"
    assert result.duration is None


def test_summarise_results_handles_statistics():
    results = [
        QueryRunResult(Path("a.rq"), "queryA", "SUCCESS", duration=0.2),
        QueryRunResult(Path("b.rq"), "queryB", "FAILED"),
        QueryRunResult(Path("c.rq"), "queryC", "SUCCESS", duration=0.4),
    ]

    summary = summarise_results(results)

    assert summary["query_count"] == 3
    assert pytest.approx(summary["total_time"], rel=1e-3) == 0.6
    assert pytest.approx(summary["average_time"], rel=1e-3) == 0.3
    assert summary["longest"].file_path.name == "c.rq"
    assert summary["shortest"].file_path.name == "a.rq"


def test_export_results_to_csv(tmp_path):
    destination = tmp_path / "report.csv"
    results = [
        QueryRunResult(Path("a.rq"), "SELECT", "SUCCESS", duration=0.25),
        QueryRunResult(Path("b.rq"), "ASK", "FAILED"),
    ]

    export_results_to_csv(results, destination)

    content = destination.read_text().splitlines()
    assert content[0].startswith("query_file")
    assert "a.rq" in content[1]
    assert "0.25" in content[1]
