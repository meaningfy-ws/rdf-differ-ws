# PLAN — tasks (EPIC: resolve-open-issues)

Golden thread: every task traces to an issue and a capability spec under `specs/`.

## T1 — cli-diff-orchestration (#132, #133-cli) — `infra/scripts/rdf-differ.sh`
- [x] T1.1 Capture `uid` from `POST /diffs`; error+exit if missing (no active[0] fallback).
- [x] T1.2 Poll `/tasks/${uid}` via existing `wait_for_task`; remove active-task path in diff flow.
- [x] T1.3 Pre-flight API reachability probe; clear error + non-zero exit if down.
- [x] T1.4 `bash -n` clean; contract test asserts uid-polling, no `tasks/active` in diff path.

## T2 — query-profiling code (#134, #133-profiler) — `query_profiler.py`
- [x] T2.1 (TDD) Test: blocking query returns within ~timeout, records TIMEOUT, no hang.
- [x] T2.2 Manual executor lifecycle + `shutdown(wait=False, cancel_futures=True)` on timeout.
- [x] T2.3 (TDD) Test: unreachable Fuseki → `main()` exits non-zero before per-query work.
- [x] T2.4 Endpoint reachability probe in `main()`.

## T3 — query-profiling docs (#135) — `README.md`
- [x] T3.1 README section: purpose, invocation, flags, exit codes (recover PR #129 context).

## T4 — diff-semantics (#142, #143) — `updated_property_*.rq`
- [x] T4.1 (TDD, the gate) rdflib test proving tag-change + literal↔IRI surface as updates.
- [x] T4.2 Relax the pairing FILTER across all `updated_property_*.rq` (handle non-uniform forms).
- [x] T4.3 Report replaced/skipped counts; note dqgen mirror requirement.

## T5 — integrate & release
- [x] T5.1 `make check-quality` / lint / `make check-architecture` green.
- [x] T5.2 `make test-unit` green.
- [x] T5.3 Bump VERSION + pyproject → 2.2.0; CHANGELOG entry.
- [x] T5.4 PR to master; release notes; tag/release 2.2.0.
