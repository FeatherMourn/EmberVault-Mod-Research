# Stage 21 — Content Creator 2.0

Stage 21 turns Content Creator from a guarded metadata form into a structured
design workspace while preserving the design-only boundary.

## Delivered

- Added deterministic project previews covering assets, materials, dimensions,
  recipe steps, registration, compatibility, research, and knowledge links.
- Added stable knowledge-entry references alongside existing research links.
- Added traceable design decisions with research and knowledge evidence links.
- Added preview data to exported design packages.
- Added Control Center preview status and explicit live-installation disabled
  messaging.
- Extended the content-project contract for knowledge references.

## Safety boundary

Content Creator produces design records and export packages only. It does not
install assets, register content in the game, mutate saves, or alter live game
files. Preview readiness means the design record is complete enough for review,
not that it is executable game content.

## Next slice

The remaining Stage 21 work is visual/editorial refinement: richer project
selection, reference pickers, asset inspection, and export-package review. Those
features should continue to consume the same contracts rather than bypassing
the service layer.
