# CODE-0023 AdminAction registry

`runtime/admin_action_registry.json` is the build-1076226 catalog for the F7
Admin Console. `runtime/AdminActionRegistry.psm1` loads and validates it,
expands compact authoring families to complete AdminAction records, exposes the
adapter table, and enforces fail-closed dispatch. `ArchitectRuntime.ps1`
imports the catalog at startup and uses it for F7 navigation, rendering,
command membership, and adapter dispatch.

## Contract

Every resolved action has `commandId`, display/category text, control and value
types, optional numeric bounds/default/current value, evidence status, backend
adapter, runtime mode, authority, persistence, risk, readback requirement,
revert support, failure reason, and enabled state. The loader accepts only the
five evidence states and four runtime modes specified by CODE-0023. An action
cannot be enabled without `PROVEN_BUILD_1076226`; a mutation cannot be enabled
without a readback mechanism.

Existing `player.*`, `item.*`, and `multiplayer.*` command IDs are retained.
New roadmap actions cover all requested F7 categories and INC-0010-derived
capability hypotheses. Those hypotheses are not evidence: every new mutation
is disabled with `PLANNED` or `UNSOLVED`, `UNAVAILABLE`, unknown authority and
an explicit failure reason. The five preset definitions are likewise disabled.

## Adapter boundary

`New-AdminAdapterTable` creates explicit Player, Movement, Travel, Inventory,
Crafting, GameSettings, World, Camera, Glider, BuildingAdmin, MultiplayerAdmin,
and Diagnostics boundaries. It installs no handlers. A handler must be added
only after independent current-build validation. Dispatch rejects unknown
actions, disabled actions, absent adapters, absent handlers, and mutating
results without `readbackVerified`.

## Integration

The runtime imports the module at F7 initialization, loads the JSON beside it,
and uses the resolved `actions` array to construct category navigation and
controls. Existing proven read-only handlers remain explicit. Empty adapter
tables ensure catalog presence alone never enables a backend. Keep the existing
`command.json`, ACK/history, build gate, and dispatcher behavior while
migrating one independently proven action at a time.

No setting is newly claimed LIVE, SESSION, or RELOAD here. Static/runtime
research must still establish its authoritative origin, caching, refresh,
authority, readback, and revert behavior. Until then all GameSettings roadmap
entries remain `PLANNED / UNAVAILABLE`.

Run the focused tests with:

```powershell
python -m unittest tools.AdminConsole.tests.test_admin_action_registry -v
```
