# Runbook — rotate leaked secrets & scrub them from git history

> **Prep only — NOT executed.** The history rewrite is destructive (it changes every commit hash,
> breaks open PRs/forks, and requires every collaborator to re-clone). It also must be a deliberate,
> coordinated act by a maintainer with push rights. This documents exactly how; run it yourself.

## What leaked

Real secret values were committed (and remain in history) in:

- `bash/.env`  — `RDF_DIFFER_SECRET_KEY_API`, `RDF_DIFFER_SECRET_KEY_UI`,
  `RDF_DIFFER_FUSEKI_PASSWORD`, `RDF_DIFFER_FUSEKI_ADMIN_PASSWORD`
- `infra/.env`, `infra/.env-test` — the same `SECRET_KEY_*` + Fuseki/Flower passwords

These files are now untracked + git-ignored (commits `e6800a53`, `596cecfa`) with `*.example`
templates, so **no new** leaks occur — but the old values persist in history until scrubbed.

## Step 1 — ROTATE FIRST (the real fix; do this regardless of the scrub)

History scrubbing is hygiene; **rotation is what actually neutralises the exposure.**

1. Generate fresh Flask secret keys and set them in the *deployed* env (not committed):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"   # x2 (API + UI)
   ```
2. Change the **Fuseki** admin/user password and the **Flower** admin password in every environment.
3. Update the deployment's real `.env` / secret store with the new values.
4. Treat the old values as compromised (assume anyone with repo/clone/fork access has them).

## Step 2 — scrub history (optional, after rotation)

Use `git filter-repo` (preferred over the deprecated `filter-branch` / BFG).

```bash
pip install git-filter-repo

# From a FRESH clone of the repo (filter-repo rewrites the whole history):
git clone <repo-url> rdf-differ-scrub && cd rdf-differ-scrub

# Remove the secret-bearing files from ALL history:
git filter-repo --invert-paths \
    --path bash/.env \
    --path infra/.env --path infra/.env-test \
    --path docker/.env --path docker/.env-test      # pre-move paths, if present in history

# (Alternative — keep the files but redact values — use --replace-text with a patterns file.)

# Re-add the remote (filter-repo drops it) and force-push every branch + tags:
git remote add origin <repo-url>
git push --force --all
git push --force --tags
```

## Step 3 — fallout & coordination

- **Every collaborator must re-clone** (or hard-reset) — old clones keep the secrets and conflict.
- **Open PRs and forks break** (their bases are rewritten) — close/recreate them.
- GitHub keeps **cached commit views**; old SHAs may stay reachable by direct URL. Contact GitHub
  Support to purge cached views if the exposure is sensitive.
- Re-run the modernization PR off the rewritten `master` if the scrub lands before this PR merges.

## Verification

```bash
git log --all -p -- bash/.env infra/.env infra/.env-test | grep -i "SECRET_KEY\|PASSWORD"   # → no hits
```
