# Visual candidate graph live smoke — 2026-09-27

## Result

The build-matched, research-only visual candidate probe loaded successfully in
Enshrouded and completed its read-only graph scan.

- EML build: `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`
- Module: `visual_candidate_graph_probe_1076226_v2`
- Runtime scan: `keen::RenderModel`, `count=12713`
- Runtime action: `read_only_no_visual_mutation`
- EML patch count: `0`
- Runtime loader: attached
- Crash/error evidence during the probe: none observed

## Interpretation

This proves that the candidate graph can be discovered and inspected by the
runtime loader on the current build. It does **not** prove that assigning the
candidate to a placed furniture object's `TemplateResource` will change the
rendered object. The probe intentionally performed no visual mutation.

## Recovery

After the smoke test, the research-only module was moved to:

`research/staging/live_probe_recovery_20260927`

The stable `enshrouded_mod_hub` module was restored. Final live preflight:

- stable modules: `1`
- research-only modules: `0`
- unclassified modules: `0`
- isolation ready: `true`

