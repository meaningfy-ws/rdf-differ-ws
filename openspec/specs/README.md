# Durable capability specs — THE TRUTH

`openspec/specs/<capability>/spec.md` is the merged, machine-validated truth for RDF Differ:
the RFC-2119 SHALL requirements + Given/When/Then scenarios that survived `/opsx:archive`.

- **This is authority.** Anything under `.claude/` (incl. `MEMORY.md`) is a regenerable index; if
  it disagrees with these specs, the specs win.
- Deltas in `openspec/changes/<id>/specs/` merge **here** on archive — never hand-edit a merged
  spec to diverge from the change that produced it.
- Starts empty; fills as changes are archived. Validate shape with `openspec validate --strict`.
