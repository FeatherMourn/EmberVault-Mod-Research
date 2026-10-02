# Game settings boundary

The Control Center keeps gameplay tuning staged and profile-scoped until a
supported application contract is available.

## Observed installation surfaces

The inspected Enshrouded installation exposes `enshrouded_local.json` with
client graphics, display, and audio preferences. It does not expose a native
gameplay-tuning document. Gameplay experiments in the reference mod workspace
are represented by mod-owned Lua/config content, for example the Enshrouded
Mod Hub configuration modules.

## Safety decision

Control Center does not write to `enshrouded_local.json`, binary game data, or
mod-owned source files as part of Game Settings. Staged values can be exported
as a portable tuning manifest and consumed later by an explicitly identified
mod or tuning module. Such a module must declare its input contract, backup
requirements, mutation scope, and verification procedure before live
application is enabled. The first reviewed exception is the experimental EML
adapter: it stages and deploys an EmberVault-owned separate-process package
for the single evidenced `baseCritChance` field, then requires runtime
readback verification. This does not promote general gameplay tuning to a
supported capability and does not permit arbitrary adapter targets. The
portable handoff is defined by
`contracts/game-settings.schema.json`. Any future adapter must declare its
process mode, supported keys, backup requirements, mutation scope, and
verification steps in `contracts/tuning-adapter.schema.json`.

The guarded tuning-audit worker consumes the exported staged manifest, verifies
its `staged-only` state, and reports the inspection without applying it.

This preserves the first-release Save Manager boundary and prevents treating
client display settings as gameplay controls.

## Evidence required before live application

A tuning adapter may move beyond `experimental` only when its review packet
contains all of the following:

- The target Enshrouded build and the exact supported setting keys.
- A reproducible mapping from each staged key to the adapter-owned input.
- A verified backup procedure and a narrowly described mutation scope.
- A readback or runtime observation proving the intended value was applied.
- A rollback procedure tested on a disposable profile or world.
- Evidence that the adapter does not write save contents, client preferences,
  or unrelated mod/configuration files.
