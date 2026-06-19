import time
from pathlib import Path

from rdf_differ.diffing.entrypoints.query_profiler import (
    QueryRunResult,
    _guess_content_type,
    export_results_to_csv,
    run_queries,
    summarise_results,
)


def test_run_queries_records_success_and_duration(tmp_path):
    query_file = tmp_path / "q1.rq"
    query_file.write_text("SELECT * WHERE {}", encoding="utf-8")
    timer = iter([1.0, 2.5])

    results = run_queries(
        [query_file],
        execute_query=lambda _text: None,
        timeout=5,
        printer=lambda _m: None,
        timer=lambda: next(timer),
    )

    assert len(results) == 1
    assert results[0].status == "SUCCESS"
    assert results[0].duration == 1.5


def test_run_queries_marks_timeout(tmp_path):
    query_file = tmp_path / "q1.rq"
    query_file.write_text("SELECT * WHERE {}", encoding="utf-8")

    results = run_queries(
        [query_file],
        execute_query=lambda _text: time.sleep(0.2),
        timeout=0.01,
        printer=lambda _m: None,
    )

    assert results[0].status == "TIMEOUT"
    assert results[0].duration is None


def test_summarise_results_with_durations():
    fast = QueryRunResult(Path("a.rq"), "q", "SUCCESS", duration=1.0)
    slow = QueryRunResult(Path("b.rq"), "q", "SUCCESS", duration=3.0)

    summary = summarise_results([fast, slow])

    assert summary["query_count"] == 2
    assert summary["total_time"] == 4.0
    assert summary["average_time"] == 2.0
    assert summary["longest"] is slow
    assert summary["shortest"] is fast


def test_summarise_results_empty():
    summary = summarise_results([])
    assert summary["query_count"] == 0
    assert summary["total_time"] == 0.0
    assert summary["average_time"] is None


def test_export_results_to_csv(tmp_path):
    destination = tmp_path / "reports" / "profile.csv"
    export_results_to_csv(
        [QueryRunResult(Path("a.rq"), "SELECT 1", "SUCCESS", duration=1.234567)],
        destination,
    )

    content = destination.read_text(encoding="utf-8")
    assert "query_file,status,query_time_seconds,query" in content
    assert "a.rq,SUCCESS,1.234567,SELECT 1" in content


def test_guess_content_type():
    assert _guess_content_type(Path("data.ttl")) == "text/turtle"
    assert _guess_content_type(Path("data.unknown")) == "application/octet-stream"
