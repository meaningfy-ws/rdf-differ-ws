# Dependency-bump blocker — eds4jinja2 0.2.0 vs Python 3.12 (seed input, 2026-06-18)

Discovered while applying the merged slice 3+5 (Poetry migration + full-majors bump on 3.12).

## The wall

`eds4jinja2 0.2.0` (Meaningfy's own report-rendering library, used by `services/report_handling`)
transitively pins:

- `pandas ~=2.0.3`  → only `>=2.0.3,<2.1`
- `numpy ~=1.24.4`  → only `>=1.24.4,<1.25`

Neither has a **Python 3.12 (cp312) wheel**:

| package | pin | cp311 wheels | cp312 wheels |
|---|---|---|---|
| pandas | 2.0.3 (~=2.0.3 caps <2.1) | yes (6) | **0** |
| numpy  | 1.24.4 (~=1.24.4 caps <1.25) | yes (6) | **0** |

(First cp312 wheels: pandas 2.1.1, numpy 1.26.0.) With no wheel, pip/poetry build from source and
`pandas 2.0.3` fails on 3.12 (`ModuleNotFoundError: No module named 'pkg_resources'`).

**`eds4jinja2` latest release is 0.2.0** — there is no newer version to bump to that relaxes these pins.

## Consequence

- `poetry lock` resolves (metadata-only), but `poetry install` on **3.12** fails.
- The same stack **installs cleanly on Python 3.11** (pandas 2.0.3 + numpy 1.24.4 have cp311 wheels).
- So the 3.12 target is blocked *specifically by eds4jinja2*, not by Flask/Connexion/Celery.

## Other bump findings (not blockers)

- **Flask-Bootstrap 3.3.7.1**: DROP — no Python imports, no template usage; UI uses Materialize CSS via CDN.
- **Connexion 2.14 → 3.x**: real code work (FlaskApp options renamed; multipart `FileStorage` handling in
  `create_diff` changed). Isolated to `entrypoints/api/__init__.py` + handler signatures.
- **pytest-bdd 7 → 8**: step-API changes in `tests/steps/`.

## Options (decision required)

- **A. Update eds4jinja2 first** (separate effort on that repo): relax pandas/numpy pins to ≥2.2/≥1.26,
  confirm 3.12, release a new version; then resume this migration on 3.12. Proper fix.
- **B. Target Python 3.11 now**: the existing stack installs as-is; revisit 3.12 once eds4jinja2 ships a
  3.12-compatible release. (3.11 is supported upstream until Oct 2027.)
- **C. Workaround**: vendor/patch a relaxed eds4jinja2 fork, or replace its reporting (the latter
  violates the no-behaviour-change no-go).
