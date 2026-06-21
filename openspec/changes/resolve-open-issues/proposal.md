# EPIC — Resolve open GitHub issues (CLI robustness, profiling, diff semantics)

> Shape-Up work shape. EPIC ≡ this proposal. Drives the PLAN (`design.md` + `tasks.md`)
> and the capability specs under `specs/`.

## Appetite

One focused batch — a single feature branch and one minor release (2.1.0 → 2.2.0).
Small-batch appetite: each issue is a self-contained fix verifiable without a full
docker stack.

## Why (the bet)

Six issues are open against rdf-differ. They cluster into three capabilities and share
one theme: **the tooling around the diff lies about what it did** — it waits on the wrong
task, fails to stop on timeout, runs blind against down services, and silently drops two
classes of RDF change. Closing them makes the CLI and reports trustworthy.

| # | Title | Capability |
|---|-------|------------|
| 132 | Wait for the wrong diff task (P1) | cli-diff-orchestration |
| 134 | Timeout does not stop blocked query (P1) | query-profiling |
| 133 | Health checks / guards for unavailable services | query-profiling + cli-diff-orchestration |
| 135 | Document the profiling script in README | query-profiling (docs) |
| 142 | Deleted/changed language tag not captured as update | diff-semantics |
| 143 | Datatype→object property change not captured | diff-semantics |

## Solution outline

1. **cli-diff-orchestration** (`infra/scripts/rdf-differ.sh`) — the `diff`/`full` flow
   posts `/diffs`, gets back the task `uid`, then **ignores it** and polls
   `/tasks/active[0]`. Fix: poll `/tasks/{uid}` for the id the create call returned.
   Add a pre-flight health check (API reachable) so the script fails fast with a clear
   message instead of curling a dead endpoint.

2. **query-profiling** (`rdf_differ/diffing/entrypoints/query_profiler.py`) —
   - #134: the per-query `ThreadPoolExecutor` is used as a context manager, so leaving
     the `with` block calls `shutdown(wait=True)` and blocks on the hung thread even
     after a TIMEOUT is recorded. Manage the executor manually and `shutdown(wait=False,
     cancel_futures=True)` on timeout so the CLI returns immediately.
   - #133: pre-flight reachability check of the Fuseki endpoint before profiling; clear
     error and non-zero exit if it is down.
   - #135: document the script (purpose, arguments, examples) in the README.

3. **diff-semantics** (`resources/templates/*/queries/updated_property_*.rq`) —
   the `updated_property` queries pair an old value with a new value only when
   `lang(?oldValue) = lang(?newValue)`. That filter drops:
   - #142: a language-tag change (`@en`→`@fr`) or removal (`@en`→none) — same text,
     different tag — so it is never reported as an update.
   - #143: a datatype→object change (literal → IRI) — never reported as update **and**
     suppressed from added/deleted by the `FILTER NOT EXISTS` guard, so it vanishes.
   Relax the pairing filter to also pair values that share text but differ in tag, and to
   pair a literal with an IRI for the same instance+property, so both surface as updates.
   **Verified with rdflib in-memory SPARQL** against a minimal skos-history fixture — no
   live Fuseki required.

## Key decisions

- **DEC-1** One feature branch (`feature/resolve-open-issues`), one PR, one minor release.
  The issues are independent but small; batching keeps the release legible.
- **DEC-2** #142/#143 are fixed in the committed `.rq` templates (the runtime source of
  truth — there is no in-repo regeneration seam). The upstream **dqgen** generator should
  mirror the same filter change; noted on the issues and in the PR so the two do not drift.
- **DEC-3** Verification gate for the SPARQL change is an **rdflib** test that runs the
  real query against a tiny named-graph dataset and asserts the change now surfaces. No
  unverified mass edit ships.
- **DEC-4** Health checks are **pre-flight reachability probes**, not a service-health
  framework. Lazy scope: one HTTP/SPARQL ping with a clear message.

## Rabbit-holes (time sinks to avoid)

- Rewriting the skos-history diff pipeline or the dqgen template model. Out.
- A generic "type-change" report category for #143 (new query family + template + UI
  wiring). The issue asks only that the change *be captured*; surfacing it as an update is
  sufficient. A distinct category is a separate, larger bet.
- Forcibly killing hung SPARQL threads (process pool, signals). `shutdown(wait=False)`
  returns control to the user; the orphaned thread dies with the process. Good enough for
  a profiling CLI.

## No-gos (explicitly out of scope)

- eds4jinja2 1.x un-vendoring (gated, separate work).
- Wiring the new Python loader into the API (future work).
- Archiving the two completed epics into `openspec/specs/` — interactive spine
  stewardship, run via `/opsx:archive`.
