# PLAN — tasks: api-ui-fastapi-modernization

Parent EPIC: `api-ui-fastapi-modernization` (proposal.md) · Design: `design.md` · Golden thread: every
slice traces to a DEC in the EPIC. Each slice lands test-first, always green (`make check` + tests),
its own commit. Implementation branch off `feature/api-ui-fastapi-modernization`.

## S0 — Dependencies & skeleton  (DEC-1, DEC-2, DEC-3) — DONE
- [x] Add `fastapi`, `httpx`, `jinja2`, `python-multipart`, `uvicorn[standard]` to `pyproject.toml`
- [x] Remove `connexion`, `flask`, `flask-wtf` once their last importer is gone (S3/S5)
- [x] `poetry lock`; `make install`

## S1 — API routes + schemas  (DEC-1, DEC-7) — DONE
- [x] Unit tests via FastAPI TestClient (services mocked): `tests/unit/test_api_routes.py`
- [x] `api/entrypoints/api/schemas.py`: pydantic request models (multipart for `POST /diffs`)
- [x] `api/entrypoints/api/routes.py`: 10 path operations calling the existing services unchanged
- [x] Responses reuse `api/domain/model.py` DTOs (fixed a real /diffs/report vs /diffs/{id} order bug)

## S2 — Error mapping + logging middleware  (DEC-1, DEC-8) — DONE
- [x] `api/entrypoints/api/exceptions.py`: werkzeug→HTTPException, problem-style JSON
- [x] `_logging.py`: status-class middleware (2xx/3xx INFO, 4xx WARNING, 5xx ERROR+traceback)
- [x] Unit tests: `tests/unit/test_entrypoint_logging.py`

## S3 — Cut over the API entrypoint  (DEC-1) — DONE
- [x] `app.py` FastAPI instance; `run.py` exposes `app`; Dockerfile → `run:app` (UvicornWorker)
- [x] Deleted `handlers.py`, `openapi/openapi.yaml`, Connexion wiring; `/openapi.json` + `/docs` served

## S4 — UI API client on httpx  (DEC-3, DEC-8) — DONE
- [x] `ui/api_client.py`: timeouts, typed `ApiResult`, guarded JSON, per-call logging
- [x] Unit tests: `tests/unit/test_ui_api_client.py` (timeout/non-JSON/error → no crash)

## S5 — UI on FastAPI + Jinja2  (DEC-2) — DONE
- [x] `ui/forms.py` pydantic validation; `ui/routes.py`; `ui/app.py` (+ session flash, static)
- [x] `ui/rendering.py`; templates ported; deleted Flask `views.py`/`api_wrapper.py`/`helpers.py`
- [x] `ui/security.py` session-bound CSRF (restores the Flask-WTF guard; security review)
- [x] Unit tests: `tests/unit/test_ui_routes.py` (renders, validation, flash, CSRF rejection)

## S6 — Modern CSS design system  (DEC-2) — DONE
- [x] New dependency-free `ui/static/main.css`; all templates restyled (dropped Materialize/jQuery)
- [x] Visual smoke via the running stack

## S7 — Behaviour tests (pytest-bdd)  (DEC-5) — MOVED
> Superseded by a dedicated, project-wide test-coverage EPIC (loading + diffs + reports + UI +
> edge/negative paths). The API/UI flows are already covered by the S1–S6 TestClient unit tests.

## S8 — eds4jinja2 un-vendor, gated  (DEC-4) — DEFERRED
> Gated and orthogonal; the report-rendering path is currently blocked by the legacy
> `load_versions.sh` pipeline (rdf-loading-module epic). Deferred to a follow-up; the vendored
> copy stays until then. No regression — nothing in this epic depends on the bump.

## S9 — Root-cause & fix the create-diff 500  (EPIC bug) — DONE
- [x] Reproduced on the live stack; status-class ERROR log pinpointed `save_files` mkdir
- [x] Fixed (`parents=True`) + the code-shadowing volume defect + non-root volume ownership
- [x] Regression test; create-diff returns 200 and enqueues (verified on the live stack)

## S10 — Ship  (release) — IN PROGRESS
- [x] Compose `command:`/Dockerfile → UvicornWorker for api + ui; `make start` smoke (all routes 200)
- [x] Deploy smoke on the live Docker stack: API + UI + OpenAPI/docs all 200
- [x] `make check` + full unit tests green (245 pass)
- [ ] Update README/docs for the FastAPI surface
- [ ] Push, open PR
- [ ] Merge + release after the project-wide test EPIC gives end-to-end confidence
