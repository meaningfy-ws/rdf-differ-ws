# Vendored eds4jinja2 (TEMPORARY workaround)

This is `eds4jinja2 0.2.0` source (from PyPI sdist) with its dependency caps **relaxed** so the
package installs on Python 3.12. Upstream 0.2.0 pins `pandas ~=2.0.3` and `numpy ~=1.24.4`, neither
of which has a cp312 wheel, which blocks rdf-differ's 3.12 migration. There is no newer eds4jinja2
release.

- **Only `requirements.txt` is changed** (caps widened to current majors; pandas `>=2.2,<3`,
  numpy `>=1.26,<3`). The package code is unmodified.
- Referenced by the root `pyproject.toml` as a Poetry **path dependency**.
- **Remove this directory** and switch back to `eds4jinja2>=0.3.0` from PyPI once the upstream fix
  ships — see `openspec/changes/meaningfy-modernization/eds4jinja2-upstream-fix.md`.
