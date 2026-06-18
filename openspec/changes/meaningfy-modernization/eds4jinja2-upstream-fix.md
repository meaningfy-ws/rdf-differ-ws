# Upstream fix spec — make eds4jinja2 Python 3.12-compatible

> ✅ **RESOLVED (2026-06-18):** `eds4jinja2 0.3.1` is published on PyPI (requires-python ≥3.11,
> `pandas~=2.2`, `numpy~=1.26`). rdf-differ now depends on `eds4jinja2>=0.3.1,<0.4` and the
> `vendor/eds4jinja2/` workaround has been removed. Residual: 0.3.1 still pins `rdflib~=7.0` and
> `requests~=2.31`, which hold those deps at 7.0.x / 2.31.x in rdf-differ — a minor follow-up for a
> future eds4jinja2 release. The original spec is kept below as the historical record.

> Hand-off spec for the **`meaningfy-ws/eds4jinja2`** repo (a *separate* repository). This is the
> PROPER fix for the blocker recorded in `inputs/dep-bump-blocker.md`. rdf-differ currently uses a
> temporary **vendored, pin-relaxed copy** of eds4jinja2 (see `vendor/eds4jinja2/`) to unblock its own
> 3.12 migration; that vendoring is removed once eds4jinja2 ships the release described here.

## Problem

`eds4jinja2 0.2.0` cannot install on Python 3.12. Its `requirements.txt` pins:

- `pandas ~=2.0.3` → `>=2.0.3,<2.1` — pandas has **no cp312 wheel below 2.1.1**; builds from source and fails.
- `numpy ~=1.24.4` → `>=1.24.4,<1.25` — numpy has **no cp312 wheel below 1.26.0**.

There is no eds4jinja2 release newer than 0.2.0, so downstreams cannot bump out of the wall.

## Required changes (eds4jinja2 repo)

1. **Relax the numerical pins** in `requirements.txt`:
   - `pandas ~=2.0.3`  → `pandas >=2.2,<3.0`  (cp312 wheels from 2.1.1; 2.2.x is the safe current line)
   - `numpy ~=1.24.4`  → `numpy >=1.26,<3.0`  (cp312 wheels from 1.26.0)
   Leave the other runtime pins (Jinja2 ~=3.1, PyYAML ~=6.0, openpyxl ~=3.1, xlrd ~=2.0, toml,
   py-singleton, click ~=8.1, rdflib ~=7.0, beautifulsoup4 ~=4.12, requests ~=2.31, SPARQLWrapper ~=2.0)
   — all have cp312 wheels.
2. **Verify code compat with pandas ≥2.2** — the pandas surface used is moderate but must be re-tested:
   - `adapters/tabular_utils.py`: `DataFrame.replace` with nested dicts; `pandas.core.dtypes.common.is_numeric_dtype`.
   - `adapters/file_ds.py`: `pd.read_csv`, `pd.read_excel`.
   - `adapters/local_sparql_ds.py` / `remote_sparql_ds.py`: `pd.DataFrame(...)`, `pd.read_csv`.
   - `adapters/namespace_handler.py`: `DataFrame` ops, `inplace=` usage (watch pandas 3.0 copy-on-write — staying <3.0 avoids it for now).
3. **Declare 3.12 support**: add `Programming Language :: Python :: 3.12` classifier; set
   `python_requires='>=3.11'` (or `>=3.12`). Run the eds4jinja2 test suite on 3.12 in CI.
4. **Release** as **0.3.0** (minor — dependency-range widening, no API change).

## Downstream follow-up (this repo)

Once `eds4jinja2 0.3.0` is on PyPI:
- Remove `vendor/eds4jinja2/` and the path dependency.
- Replace it with `eds4jinja2>=0.3.0` (or current) in `pyproject.toml`.
- Re-run `poetry lock && make check-all`.

## Acceptance

- `pip install eds4jinja2==0.3.0` succeeds on a clean Python 3.12 environment.
- eds4jinja2's own tests pass on 3.12 with pandas ≥2.2 / numpy ≥1.26.
- rdf-differ drops the vendored copy and installs eds4jinja2 0.3.0 from PyPI with `make check-all` green.
