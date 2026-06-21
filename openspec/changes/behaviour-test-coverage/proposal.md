# EPIC: Project-wide behaviour-test coverage (Gherkin) for the RDF Differ capabilities

> A dedicated testing EPIC. It inventories what RDF Differ does and pins that behaviour with
> **Gherkin features + pytest-bdd step definitions** covering happy paths, edge cases, and negative
> paths across the main capabilities. It changes **test code only** — no production behaviour.

## Appetite

**Medium, and bounded by "infra-free first".** The bulk of the value — loading RDF + computing diffs
(in-memory engines), building/inspecting reports (file-based application profiles), the web UI
(FastAPI `TestClient`), and the CLI (`CliRunner`) — needs **no running infrastructure** and lands as
fast, deterministic tests. The thin slice that genuinely needs Fuseki/Redis/Celery (the remote diff
pipeline) is written too but tagged `@integration` so it is opt-in and never blocks the default run.
Features land capability by capability, always green.

## Why

RDF Differ has accreted behaviour across five capabilities (loading, diffing, reporting, API, UI,
CLI) with **uneven** test coverage: the loader and OWL diff have BDD features, but reporting, the
new FastAPI UI, the CLI, and most **negative/edge** paths are only covered ad-hoc or not at all.
Without executable behaviour specs, the migration (FastAPI) and the in-flight loader rewrite risk
silent regressions, and "what is this system supposed to do?" has no single, runnable answer.

A behaviour suite written against the **existing test data** (`tests/test_data/`) and **existing
application profiles** (`tests/test_data/sample_ap_config/`, `resources/`) gives us: a living
specification, regression protection for both modernization epics, and confidence to merge + release.

## Solution outline (Description)

Author Gherkin features under `tests/features/` and step definitions under `tests/feature/`
(matching the existing pytest-bdd layout), grouped by capability. Each feature covers **happy path +
edge cases + negative paths**. Use the existing fixtures and test data; add small fixtures only where
needed. Marker injection by path already tags `tests/feature/` as `feature`; service-dependent
scenarios additionally carry `@integration`.

**Capabilities and the behaviour to pin:**

1. **RDF loading & diff computation (in-memory, no infra).** Using `loader.services.diff_service`
   (`build_diff_config` + `create_version_diff`) with the `rdflib` and `pyoxigraph` engines over
   real files in `tests/test_data/` (owl, shacl, eurovoc): load two versions; compute
   insertions/deletions; assert delta counts/contents. Edge: identical versions → empty delta;
   blank-node handling. Negative: missing/unreadable file; mismatched file formats.

2. **Reporting (file-based, no infra).** Using `reporting.services.ap_manager` over
   `tests/test_data/sample_ap_config` and the bundled profiles: list application profiles, list
   template variants, resolve the template/queries folders, build the queries dict. Negative:
   unknown application profile, unknown template type, missing queries folder.

3. **Web UI (FastAPI `TestClient`, no infra).** Behaviour over the running ASGI app with the
   `api_client` mocked: list diffs; create-diff happy path → redirect to tasks; validation errors
   re-render with messages; an API error becomes a flash (not a 500); CSRF-less POST is rejected;
   view a dataset; report download success/failure; revoke a task.

4. **REST API (FastAPI `TestClient`, no infra).** Behaviour over the API with services mocked: the
   diff/report/task endpoints' success + error status codes; the problem-style error body; OpenAPI
   is served. (Complements the unit-level route tests with journey-level scenarios.)

5. **CLI (`CliRunner`, no infra with the in-memory engine).** `rdf-diff load` happy path against an
   in-memory engine + a temp out-dir produces the artifacts; negative: bad arguments, missing file.

6. **Remote diff pipeline (`@integration`, needs infra).** A thin end-to-end: create a diff via the
   API against a live Fuseki/Redis/Celery stack and poll the task — opt-in, documented, never in the
   default run.

A short **coverage inventory** (what exists vs. what this epic adds) is maintained in `design.md` so
gaps are visible.

## Key decisions

- **DEC-1 — Infra-free by default.** Every feature runs with `make test-unit`/`test-feature` and no
  services, except those explicitly tagged `@integration`.
- **DEC-2 — Use existing data & profiles.** No new large fixtures; reuse `tests/test_data/` and the
  bundled application profiles. Small inline fixtures only.
- **DEC-3 — pytest-bdd in the existing layout.** Features in `tests/features/`, steps in
  `tests/feature/`; reuse `tests/feature/conftest.py` fixtures; marker-by-path stays.
- **DEC-4 — Happy + edge + negative for each capability.** A feature without a negative scenario is
  incomplete.
- **DEC-5 — No gratuitous production changes, but discovered bugs MUST be fixed.** This epic does not
  refactor or alter production behaviour for its own sake. However, when a scenario uncovers a real
  **bug or limitation**, it SHALL be **fixed** (minimal, targeted change + the regression test that
  proves it) — never `xfail`-ed, silenced, or merely deferred to another epic. The fix is committed
  alongside its failing-then-passing test; only a genuinely large fix is split into its own commit,
  but the bug is never left unaddressed. Existing **correct** behaviour stays byte-for-byte unchanged.

## Rabbit-holes (avoided)

- No refactors or feature changes "while we're in there" — production code changes are limited to
  fixing the specific bug/limitation a test uncovered (DEC-5), with its regression test.
- No browser/e2e (Playwright) — out of scope; `tests/e2e/` stays opt-in.
- The legacy `load_versions.sh` remote pipeline is the `rdf-loading-module` epic's responsibility; the
  remote scenario here is `@integration`. (If a defect is in *this* repo's code rather than that
  pipeline, DEC-5 still applies — fix it.)

## No-gos

- **No gratuitous production behaviour changes** — but a discovered bug or limitation is fixed, not
  worked around (DEC-5). Existing *correct* behaviour is preserved exactly.
- **No new heavyweight fixtures or test data** committed to the repo.
- **No coupling of the default test run to infrastructure.**
- **No duplication** of scenarios already covered by existing features — extend, don't copy.

## Out of scope (future)

Browser e2e, performance/load testing, and mutation testing.
