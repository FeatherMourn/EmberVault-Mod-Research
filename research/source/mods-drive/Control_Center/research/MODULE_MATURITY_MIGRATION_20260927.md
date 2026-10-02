# Module maturity migration — 2026-09-27

All 28 Control Center-owned module manifests now declare
`feature_state: experimental`. The declaration is intentionally conservative:
it identifies the maturity gate without claiming that every gameplay or
visual feature is runtime verified.

The reusable audit command is:

```text
python tools/report_module_graph.py modules --strict-metadata
```

The built-in module graph currently returns no issues. Legacy manifests remain
loadable in compatibility mode, but strict mode exits nonzero when a manifest
omits or misstates `feature_state`.

The live game directory is not modified by this migration. Live third-party
folders continue to be classified by `tools/verify_live_loader.py`; any folder
without maturity metadata remains unclassified and should not be used for a
production smoke test until reviewed or isolated.
