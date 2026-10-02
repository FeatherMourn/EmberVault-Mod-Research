# Placement Blueprint Authority — static map v1

Status: **STATIC / OBSERVE-FIRST** for Enshrouded revision 1076226.

## v0.31 result

The one-shot carrier forwarded Foundation ID `950598916` for both raw events
of a wall placement whose original ID was `948722226`. Restoration succeeded,
the event was inside the ten-second arm window, and the user-confirmed world
geometry remained the wall. Therefore local fifth-argument substitution is
`PROVEN_BUILD_1076226`, while its authority over committed voxel geometry is
`DISPROVEN_BUILD_1076226`. This is a useful negative result, not a failed
experiment, and the same mutation must not be retested.

## Known placement flow

The connected static chain is:

```
0x280F86 call 0x3E2CD0
  -> 0x3E2D47 call 0xCB4B50; 0x3E2D4C mov r12,rax
  -> 0x3E34E1 mov eax,[r12]
  -> 0x3E34F1 mov [rsp+0x20],eax
  -> 0x3E3505 call 0x3EBB70
```

`0x3E2CD0` computes integerized position/orientation and clamped volume from
the R15 transform-like input. The wall event’s volume was already derived as
4 × 4 × 0.5 before the helper call. The cache consumer family
`0x3E40D0..0x3E4838` uses `RSI+0xF0` and `0xCA90E0`, but direct identity with
the helper context or the +0x48 child is not established.

## Context +0x48 child

Runtime observation gives `BuildingPlaceEvent.context + 0x48` as a readable
candidate object. In the wall capture, neutral fields `unknown_1C` and
`unknown_30` both contained `948722226` before and after forwarding. Their
concrete type, allocation owner, lifetime, writers, and semantic roles remain
unknown. Equal values are not sufficient to call either field authoritative.
The static map records connected reads only where evidence exists and does not
claim those reads alias the child.

## Resolution and volume roles

`R12[0]` is a proven tracking/provenance identity. The runtime placement record
layout is `+0x00` item ID, `+0x04/+0x0C` dimensions, `+0x10` signed relative
payload offset, `+0x14` payload length, and `+0x18` compression. Its payload
formula is `(record+0x10) + sign_extend(*(int32*)(record+0x10))`.

The key unresolved boundary is the first common producer that supplies both a
concrete blueprint/occupancy record and the volume used to construct the event.
Until that producer is found, the existing helper hook is useful only as a
low-risk observation point.

## Safe next step

Keep the stable `BuildingPlaceEvent` observer and perform bounded static
analysis of connected producers/consumers. Do not hook `0xCB4B50`, `0xCA90E0`,
`0x3E2CD0`, or the rejected selector path, and do not mutate the +0x48 child.
The machine-readable evidence is in
`bridge/placement_blueprint_authority_static_map.json`.
