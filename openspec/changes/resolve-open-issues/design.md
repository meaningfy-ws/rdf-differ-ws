# PLAN — design (resolve-open-issues)

> EPIC: resolve-open-issues. PLAN ≡ this design + `tasks.md`. Clarity gate ≥9/10.

## Capability 1 — cli-diff-orchestration (`infra/scripts/rdf-differ.sh`)

**#132.** `create_diff()` posts `/diffs` and parses the response. Today it discards the
response and calls a separate helper that GETs `/tasks/active` and takes `.[0].id`. The
create response already carries the Celery task id under `uid`.

- Capture `uid` from the `POST /diffs` JSON (`jq -r '.uid'`).
- If absent/null → print a clear error and exit non-zero (don't fall back to active[0]).
- `wait_for_task "${uid}" "diff"` against `/tasks/{uid}` (helper already exists).
- Delete the `get-active-task-and-take-index-0` path for the diff flow.

**#133 (CLI side).** Before any curl, probe the API base URL once
(`curl -fsS --max-time 5 "${BASE_URL}/diffs"` or a `/health`-style GET). On failure,
print `❌ RDF Differ API not reachable at ${BASE_URL}` and exit non-zero.

**Verification.** `bash -n` syntax check + a `bats`-free shell test is overkill; instead a
small Python/pytest test that runs the script against a stub HTTP server, OR — lazy — a
focused unit asserting the script greps `uid` and polls `/tasks/${uid}` (string/contract
check). Pragmatic: assert the script no longer contains `tasks/active` in the diff path
and does poll `/tasks/${uid}` with the captured id.

## Capability 2 — query-profiling (`query_profiler.py`)

**#134.** Replace the `with ThreadPoolExecutor(...) as executor:` block in `run_queries`
with manual lifecycle:

```python
executor = ThreadPoolExecutor(max_workers=1)
future = executor.submit(execute_query, query_text)
try:
    future.result(timeout=timeout)
except FuturesTimeoutError:
    future.cancel()
    executor.shutdown(wait=False, cancel_futures=True)  # ponytail: orphan thread dies with process
    ...record TIMEOUT...
    continue
...
else:
    ...record SUCCESS...
executor.shutdown(wait=False)
```

On the success/fail paths the thread has finished, so `shutdown(wait=False)` is immediate.
On timeout we do **not** wait — the CLI returns now. `cancel_futures` needs py3.9+ (we are
3.12). 

**#133 (profiler side).** Add a reachability probe of the Fuseki endpoint in `main()`
before profiling (a cheap `ASK {}` via the adapter or an HTTP GET on the endpoint root).
On failure: clear stderr message + return non-zero, before any per-query work.

**#135.** README section: what `query_profiler` is for, how to run it
(`poetry run python -m rdf_differ.diffing.entrypoints.query_profiler <profile> [old new]`),
key flags (`--timeout`, `--csv-output`, `--create-delta-graphs`, `--endpoint`), and exit
codes. Recover the context from closed PR #129.

**Verification.** Existing `tests/unit/test_query_profiler*.py` + new tests: a fake
`execute_query` that blocks on an `Event` proves `run_queries` returns within ~timeout and
records `TIMEOUT` without blocking; a fake adapter whose probe fails proves `main()` exits
non-zero early.

## Capability 3 — diff-semantics (`updated_property_*.rq`)

The pairing filter today:

```sparql
FILTER( lang(?oldValue) = lang(?newValue) && ?oldValue != ?newValue )
```

Replace with a filter that pairs old/new for the **same instance+property** when EITHER
the tags match (existing same-language value change) OR the lexical text matches (#142,
pure tag change) OR exactly one side is a literal (#143, datatype↔object), while never
pairing identical values:

```sparql
FILTER(
  ?oldValue != ?newValue
  && (
       lang(?oldValue) = lang(?newValue)        # same tag, changed text (existing behaviour)
    || str(?oldValue) = str(?newValue)          # #142: same text, changed/removed tag
    || ( isLiteral(?oldValue) != isLiteral(?newValue) )  # #143: literal <-> IRI
  )
)
```

This keeps pairing bounded (no cross-language cartesian noise beyond the deliberate cases)
because old/new are already constrained to the same instance+property and to the
deletions/insertions graphs.

**Filters are NOT uniform across the 149 files** (some profiles use a richer multi-case
filter). The transform must:
1. Find every `updated_property_*.rq` whose final FILTER matches the simple
   `lang(?oldValue) = lang(?newValue)` form and replace it with the relaxed form.
2. For any file with a divergent filter shape, handle explicitly (read + edit) rather than
   blind-sed. Report counts of replaced vs skipped.

**Verification (the gate, DEC-3).** A new `tests/unit/test_diff_semantics_queries.py`:
- Builds a minimal in-memory `rdflib.Dataset` mirroring the skos-history layout
  (version-history graph with the dsv/sh/dct metadata, old/new version graphs,
  insertions/deletions graphs) for `skos:prefLabel`.
- Runs the actual `updated_property_concept_pref_label.rq` text.
- Asserts the language-tag change row (#142) and the literal→IRI row (#143) are returned,
  and that an unchanged value is not.
If rdflib cannot execute a given query construct, fall back to asserting the corrected
FILTER is present in the templates and flag the integration-test gap honestly in the PR.

## Cross-cutting

- Architecture: all changes live in `entrypoints`/`adapters`/resources/infra — no layer
  inversion. `make check-architecture` must stay green.
- Release: bump VERSION + pyproject to `2.2.0`, changelog entry, GitHub release.
