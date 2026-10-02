# CODE-0021 — F7 PlayerObserver research probe

## Result

The current repository and build-1076226 artifacts do not contain enough
evidence to identify a defensible local-player or vital-state observation
point. CODE-0021 therefore implements the requested stop-condition result: a
modular, build-scoped, read-only scaffold with no new game hook and no player
memory dereference.

## Static findings and classifications

| Finding | Classification |
|---|---|
| Build identity: revision 1076226 / SHA-256 AF2F…0781 | `PROVEN_BUILD_1076226` |
| `ClientPlayerInput` reflected layout | `PROVEN_STATIC_BUILD_1076226` |
| InventoryTransferAction consumer at `0x371810..0x37229F` | `PROVEN_BUILD_1076226` |
| Concrete owner of that dispatch context | `UNSOLVED` |
| Local-player entity/pointer | `UNSOLVED` |
| Health current/max | `UNSOLVED` |
| Stamina current/max | `UNSOLVED` |
| Mana current/max | `UNSOLVED` |
| Player hook/signature/RVA | `UNSOLVED`; profile RVAs are deliberately zero |
| Bounded future diagnostic queue | `PLANNED`, capacity 32 |

Current reflection independently identifies `keen::ecs::Health`, `Stamina`,
and `Mana` as 0x44-byte server-only/do-not-save components. Each exposes hidden
`definition` at `+0x14` and `dataStorage` at `+0x24`; the shared storage layout
and live owner are unresolved. It also identifies dynamic/do-not-save
`NetworkHealth` (0x08: reflected `health +0x00`, `healthMax +0x04`) and
`NetworkStamina` (0x04: uint16 `stamina +0x00`, `staminaMax +0x02`). These are
`PROVEN_STATIC_BUILD_1076226` layout facts only. No equivalent NetworkMana type
was found by the bounded name query, and none of these types is tied to the
local controlled entity or a native consumer.

The action consumer is not promoted to player identity. It proves an action
path, not a controlled-character owner or vital component.

## Implementation

`PlayerObserver.c/.h` owns state, bounded sample storage, request bookkeeping,
and clean shutdown. `PlayerBuildProfile.h` centralizes the supported build and
explicitly absent observer points. `ArchitectNativeRuntime.c` hosts the module
and publishes `bridge/player_state.json` with the existing JSON validation,
temporary sibling, and atomic replace mechanism.

The F7 registry contains one read-only `player.inspect` command. The dispatcher
reads schema-v1 state without inventing data. Character Editor displays local
player status and each vital as `Not mapped`; all fill/set/max/infinite controls
remain disabled.

## Expected state before evidence

```json
{
  "schemaVersion": 1,
  "sessionId": "v035-...",
  "build": {"revision": 1076226, "supported": true},
  "observer": "player_observer",
  "localPlayer": {
    "status": "UNSOLVED",
    "candidateEntityId": null,
    "candidatePointer": null,
    "identityEvidence": []
  },
  "vitals": {
    "health": {"status": "UNSOLVED", "current": null, "max": null, "source": null},
    "stamina": {"status": "UNSOLVED", "current": null, "max": null, "source": null},
    "mana": {"status": "UNSOLVED", "current": null, "max": null, "source": null}
  },
  "diagnostics": {
    "probeActive": false,
    "runtimeProbeReady": false,
    "boundedCapacity": 32,
    "lastFailureReason": "No validated local-player or vital observation point; probe disabled fail closed."
  }
}
```

A future successful observation session would retain this schema but publish a
non-null entity/pointer only with repeatable ownership evidence, and each vital
independently with a build-specific status, current/max values, and source.
Diagnostic samples must remain bounded and carry tick, phase, identity evidence,
raw value, width, and readability. No plausible-looking value is sufficient.

## Build and verification

From an MSVC x64 developer environment, assemble the existing hook shims, then:

```text
cl /nologo /c /O2 /GS- /Zl /W4 /TC runtime\native\source\ArchitectNativeRuntime.c
link /nologo /dll /machine:x64 /nodefaultlib /entry:DllMain ... kernel32.lib vcruntime.lib
python tools\run_offline_regression.py
```

Runtime checklist:

1. Use the exact supported executable and start Architect normally.
2. Confirm v0.35.0 identity and existing F7/F8 behavior.
3. Open F7 → Character Editor; confirm all three values say `Not mapped`.
4. Invoke `player.inspect`; expect `state: unsolved` with read-only data.
5. Validate `bridge/player_state.json`, then exercise existing inventory and
   building observers.
6. Stop normally; confirm `diagnostics.stoppedCleanly: true` and existing hook
   bytes are restored.

Regression checklist: F7/F8 toggle, command ACK/history, BuildingPlaceEvent,
inventory semantic events, carrier observation, atomic state publication, and
clean unload.

## Safety and next experiment

No new detour, pointer scan, game call, vital read, or player-state write is
introduced. The only added runtime write is the bridge JSON file. Failure is
isolated to PlayerObserver state publication.

## Build-profile mismatch correction

The first CODE-0021 build initialized PlayerObserver immediately after PE
discovery, before `install_building_place_hook()` performed Architect's unique
BuildingPlace signature plus allocator-sequence validation. Consequently
`g_buildFingerprintValidated` was still its default `false`, even for the exact
supported executable. This was an initialization-order integration defect, not
a stale profile or changed game binary.

PlayerObserver now initializes after canonical signature validation and accepts
the build only when all of the following agree: canonical fingerprint true,
exactly one BuildingPlace signature, PE timestamp `0x6A4236C8`, and image size
`0x02DA7000`. The external injector continues to require executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
The bridge reports these validation facts. No hash, signature, or PE gate was
removed or broadened.

The smallest next research step is offline-first: xref the reflected
`NetworkHealth` and `NetworkStamina` type identities and find current-build
native consumers that access both named fields. In parallel, trace the shared
0x44-byte vital `dataStorage` type without assuming it contains current/max.
Only after a unique,
signature-validatable vanilla path also exposes a stable controlled-player
identity should a bounded observe-only hook be proposed. Runtime validation must
then use full→consume→recover stamina, baseline→cast→recover mana, and
baseline→damage→heal health sequences across repeated samples.
