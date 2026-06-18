# Browser E2E tests (Playwright) — opt-in

A thin browser smoke harness for the UI. **Opt-in**: these tests need the full stack running
and a browser installed, and they **auto-skip** otherwise — so they never break a normal unit
run or CI.

When to invest here: only for user-critical, JS-dependent flows. The UI is server-rendered with
minimal client JS, so the Flask-test-client + BeautifulSoup tests in `tests/unit` / `tests/integration`
cover most behaviour; keep this suite small.

## Run

```bash
poetry install --with e2e
poetry run playwright install chromium       # one-off: fetch the browser
make start-services-test                     # bring up UI + API + Fuseki + Redis + Celery
RDF_DIFFER_UI_URL=http://localhost:8030 \
  poetry run pytest tests/e2e --browser chromium
```

`RDF_DIFFER_UI_URL` defaults to `http://localhost:8030`. CI runs this only via the opt-in
`.github/workflows/e2e.yaml` (manual `workflow_dispatch`).
