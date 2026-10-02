# Building Identity Authority — Static Map v1

Status: **observe-only research** for Enshrouded revision 1076226. No process
access, new detour, game-memory write, or placement mutation is used.

## Retired v0.31 experiment

The v0.31 carrier changed the local fifth argument to `BuildingPlaceEvent`
from wall `948722226` to Foundation `950598916` for both observed events and
restored the local value. The user confirmed that committed geometry remained
Wall Straight 4m. Thus the local argument write and logical pair are proven,
but helper-argument control of world geometry is
`DISPROVEN_FOR_WORLD_GEOMETRY_AUTHORITY_BUILD_1076226`. The experiment is
retired; the legacy arm command now fails closed.

## Proven connected flow

```
0x280F86 call 0x3E2CD0
  -> 0x3E2D47 call 0xCB4B50
  -> 0x3E2D4C mov r12, rax
  -> 0x3E34E1 mov eax, [r12]
  -> 0x3E34F1 mov [rsp+0x20], eax
  -> 0x3E3505 call 0x3EBB70
```

`R12[0]` is a tracking/provenance identity. `0x3E2CD0` also derives the
volume before the helper call. The static consumer family
`0x3E40D0..0x3E4838` uses `RSI+0xF0` and `0xCA90E0`; `0x3E74B0` normalizes
runtime blueprint records. Their common producer with committed geometry is
not established.

## Context child and R12

The existing observer reports a readable `context+0x48` child. Neutral names
`candidateItemId_1C` and `candidateItemId_30` are used because both fields
contained the original wall ID before and after forwarding, but no static
alias, writer, type, or lifetime proof connects them to R12 or to occupancy
selection. They remain read-only evidence, not authority candidates.

## Authority boundary

The first unresolved boundary is the upstream producer that supplies both a
selected identity and the runtime blueprint occupancy/payload used for commit.
The BuildingPlaceEvent observer is downstream of that classification and is
kept only for correlation. No safe new observer was justified in this build.

The machine-readable map is
`bridge/building_identity_authority_static_map.json`.
