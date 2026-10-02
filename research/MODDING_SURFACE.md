# Current modding surface

This document is a living capability map. It describes the state of the research corpus, not a guarantee that every capability works on every game version.

## Areas with substantial evidence

- Lua-based mod structure and feature configuration
- Static inspection of game/reference data and KFC-related artifacts
- Runtime probing and capture workflows
- Player/entity discovery and observer-oriented investigation
- Item, inventory, ownership, and container research
- Building selection, placement, blueprint, preview, and snapping research
- Game settings and admin/multiplayer research
- Supporting analyzers, indexes, correlation tools, and validation scripts

## Areas requiring version-aware validation

- Native addresses, signatures, offsets, and hook locations
- Runtime object layouts and descriptor fields
- Internal call paths and parent/child relay behavior
- Multiplayer and server-side behavior
- UI/backend contracts and lifecycle assumptions
- Any claim derived from a single game build or one capture

## Practical rule

Treat Lua and data-file behavior as implementation evidence, not automatically as a stable public API. Treat native/runtime discoveries as build-specific until reproduced across versions. Every capability claim should link to a finding record and its evidence.

## Gaps to close

- Promote the strongest recurring deep dives into canonical records.
- Add exact build/version metadata to older findings.
- Mark obsolete offsets, failed approaches, and superseded hypotheses.
- Connect each major implementation feature to the research that justified it.
