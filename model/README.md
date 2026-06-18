# Domain model (LinkML) — seam

`schema.yaml` is the LinkML conceptual model for the RDF Differ domain.

**Status (modernization DEC-6): SEAM ONLY — not yet authoritative.** The runtime domain model is
still hand-written in [`../rdf_differ/domain/model.py`](../rdf_differ/domain/model.py); this schema
mirrors it. The `make generate-models` bridge is wired so generation *can* be adopted later, but no
generated code is committed or imported yet. Adopting generation (generated Pydantic replaces the
hand-written model, this schema becomes the source of truth) is a deliberate follow-up.

## Generating (opt-in)

`make generate-models` runs LinkML's `gen-pydantic`. LinkML is **not** in the default install (it
pulls a large dependency tree); install it on demand first:

```bash
poetry add --group model "linkml>=1.7"      # one-off, when adopting generation
make generate-models                         # writes rdf_differ/domain/_generated_model.py
```

Until generation is adopted, treat `_generated_model.py` (if produced) as a preview, not as wired-in
code. See the `conceptual-modelling` skill for the living-model workflow and multi-target generation.
