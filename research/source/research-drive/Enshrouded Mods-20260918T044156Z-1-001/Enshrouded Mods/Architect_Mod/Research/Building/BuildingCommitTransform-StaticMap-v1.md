# Building commit transform context — v0.28 static map

Static-only analysis of Enshrouded revision 1076226 (SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`). No
process access, hooks, writes, or deployment changes were made.

## Function and inputs

The mapped function is `0x3E2CD0..0x3E354E`. At entry, `R15` is copied from
argument `RDX` (`0x3E2CEF`) and `RSI` from `RCX` (`0x3E2CF6`). `R15` is therefore
an incoming transform/context-like structure; its concrete type is not known.
The bounded pseudo-layout is derived only from actual accesses: qword/dword
scalars at `+0x00/+0x04/+0x08`, a four-lane vector at `+0x0C`, a dword at
`+0x1C`, and a control byte at `+0x20`.

The function resolves records through `0xCA90E0` and `0xCB4B50`, then computes
integerized coordinates, vector fields, and clamped bounds before dispatching
`BuildingPlaceEvent` through `0x3EBB70` at `0x3E3505`.

## Event field data flow

- Position (`+0x08..+0x10`) comes from the caller RDX structure at
  `[RSP+0x70]`, populated with scaled/truncated values (`cvttss2si` at
  `0x3E2FE1..0x3E3006` and `0x3E345E..0x3E3496`).
- Orientation (`+0x14..+0x20`) comes from lanes at RDX structure offsets
  `+0x18..+0x24`, assembled with `shufps` immediately before the event call.
- Volume min/max (`+0x24..+0x38`) come from the R8 structure `[RBP-0x20]`,
  after `maxss/minss` clamping and packing.
- Material (`+0x3C`) is the `R9D` result of `0xCAEC50` (`0x3E3392`).
- Tracking item (`+0x40`) is `[R12+0]`, where R12 is the record returned by
  `0xCB4B50` (`0x3E2D4C`); it is stored as the fifth stack argument at
  `0x3E34F1`.
- Owner (`+0x44`) is read from placement state `RSI+0x134` by the event helper.

These mappings are instruction-backed; semantic names for the input fields,
material value, and owner value remain unresolved.

## Rotation and alternate path

The incoming vector at `R15+0x0C` is repeatedly shuffled and combined with
derived values. A discrete rotation index or 90-degree snap enum was not
found. `0x3E40D0` shares normalized-record and candidate-filter machinery but
uses a distinct caller-owned collection and a different downstream transform /
commit sequence; equivalence to `0x3E2CD0` is not proven.

## Observer decision

No runtime observer was installed. Although `0x3E2CD0` is the commit-path
anchor, its runtime frequency and a safe early instruction window are not
validated. The machine-readable evidence is in
`bridge/building_commit_transform_static_map.json`.
