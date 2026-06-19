# PLAN — design: api-ui-fastapi-modernization

> Parent EPIC: `openspec/changes/api-ui-fastapi-modernization/proposal.md`.
> Derives the technical approach for migrating the API to FastAPI and rebuilding the UI on
> FastAPI + Jinja2 + modern CSS. Scope is the **`api` component entrypoint layer** only;
> `core`, `diffing`, `reporting`, `loader` domain/services/adapters are untouched (DEC-7).

## 1. Current state

- **API** — `rdf_differ/api/entrypoints/api/`: Connexion 3 (`AsyncApp`/Flask app), routes declared in
  `openapi/openapi.yaml`, handlers in `handlers.py` returning `(body, status)` tuples and raising
  `werkzeug.exceptions`. Runs under uvicorn. Pulls Flask in for logging.
- **UI** — `rdf_differ/api/entrypoints/ui/`: Flask app (`__init__.py`), routes in `views.py`,
  Flask-WTF forms in `forms.py`, a thin API client in `api_wrapper.py` (bare `requests`, no timeouts),
  Jinja templates under `templates/`, one `static/main.css`.
- **Services/adapters** (unchanged): `api/services/{celery,tasks,queue}.py`, plus `core`, `diffing`,
  `reporting` adapters/services. Handlers already build pydantic DTOs from `api/domain/model.py`.

## 2. Target architecture

Two ASGI apps in the `api` component, both **FastAPI**:

```
rdf_differ/api/entrypoints/
  api/                      # FastAPI REST API (replaces Connexion)
    app.py                  # FastAPI() instance, routers, exception handlers, logging middleware
    routes.py               # path operations (was handlers.py) — thin, call services
    schemas.py              # pydantic request models (response models reuse api/domain/model.py)
    errors.py -> exceptions.py   # domain/HTTP error -> HTTPException mapping (per-layer exceptions.py)
    run.py                  # uvicorn entrypoint (connexion_app -> fastapi app)
  ui/                       # FastAPI + Jinja2 (replaces Flask)
    app.py                  # FastAPI() instance, Jinja2Templates, static mount, logging middleware
    routes.py               # page endpoints (was views.py)
    forms.py                # pydantic form models (replaces Flask-WTF)
    api_client.py           # httpx client with timeouts + typed errors (replaces api_wrapper.py)
    templates/              # restyled Jinja templates
    static/                 # modern CSS design system
  _logging.py               # shared status-class logging middleware + helpers (DEC-8)
```

Both apps keep importing the existing `services`/`adapters` unchanged. The compose `command:` for each
service becomes `uvicorn rdf_differ.api.entrypoints.<api|ui>.run:app`.

## 3. Endpoint mapping (API)

Connexion handler → FastAPI path operation, 1:1, same paths/verbs/status codes:

| Path / verb | Handler (old) | Route (new) |
|---|---|---|
| `GET /diffs` | `get_diffs` | `list_diffs` |
| `GET /diffs/{id}` | `get_diff` | `get_diff` |
| `POST /diffs` (multipart) | `create_diff` | `create_diff` |
| `DELETE /diffs/{id}` | `delete_diff` | `delete_diff` |
| `POST /diffs/report` | `build_report` | `build_report` |
| `GET /diffs/report` | `get_report` | `get_report` |
| `GET /aps` | `get_application_profiles_details` | `list_application_profiles` |
| `GET /tasks/active` | `get_active_tasks` | `list_active_tasks` |
| `GET /tasks/{id}` | `get_task_status` | `get_task_status` |
| `DELETE /tasks/{id}` | `stop_running_task` | `stop_task` |

Routes return pydantic response models (FastAPI serialises) instead of `(dict, status)` tuples.
Multipart upload (`POST /diffs`) uses `UploadFile` + `Form(...)`.

## 4. Error mapping

A single `werkzeug → HTTPException` translation table, applied by replacing the raises in the routes
and adding FastAPI exception handlers so the JSON body keeps a problem-style shape:

| Old (werkzeug) | New | HTTP |
|---|---|---|
| `Conflict` | `HTTPException(409)` | 409 |
| `NotFound` | `HTTPException(404)` | 404 |
| `UnprocessableEntity` | `HTTPException(422)` | 422 |
| `NotAcceptable` | `HTTPException(406)` | 406 |
| `InternalServerError` | `HTTPException(500)` | 500 |

A catch-all handler maps unhandled exceptions to 500 **and logs at ERROR with traceback** (DEC-8) —
this is what makes the create-diff 500 debuggable when we test the migrated path.

## 5. Status-class logging (DEC-8)

A single ASGI middleware in `_logging.py` wraps every request on both apps:

- choose level by status class: **2xx/3xx → INFO**, **4xx → WARNING**, **5xx → ERROR (+traceback)**;
- emit one structured line: `method path status latency_ms` + contextual ids (dataset_id/task_id when
  present in path params);
- the UI's `httpx` client logs each upstream call the same way (so a failing API is visible from the
  UI side too).
- logging lives only in entrypoints (`_logging.py`, `app.py`, `api_client.py`) — never in
  `domain`/`adapters`, per layering. Replaces the `logger.exception()`-without-exception calls.

## 6. UI client (DEC-3)

`api_client.py` uses a module-level `httpx.Client(timeout=httpx.Timeout(10.0))`. Each call returns a
typed `ApiResult` (status + parsed body or raw text) and **never** calls `.json()` unguarded — a
non-JSON/error response yields a typed error the route turns into a flash, not a UI 500.

## 7. eds4jinja2 un-vendor (DEC-4, gated)

1. Add a **golden-file test**: render a known report with the current vendored code, snapshot output.
2. Remove the vendored `eds4jinja2`, add dependency `eds4jinja2 = ">=1,<2"`.
3. Re-run the golden test. **If output matches** → keep the upgrade. **If it diverges incompatibly**
   → revert to vendored, record the gap in this design under "Deferred", ship everything else.

## 8. Testing strategy

- **Unit** (`tests/unit/`): routes (request/response mapping, error mapping), the logging middleware
  (level per status class), the httpx client (timeout + non-JSON handling), forms validation.
  Services/adapters are mocked — we do not re-test them.
- **Behaviour** (`tests/feature/`, pytest-bdd): create-diff, list/view dataset, build+download report,
  list/revoke tasks — against the API (TestClient) and the UI (TestClient). Existing path-based marker
  injection (`tests/conftest.py`) applies; service-dependent steps tagged `@pytest.mark.integration`.
- Coverage ≥80% retained; `make check` (ruff + mypy + import-linter) stays green.

## 9. Architecture / import-linter

The `api` component stays **tier 3** (may import `core`, `diffing`, `reporting`). FastAPI/httpx/Jinja
are entrypoint-layer dependencies — they must not leak into `domain`/`adapters`. The existing
`.importlinter` per-component layer contracts already forbid that; no contract changes expected beyond
removing `connexion`/`flask`/`flask_wtf` and adding `fastapi`/`httpx`/`jinja2`/`python-multipart` to
`pyproject.toml`.

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| FastAPI multipart differs from Connexion's file handling | Behaviour test for `POST /diffs` with real `UploadFile`s before deleting the old handler |
| Hidden Connexion request-validation we relied on | Re-declare validation explicitly in pydantic schemas; behaviour tests cover the contract |
| eds4jinja2 1.x breaks rendering | Golden-file gate (DEC-4) with vendored fallback |
| The create-diff 500 is environmental (celery/redis/fuseki) not code | Root-cause during behaviour testing of the migrated path; status-class logging surfaces the real error |
| UI redesign scope creep | CSS is a single design-system pass; no SPA, no new components beyond the existing pages |

## 11. Slice order (always green)

S0 deps & skeleton → S1 API routes+schemas (TDD) → S2 API error mapping + logging middleware →
S3 swap API entrypoint to FastAPI, delete Connexion + openapi.yaml → S4 UI httpx client (TDD) →
S5 UI FastAPI routes + Jinja + forms → S6 modern CSS design system → S7 behaviour tests (API+UI) →
S8 eds4jinja2 un-vendor (gated) → S9 fix create-diff 500 (found in S7 testing) → S10 compose/docs +
deploy smoke + release.

## Deferred / open

- eds4jinja2 1.x compatibility verdict (decided in S8 by the golden test).
- Production HTTPS/cert automation and CD pipeline ratification remain out of scope (EPIC no-gos).
