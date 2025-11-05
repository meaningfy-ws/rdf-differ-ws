import subprocess
import os
import pytest
import json

SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../bash/rdf-differ.sh'))
TESTDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_data/owl'))
OUTDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../diff-output'))
OLD = os.path.join(TESTDIR, 'ePO_sample-4.0.0.orig.ttl')
NEW = os.path.join(TESTDIR, 'ePO_sample-4.0.0.upd.ttl')
PROFILE = 'owl-core-en-only'
BASE_URL = os.environ.get('RDF_DIFFER_BASE_URL', 'http://localhost:4030')

@pytest.mark.integration
def test_full_workflow_json():
    # Run full workflow with JSON template
    result = subprocess.run([
    SCRIPT, '--base-url', BASE_URL, '--old', OLD, '--new', NEW, '--ap', PROFILE, '--template', 'json', '--output', OUTDIR, 'full'
    ], capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}\n{result.stdout}"
    report_file = os.path.join(OUTDIR, 'diff.json')
    assert os.path.isfile(report_file), f"Report file not found: {report_file}"
    with open(report_file) as f:
        content = f.read()
    # Check for expected JSON keys
    data = json.loads(content)
    assert 'dataset_name' in data, "Missing 'dataset_name' in JSON report"
    assert 'application_profile' in data, "Missing 'application_profile' in JSON report"

@pytest.mark.integration
def test_full_workflow_html():
    # Run full workflow with HTML template
    html_file = os.path.join(OUTDIR, 'diff.html')
    result = subprocess.run([
    SCRIPT, '--base-url', BASE_URL, '--old', OLD, '--new', NEW, '--ap', PROFILE, '--template', 'html', '--output', OUTDIR, 'full'
    ], capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}\n{result.stdout}"
    assert os.path.isfile(html_file), f"HTML report file not found: {html_file}"
    with open(html_file) as f:
        content = f.read()
    # Check for expected HTML tags
    assert '<html' in content and '<body' in content, "HTML report missing expected tags"

@pytest.mark.integration
def test_diff_only():
    result = subprocess.run([
    SCRIPT, '--base-url', BASE_URL, '--old', OLD, '--new', NEW, '--ap', PROFILE, 'diff'
    ], capture_output=True, text=True)
    assert result.returncode == 0, f"Diff command failed: {result.stderr}\n{result.stdout}"
    assert 'Dataset ID' in result.stdout, "Diff output missing Dataset ID"

@pytest.mark.integration
def test_list_command():
    result = subprocess.run([SCRIPT, '--base-url', BASE_URL, 'list'], capture_output=True, text=True)
    assert result.returncode == 0, f"List command failed: {result.stderr}\n{result.stdout}"
    assert 'Response' in result.stdout or 'Raw response' in result.stdout, "List output missing expected response"
