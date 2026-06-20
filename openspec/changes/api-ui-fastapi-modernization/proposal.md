# EPIC: Migrate the API to FastAPI and rebuild the UI (FastAPI + Jinja2 + modern CSS)

> Sibling of `meaningfy-modernization`. This EPIC modernises the **`api` component** (tier 3):
> the REST API entrypoint, the web UI entrypoint, their tests, and the report-rendering dependency.
> It does **not** touch `core`, `diffing`, `reporting` logic, or `loader` — those layers are already
> framework-free and stay as-is. The PLAN (`design.md` + `tasks.md`) is derived from this and gated
> by the clarity gate (≥9/10) before `/opsx:apply`.

## Appetite

**Large, but bounded by a clean seam.** Everything lands in the `api` component's **entrypoint
layer** plus one dependency bump in `reporting`. The domain models, diffing/reporting services, and
all adapters (Fuseki, Redis, Celery, SPARQL) are already framework-free and **do not change** — so
this is a rewrite of *how requests come in and pages go out*, not of *what the system computes*. The
work lands test-first in reviewable TDD slices, always green, as its own PR off
`feature/api-ui-fastapi-modernization`. The eds4jinja2 1.x upgrade is **gated**: if the major release
proves backwards-incompatible for our templates, we stay vendored and ship the rest — never blocked,
never reworked.

## Why

The "API" already runs on **Connexion 3** (ASGI/uvicorn, spec-first OpenAPI), so this is not an
"async upgrade" — it is a deliberate move to the team-standard **code-first FastAPI** stack, and a
chance to pay down real debt that the current surface carries:

- **The API still drags Flask in** (Connexion 3 wraps a Flask app purely for logging) and mixes
  `werkzeug.exceptions` into handlers — coupling the "API" to Flask internals. There are **no
  behaviour tests** for any API flow.
- **The UI is Flask + Jinja + Flask-WTF** with a dated single-stylesheet design. Its API client
  (`api_wrapper.py`) uses bare `requests` with **no timeouts** and **no guard on `.json()`** — a
  non-JSON 500 from the API crashes the UI itself.
- **A live bug:** creating a diff in the UI returns 500, and `views.py` calls `logger.exception(...)`
  with **no active exception**, producing the exact `NoneType: None` noise seen in the logs. The real
  fault is an unhandled error in the API `/diffs` handler path.
- **eds4jinja2 is currently vendored.** Its major **1.x** release (possibly backwards-incompatible)
  lets us un-vendor and pin a real version — removing carried source from the repo.

Doing API + UI **together** is cheaper than separately: they share the request/response contract
(the Pydantic DTOs in `api/domain/model.py`), and a FastAPI API plus a FastAPI-served Jinja UI
**collapse three frameworks (Connexion, Flask×2) into one**.

## Solution outline (Description)

**API — rewrite `entrypoints/api` on FastAPI (DEC-1).** Each handler becomes a FastAPI path
operation with Pydantic request/response models (reusing `api/domain/model.py`). `werkzeug`
exceptions are replaced by `fastapi.HTTPException` + centralised exception handlers that emit the same
problem-style JSON. Connexion and the hand-maintained `openapi/openapi.yaml` go away — FastAPI
generates the OpenAPI and Swagger UI. The Celery/Redis/Fuseki **services and adapters are imported
unchanged**. Flask is removed from the API entirely.

**UI — rebuild `entrypoints/ui` on FastAPI + Jinja2 + modern CSS (DEC-2).** Routes become FastAPI
endpoints rendering `Jinja2Templates`; Flask-WTF forms become FastAPI form parsing + Pydantic
validation. A new, clean CSS design system replaces `main.css` (responsive layout, consistent
components, accessible defaults). The API client is rewritten on **httpx** with explicit timeouts and
typed error handling (DEC-3) so a failing API degrades to a flash message, never a UI crash. The
**create-diff 500 and the `NoneType: None` logging are fixed** as part of this slice.

**Tests — behaviour coverage for the core journeys (DEC-5).** Add `pytest-bdd` features for: create a
diff, list/view a dataset, build & download a report, and list/revoke tasks — exercised against both
the API and the UI. Unit coverage stays ≥80%; the new entrypoint code is covered by both.

**Observability — request/response logging by status class (DEC-8).** Every API request and every
UI→API call is logged at a level matching its outcome: **2xx/3xx → `INFO`**, **4xx → `WARNING`**,
**5xx → `ERROR`** (with traceback). Logs carry enough context to debug without a repro — method,
path, status, dataset/task id where applicable, and latency. Logging is added as **FastAPI middleware
+ the httpx client wrapper** (entrypoints/services layer), never buried in `domain`/`adapters`, per
the layering rules. This replaces the current ad-hoc `logger.exception(...)`-with-no-exception calls
(the `NoneType: None` noise) with deliberate, level-correct logging.

**Reporting — un-vendor eds4jinja2, pin `>=1,<2` (DEC-4).** A **gated** slice: add a golden-file test
that asserts report rendering output is unchanged, then swap the vendored copy for the pinned
release. If 1.x changes output incompatibly, **remain vendored**, record the gap, and ship everything
else.

**Infra.** Local dev is served over **plain HTTP via Traefik** — the https-redirect middleware is
dropped for `.localhost` (DEC-6, already applied), removing the self-signed-cert friction. The
compose `command:` for the now-single FastAPI app(s) is updated to a uvicorn worker invocation.

## Key decisions

- **DEC-1 — API = FastAPI (code-first), replacing Connexion 3.** Entrypoint-only rewrite; OpenAPI is
  generated, not hand-written.
- **DEC-2 — UI = FastAPI + Jinja2 SSR + modern CSS; decommission Flask** across both API and UI.
- **DEC-3 — UI→API client = httpx** with timeouts + typed errors, replacing bare `requests`.
- **DEC-4 — eds4jinja2 un-vendored, pinned `>=1,<2`; gated** by a golden-file rendering test;
  backwards-incompatible fallback = remain vendored.
- **DEC-5 — pytest-bdd behaviour tests** for API + UI core flows; ≥80% coverage retained.
- **DEC-6 — local dev over plain HTTP via Traefik** (https-redirect dropped for `.localhost`).
  *Applied.*
- **DEC-7 — `domain`/`services`/`adapters` unchanged** — the migration is confined to the `api`
  component entrypoint layer (+ the `reporting` dependency bump).
- **DEC-8 — status-class request/response logging**: 2xx/3xx → `INFO`, 4xx → `WARNING`, 5xx →
  `ERROR` (+traceback), with method/path/status/ids/latency context; implemented as FastAPI
  middleware + the httpx client wrapper, kept out of `domain`/`adapters`.

## Rabbit-holes (timeboxed / avoided)

- No redesign of the domain model, diff algorithm, or report-generation logic.
- No SPA — server-rendered Jinja only.
- eds4jinja2 1.x: timeboxed compatibility check; if incompatible, stay vendored — do **not** fix
  eds4jinja2 in this epic.
- No change to the Celery/Redis/Fuseki topology or the SPARQL contract.

## No-gos

- **No SPA / JS framework** (React/Vue/etc.).
- **No new datastore or message broker.**
- **No authentication / users / RBAC.**
- **No change to the SPARQL / diff / report computation.**
- **No production HTTPS / cert automation** in this epic (separate infra concern).
- **No rewrite of the `loader` component** (its own epic on `feature/rewrite-load-versions-to-python`).

## Out of scope (future)

CD pipeline ratification, observability/OpenTelemetry, production TLS — tracked under
`meaningfy-modernization`.
