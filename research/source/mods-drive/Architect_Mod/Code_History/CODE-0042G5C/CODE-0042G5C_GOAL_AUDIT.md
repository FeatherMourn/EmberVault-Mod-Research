# CODE-0042G5C — Goal package

Date: 2026-09-21
Build: Enshrouded 1076226

Purpose:
Autonomous milestone goal for migrating `Render-MobilityTravelPage` to the established responsive F7 framework while preserving existing semantic and fail-closed behavior.

Starting authoritative runtime:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Verified starting SHA-256:
`05BCD81A8E46ABEAC8B22151091F6E48BD1A775D1A925700D62C6C30FAD0C76E`

Key source facts captured before goal creation:
- `Render-MobilityTravelPage` is still fixed-pixel.
- Responsive helpers `New-F7ResponsiveCard`, `New-F7ResponsiveTable`, and `Resize-AdminPageChildren` are already present.
- Speed, jump, autorun, gravity, teleport, position-read, and glider-stamina canonical actions are registry-disabled/fail-closed.
- Location category/search/selection are UI_ONLY F7 events.
- Teleport and current-position controls must remain fail-closed.
- Player G5B is closed at source/static level and must remain unchanged.

This package intentionally gives Codex autonomous iteration permission for bounded renderer edits and TEMP test infrastructure, with stop conditions only for genuine product/safety blockers.
