# PLAN — tasks (EPIC: report-delivery-ux)

Golden thread: restores the report build→discover→serve loop lost in the 2.2.0 FastAPI rewrite.

## T1 — api-client
- [ ] T1.1 Add `get_task(task_id) -> ApiResult` (GET `/tasks/{task_id}`).

## T2 — UI routes (`ui/routes.py`)
- [ ] T2.1 `build_report`: thread the API `task_id` into a redirect `?building=&ap=&tt=`.
- [ ] T2.2 `view_dataset`: accept optional `building`/`ap`/`tt`, pass to template.
- [ ] T2.3 New `task_status` proxy route `GET /tasks/{id}/status` → JSON `{status}`.
- [ ] T2.4 New `view_report` route serving the report **inline** (HTML renders, JSON/ASCII shown).

## T3 — Templates (`dataset/view_dataset.html`)
- [ ] T3.1 Per-variant **View** (new tab) + **Download** actions in the available-reports list.
- [ ] T3.2 Building banner + dependency-free bounded poller that refreshes on completion.

## T4 — Tests
- [ ] T4.1 Unit: build redirect carries building params; view renders banner; status proxy; inline view; list links. (TDD)
- [ ] T4.2 BDD: `tests/features/report_delivery.feature` + steps (happy, edge=build fails, negative=missing report).
- [ ] T4.3 `make check-quality` / `check-architecture` / `test-unit` green.

## T5 — Docs
- [ ] T5.1 README: document viewing vs downloading a report and the completion behaviour.
