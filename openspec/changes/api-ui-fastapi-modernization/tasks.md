# PLAN — tasks: api-ui-fastapi-modernization

Parent EPIC: `api-ui-fastapi-modernization` (proposal.md) · Design: `design.md` · Golden thread: every
slice traces to a DEC in the EPIC. Each slice lands test-first, always green (`make check` + tests),
its own commit. Implementation branch off `feature/api-ui-fastapi-modernization`.

## S0 — Dependencies & skeleton  (DEC-1, DEC-2, DEC-3)
- [ ] Add `fastapi`, `httpx`, `jinja2`, `python-multipart`, `uvicorn[standard]` to `pyproject.toml`
- [ ] Remove `connexion`, `flask`, `flask-wtf` once their last importer is gone (S3/S5)
- [ ] `poetry lock`; `make install`
- [ ] Create empty `api/entrypoints/_logging.py`, `api/entrypoints/api/app.py`, `ui/app.py`

## S1 — API routes + schemas (TDD)  (DEC-1, DEC-7)
- [ ] Unit tests: each route's request parse + response model + status, services mocked
- [ ] `api/entrypoints/api/schemas.py`: pydantic request models (multipart for `POST /diffs`)
- [ ] `api/entrypoints/api/routes.py`: 10 path operations calling the existing services unchanged
- [ ] Responses reuse `api/domain/model.py` DTOs

## S2 — Error mapping + logging middleware (TDD)  (DEC-1, DEC-8)
- [ ] `api/entrypoints/api/exceptions.py`: werkzeug→HTTPException table + handlers (problem-style JSON)
- [ ] Unit tests: each error maps to the right status + body
- [ ] `_logging.py`: status-class middleware (2xx/3xx INFO, 4xx WARNING, 5xx ERROR+traceback, latency, ids)
- [ ] Unit tests: level chosen per status class; traceback on 5xx

## S3 — Cut over the API entrypoint  (DEC-1)
- [ ] `app.py`: FastAPI instance wiring routers + handlers + middleware
- [ ] `run.py`: `app` is the FastAPI app (uvicorn)
- [ ] Delete `handlers.py`, `openapi/openapi.yaml`, Connexion wiring
- [ ] `make check` green; `/openapi.json`, `/docs` served by FastAPI

## S4 — UI API client on httpx (TDD)  (DEC-3, DEC-8)
- [ ] `ui/api_client.py`: `httpx.Client` with timeouts; typed `ApiResult`; guarded JSON
- [ ] Unit tests: timeout path, non-JSON/error response → typed error (no crash), per-call logging

## S5 — UI on FastAPI + Jinja2 (TDD)  (DEC-2)
- [ ] `ui/forms.py`: pydantic form models (replace Flask-WTF)
- [ ] `ui/routes.py`: page endpoints (index, create-diff, view-dataset, report, tasks, revoke)
- [ ] `ui/app.py`: FastAPI + `Jinja2Templates` + static mount + logging middleware + flash shim
- [ ] Port templates; delete Flask `__init__.py`/`views.py`/`api_wrapper.py`
- [ ] Unit tests: route renders, form validation, error→flash

## S6 — Modern CSS design system  (DEC-2)
- [ ] New `ui/static/` stylesheet: layout, typography, components (cards, forms, tables, flash, nav), responsive
- [ ] Restyle `base.html` + page templates against it
- [ ] Manual visual smoke via the running stack

## S7 — Behaviour tests (pytest-bdd)  (DEC-5)
- [ ] Features: create diff, view dataset, build+download report, list/revoke tasks
- [ ] Steps against API `TestClient` and UI `TestClient`; service-dependent steps `@pytest.mark.integration`
- [ ] Coverage ≥80%

## S8 — eds4jinja2 un-vendor, gated  (DEC-4)
- [ ] Golden-file test: snapshot a rendered report from the vendored code
- [ ] Remove vendored copy; add `eds4jinja2 = ">=1,<2"`; `poetry lock`
- [ ] Re-run golden test → keep if equal; **revert to vendored + record gap** if incompatible

## S9 — Root-cause & fix the create-diff 500  (EPIC bug)
- [ ] Reproduce via behaviour test + the running stack; read status-class ERROR log/traceback
- [ ] Fix root cause; regression test green

## S10 — Ship  (release)
- [ ] Update compose `command:` to uvicorn for api + ui; `make start` smoke (all routes 200/expected)
- [ ] Update README/docs for the FastAPI surface
- [ ] `make check` + full tests green
- [ ] Push, open PR, merge to master (own org only, no AI attribution)
- [ ] Deploy smoke: `make start` on merged master, verify UI/API/report flow end-to-end
- [ ] Cut release (tag + GitHub release) once deploy verified
