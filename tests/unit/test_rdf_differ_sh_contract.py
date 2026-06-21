"""Contract tests for the bash diff CLI ``infra/scripts/rdf-differ.sh``.

Cites EPIC: resolve-open-issues (capability cli-diff-orchestration, issues #132, #133).

These are pure text/contract assertions on the script source — no I/O, no subprocess.
The ``unit`` marker is applied automatically by ``tests/conftest.py`` (by path).
"""
import re
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "infra" / "scripts" / "rdf-differ.sh"


def _read_script() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def _create_diff_body(text: str) -> str:
    """Return the body of the create_diff() bash function."""
    start = text.index("create_diff()")
    # The next top-level function definition marks the end of create_diff().
    end = text.index("generate_report()", start)
    return text[start:end]


def test_script_exists():
    assert SCRIPT_PATH.is_file(), f"missing script: {SCRIPT_PATH}"


def test_diff_flow_captures_uid_from_create_response():
    """#132: the diff flow reads .uid from the POST /diffs response."""
    body = _create_diff_body(_read_script())
    assert re.search(r"jq\s+-r\s+'\.uid'", body), (
        "create_diff must capture the task id via jq -r '.uid'"
    )


def test_diff_flow_polls_tasks_endpoint_with_captured_uid():
    """#132: the captured uid is passed to wait_for_task (which polls /tasks/${id})."""
    text = _read_script()
    body = _create_diff_body(text)
    # Find every variable captured from the create response via jq -r '.uid';
    # at least one of them must be the value we wait on for the "diff" task.
    captured_vars = re.findall(
        r"(\w+)=\$\(echo\s+\"\$\{RESPONSE\}\"\s*\|\s*jq\s+-r\s+'\.uid'\)", body
    )
    assert captured_vars, "expected a variable assigned from jq -r '.uid' on the create response"
    waited = [
        v for v in captured_vars
        if re.search(rf"wait_for_task\s+\"\$\{{{v}\}}\"\s+\"diff\"", body)
    ]
    assert waited, (
        "create_diff must wait_for_task on a uid captured from the create response"
    )
    # And wait_for_task must poll /tasks/${task_id}.
    assert re.search(r"\$\{BASE_URL\}/tasks/\$\{task_id\}", text), (
        "wait_for_task must poll /tasks/${task_id}"
    )


def test_diff_flow_does_not_curl_tasks_active():
    """#132: the discovery path /tasks/active[0] is gone from the create_diff flow."""
    body = _create_diff_body(_read_script())
    # Ignore comments; assert there is no actual request to /tasks/active.
    code_lines = [ln for ln in body.splitlines() if not ln.lstrip().startswith("#")]
    code = "\n".join(code_lines)
    assert "tasks/active" not in code, (
        "create_diff must not query /tasks/active anymore"
    )
    assert ".[0].id" not in code, "create_diff must not take the first active task"


def test_diff_flow_errors_when_uid_missing():
    """#132: a missing/null uid produces a clear error and a non-zero exit."""
    body = _create_diff_body(_read_script())
    assert "Could not determine diff task id" in body
    assert "exit 1" in body


def test_reachability_probe_against_base_url():
    """#133: a single pre-flight probe of ${BASE_URL} exists with a clear failure."""
    text = _read_script()
    assert re.search(r"curl\s+-fsS\s+-m\s+5\s+-o\s+/dev/null\s+\"\$\{BASE_URL\}/diffs\"", text), (
        "expected a cheap reachability probe: curl -fsS -m 5 -o /dev/null \"${BASE_URL}/diffs\""
    )
    assert "RDF Differ API not reachable at ${BASE_URL}" in text
