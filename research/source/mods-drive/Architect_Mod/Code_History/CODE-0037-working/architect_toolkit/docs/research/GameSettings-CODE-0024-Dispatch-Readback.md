# CODE-0024 — GameSettings dispatch and readback mapper

## Outcome

Build 1076226 was inspected offline. The vanilla reflection model is coherent,
but neither the action dispatch boundary nor an authoritative state/event
readback boundary was recovered. CODE-0024 therefore installs zero
GameSettings hooks and enables no mutation.

The executable identity is SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`,
PE timestamp `0x6A4236C8`, image size `0x02DA7000`. Runtime scaffolding also
requires Architect's canonical unique BuildingPlace signature validation; a
failure in any field disables this observer without disabling other features.

## Static path assessment

| Path element | Evidence | Result |
|---|---|---|
| Aggregate | `keen::ecs::GameSettings`, index 2702, size `0x90` | `PROVEN_STATIC_BUILD_1076226` |
| Action | `AdminChangeGameSettingsAction`, index 2703, aggregate `+0`, `VersionedData +0x90` | layout proven; constructor/submission `UNSOLVED` |
| Version | `VersionedData`, size 4, `VersionedDataVersion` typedef | representation proven; increment/wrap/stale comparison `UNSOLVED` |
| Server consumption | `ServerConsumedPlayerInput.consumedAdminChangeGameSettingsAction +0xC4` | server-side consumed-version slot proven; owning entity and consumer `UNSOLVED` |
| Changed event | `GameSettingsChangedEvent`, index 3410, size `0x98`, aggregate `+0x08` | layout proven; producer/subscribers `UNSOLVED` |
| Presets/bounds | `GameSettingsPresetsResource`, index 4311, min `+0`, max `+0x90`, presets `+0x120` | resource shape proven; loaded instance/default identity `UNSOLVED` |

A bounded search for the reflection name/impact/qualified/internal hashes found
no direct 32-bit immediate occurrence in `.text` for the action, changed event,
or aggregate. Existing action-consumer research does not identify a
GameSettings-specific dispatch edge. Consequently there is no unique exact
signature, understood overwrite span, owner, or calling convention to qualify.

The reflection record reports `fieldCount: 37`; this corrects the earlier
36-field summary. Every field and offset is emitted by
`bridge/game_settings_static_map.json`. All 37 are currently `UNAVAILABLE`.
No field is classified `PROVEN_LIVE`, `EXPERIMENTAL_LIVE`, `SESSION`, or
`RELOAD`.

## Observe-only runtime scaffold

F7 exposes `gamesettings.inspect`, `gamesettings.capture.begin`, and
`gamesettings.capture.end`. They publish a read-only envelope to the native
worker. The worker writes lifecycle records only because no qualified probe
exists. Null aggregate/value fields are intentional and must not be treated as
zero values.

Bounds are 64 records and 262,144 capture bytes. Startup clears stale command
and capture files. Status/state documents are atomic. Clean unload closes an
active capture. No process-memory scan, pointer traversal, game-memory write,
detour, action construction, or dispatch occurs.

## Authority, persistence, readback, and restoration

The server-side consumed slot supports a server-authoritative hypothesis, but
does not prove host permission, client routing, or the authoritative owner.
Authority is therefore `UNSOLVED`. Cache, replication, application timing, and
persistence are also `UNSOLVED`.

There is no restoration mechanism yet. A future mechanism must first read and
verify the complete authoritative aggregate, dispatch the complete original
through the same proven vanilla route, and verify byte/field equality through
an independent authoritative readback. Direct aggregate writes are forbidden.

`factoryProductionSpeedFactor` is the preferred first mutation candidate only
after that round trip is proven: it has a clear aggregate field and a fresh
production job can provide a high-signal behavioral check. This is a candidate,
not an enabled operation.

## Smallest next discriminating experiment

Use an external static disassembler/data-flow pass to locate the generated ECS
registration/query descriptor keyed by numeric component/action/event identity,
then trace its callback to a concrete current-build function. A candidate can
be instrumented only after proving a unique signature, whole-instruction
overwrite span, aggregate argument provenance, side/authority, and a separate
readback boundary. Return `game_settings_state.json`,
`game_settings_status.json`, and `game_settings_capture.jsonl` from the initial
zero-probe session; they should confirm build gating and command lifecycle, not
claim settings values.
