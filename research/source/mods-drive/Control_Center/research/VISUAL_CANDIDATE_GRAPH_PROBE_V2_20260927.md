# Visual Candidate Graph Probe v2 — 2026-09-27

## Status

Research-only, read-only probe generated from the staged visual candidate. It
has not been installed into the live `mods` directory and performs no runtime
mutation.

## Inputs

- Candidate: `research/staging/visual_candidate_159b_template_variant_1076226.json`
- Resource type: `keen::RenderModel`
- Target build: `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`
- Probe: `research/probes/visual_candidate_graph_probe_1076226_v2`
- Dependency count: 1 candidate GUID

## Safety checks

- Manifest explicitly declares `feature_state: research-only`.
- Manifest declares `runtime_mutation: false`.
- Live preflight reports one stable module, zero research-only modules, zero
  unclassified modules, and `isolation_ready: true`.

## Boundary

This probe can observe whether the candidate RenderModel and direct dependency
metadata are visible to the runtime API. It does not prove that the model can
be assigned to a placed TemplateResource or rendered in-game.
