# Visual substitution comparison findings — 2026-09-27

The read-only comparison in
`VISUAL_SUBSTITUTION_COMPARISON_20260927.json` compared the staged furniture
`keen::RenderModel` with a second extracted KFC `RenderModel` candidate.

## Findings

- The donor exposes 40 inspected visual references.
- The candidate shares some basic fields and one material shape, but does not
  contain the donor's full LOD and mesh layout.
- Several donor material references and mesh indices are missing in the
  candidate.
- The report identifies candidate references and missing-in-candidate fields;
  it does not rewrite either resource.
- Runtime visual substitution remains unverified.
- The dependency-report CLI now exits with code `2` when the candidate graph
  is incomplete, preventing an incomplete comparison from being treated as a
  deployable research input.

## Consequence

A donor-preserving visual replacement cannot safely be implemented as a simple
field swap for this pair. The next valid research step is a resource-graph
construction experiment that supplies every referenced mesh, LOD, material,
texture, and dependent resource, followed by isolated in-game inspection.
Until that evidence exists, the Control Center must keep this capability
research-only and fail closed on incomplete graphs.
