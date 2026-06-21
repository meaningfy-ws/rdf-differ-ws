# EPIC — Report delivery UX: serve, view and discover built reports

> Shape-Up work shape. EPIC ≡ this proposal. Drives the PLAN (`design.md` + `tasks.md`)
> and the capability spec under `specs/report-delivery/`.

## Appetite

Small batch — one feature branch. UI-layer change plus a thin api-client method; the REST
API and report storage already do everything needed. No new infrastructure.

## Why (the bet)

After the 2.2.0 FastAPI rewrite, a user who builds a report has **no way to tell when it is
ready**: `POST /diffs/{id}` enqueues a Celery task, flashes "Report building started.", and
redirects — but the page does not reflect progress and the freshly-built report only appears
after a *manual* refresh. To the user this reads as "the software does not deliver the basic
functionality." The download route itself works; the **completion signal and a live view are
missing**.

In 2.1.0 the loop was discoverable (documented build → list → download, with screenshots) so
reports "were served well". The rewrite preserved the download route but dropped the feedback
loop. This EPIC restores a trustworthy loop and adds **serving the report live** (the
explicitly preferred option) alongside download.

## Solution outline

Three affordances on the dataset (diff) view, all UI-layer:

1. **Serve/view live (preferred).** A new `view_report` route serves a built report **inline**
   so the browser renders it: HTML reports display as a page, JSON/ASCII show in the browser.
   HTML reports are self-contained (inline `<style>`, only remote/CDN refs), so a single-file
   inline response renders correctly. Each report variant gets a **View** link (opens in a new
   tab) next to the existing **Download** link.

2. **Discover when ready (completion signal).** `build_report` captures the `task_id` the API
   returns and redirects to the dataset view with it. The view shows a "Building `<ap>` ·
   `<type>`…" banner and a small dependency-free poller that hits a same-origin task-status
   endpoint; on success it refreshes so the new report appears (and surfaces a "ready —
   View / Download" prompt); on failure it shows an error. No manual refresh.

3. **List to download (kept, clarified).** The existing per-variant download list stays; each
   row now offers both View and Download, grouped by application profile and template type.

## Key decisions

- **DEC-1** All changes live in the UI entrypoint (`routes.py`, `api_client.py`, templates) +
  one tiny api-client `get_task` call. The REST API (`/diffs/report`, `/tasks/{id}`,
  `/diffs/{id}` with `available_reports`) and report storage are unchanged — they already work.
- **DEC-2** Live view serves the report **inline** by re-serving the bytes the API already
  returns, with `Content-Disposition: inline` and the report's media type. No new API endpoint.
- **DEC-3** Completion is detected by **client-side polling** of a same-origin
  `GET /tasks/{id}/status` UI proxy (3s interval, bounded). Polling, not websockets — lazy,
  no new dependency, matches the existing httpx/SSR stack.
- **DEC-4** Inline view serves the **single built file**. Self-contained HTML confirmed; if a
  future template emits external local assets, escalate to serving the report directory.

## Rabbit-holes (avoid)

- WebSockets / SSE / a task-event bus for push completion. Polling is enough.
- A bundled in-app report viewer/renderer. The browser renders the served file; don't rebuild
  a viewer.
- Reworking report storage layout or the eds4jinja2 build. Out of scope.

## No-gos (explicitly out of scope)

- Changing the REST API contract or the Celery task signatures.
- Auth/access control on report URLs (same posture as today).
- The active-tasks page redesign (task↔report correlation there is a separate, smaller follow-up).
