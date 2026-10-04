# Contracts and Module SDK alignment — 2026-10-04

## Result

The Research module manifest is aligned with the current shared Contracts and
Module SDK version 1.

- The manifest contains the canonical module fields, contract version, process
  mode, safety declaration, recovery declaration, and operation types.
- `embervault.research` is a valid module identifier and uses the separate
  process mode required by the isolated research worker.
- The research profile is the only allowed profile, and the manifest remains
  read-only with no backup requirement for live files.
- The worker uses the SDK `ModuleResult` boundary and reports read-only,
  non-mutating evidence-session data.
- Evidence, recovery, and Content Creator handoff data remain module-owned
  research records; no local replacement for shared contracts was added.

## Verified boundaries

- Contract version `1` is accepted by the SDK manifest validator.
- The worker remains blocked outside the research profile.
- The catalog, publication, and Content Creator handoff are read-only data
  operations and do not grant runtime approval.

## Follow-up

Future contract changes must update the shared Contracts repository first, then
the SDK dependency and module fixtures together. Research should not introduce
parallel schema versions locally.
