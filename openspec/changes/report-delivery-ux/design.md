# PLAN — design (report-delivery-ux)

> EPIC: report-delivery-ux. PLAN ≡ this design + `tasks.md`.

## Current flow (what works, what's missing)

```
build form ──POST /diffs/{id}──> api_client.build_report ──POST /diffs/report──> API enqueues
   Celery async_generate_report ──> writes {reports_db}/{name}/{ap}/{type}/<file>   [WORKS]
GET /diffs/{id} ──> get_diff sets dataset.available_reports = get_all_reports(...)   [WORKS]
view_dataset template ──> renders Download links per variant                          [WORKS]
download_report ──> streams file as attachment                                        [WORKS]
        ^
        └── MISSING: nothing tells the user the build finished; no live view.
```

The API returns `{"task_id": ..., "application_profile": ...}` from `POST /diffs/report`, and
`GET /tasks/{id}` returns `{"task_id","status","result"}`. Both already exist.

## Changes (UI entrypoint only)

### 1. `api_client.py`
- Add `get_task(task_id) -> ApiResult` → `_request("GET", f"/tasks/{task_id}")`.
- (Reuse the existing `build_report`, which returns an `ApiResult` whose `.json` carries
  `task_id`, and `get_report`, which returns the raw bytes response.)

### 2. `ui/routes.py`
- **`build_report`**: on success read `task_id = result.json.get("task_id")` and redirect to
  `view_dataset` with query params `?building=<task_id>&ap=<ap>&tt=<tt>` (keep the flash).
- **`view_dataset`**: accept optional `building`, `ap`, `tt` query params and pass them to the
  template so it can show the banner + poller.
- **New `task_status` route** `GET /tasks/{task_id}/status` (name `task_status`): proxy
  `api_client.get_task(task_id)` → return `JSONResponse({"status": ...})` (404/503 surfaced as
  a status string the poller can handle). Same-origin so the browser fetch needs no CORS.
- **New `view_report` route** `GET /diff-report/{dataset_id}/{ap}/{tt}/view` (name
  `view_report`): call `api_client.get_report(...)`; if 200 return `Response(content=bytes,
  media_type=<from upstream content-type>, headers={"content-disposition": "inline"})`; else
  flash + redirect (mirror `download_report`'s error handling). This makes the browser render
  the HTML live / show JSON/ASCII.

### 3. Templates (`dataset/view_dataset.html`)
- **Available reports list**: for each `variant`, render **View** (→ `view_report`, `target="_blank"`)
  and **Download** (→ `download_report`) actions per row.
- **Building banner**: when `building` is set, show "⏳ Building `{{ap}}` · `{{tt}}` report…" and
  a `<script>` poller: every 3s `fetch('/tasks/{building}/status')`; on `SUCCESS` →
  `location.replace(view_dataset url without query)` (report now listed) and surface a
  "ready" prompt; on `FAILED`/`ERROR` → replace banner with an error; bounded to ~100 polls
  then show "still building — refresh later". Dependency-free vanilla JS, consistent with the
  existing template-type dropdown script.

## Verification

- **Unit (UI routes, Flask/Starlette test client)** — see existing `tests/unit/test_ui_routes.py`:
  - `build_report` success redirects with `building`/`ap`/`tt` query params (task_id threaded).
  - `view_dataset` with `?building=...` renders the banner + poller markup.
  - `task_status` returns the upstream status JSON; degrades to a status string on API error.
  - `view_report` returns the report bytes with an **inline** disposition and the right
    media type for 200; flashes + redirects when the report is missing.
  - Report list renders both View and Download links per variant.
- **BDD** — `tests/features/report_delivery.feature` + steps in `tests/feature/`: build → see
  building state → on completion the report is listed and can be viewed inline or downloaded;
  edge (build fails → error shown); negative (view a non-existent report → friendly redirect).
- Quality gate: `make check-quality`, `make check-architecture`, `make test-unit` green.

## Risks

- **Self-contained HTML** confirmed for current templates (inline style, remote-only refs). If a
  template later emits local assets, the single-file inline view loses styling → DEC-4 escalation.
- **Poller** must stop on terminal states and cap total polls so a stuck task doesn't spin forever
  (mirrors the bash `wait_for_task` bound added for #133).
