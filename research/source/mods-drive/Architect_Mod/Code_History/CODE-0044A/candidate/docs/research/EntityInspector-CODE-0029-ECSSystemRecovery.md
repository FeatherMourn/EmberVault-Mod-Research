# CODE-0029 — ECS Registry Consumer and Cursor System Recovery

## Primary conclusion

`GENERIC_REGISTRY_CONSUMER_ONLY`

No typed ECS system, query, action subscription, event subscription, or owned callback was recovered for reflection indices 2670 or 2842. CODE-0030 observe-only probing is not justified. Runtime v0.38.0 remains unchanged and no hook was installed.

## Exact registry lookup model

The primary registry remains proven at `0x18125B0`, with eight-byte descriptor-pointer entries:

```text
descriptor = *(0x18125B0 + reflectionIndex * 8)
```

Validation:

| Index | Type | Entry | Descriptor |
|---:|---|---:|---:|
| 2670 | `CursorSelectObjectAction` | `0x1817920` | `0x196D820` |
| 2766 | `ClientCursorInput` | `0x1817C20` | `0x19E08C0` |
| 2842 | `ClientCursor` | `0x1817E80` | `0x17B4320` |

Two generated global records contain the registry base at `0x1830AE0` and `0x1832620`. The adjacent qword is `0x383E` in both records. It is preserved as an observed value; its semantic name is not assumed.

## Generic consumers

### Registry owner accessor — `0x75E710`

- Bounds: `[0x75E710, 0x75E718)`
- Signature: `48 8D 05 09 3F 0D 01 C3`
- Operation: returns the owner record at `0x1832620`
- Registry provenance: owner `+0` points to `0x18125B0`; owner `+8` is `0x383E`
- Direct callers: `0x800C6D`, `0x802F94`
- Arguments: none observed
- Classification: `PROVEN_STATIC_GENERIC_ACCESSOR`

### Generic descriptor resolver — `0x802F50`

- Bounds: `[0x802F50, 0x802FDF)`
- Signature prefix: `48 89 5C 24 08 57 48 83 EC 20 48 8B 3D 97 53 70`
- Input: caller-provided 32-bit key in `ECX`, retained in `EBX`
- Fast path: generic cache lookup through `0x802A20`; returned mapped index selects an eight-byte pointer
- Fallback: calls `0x75E710`, reads table/count from owner `+0/+8`, advances through eight-byte descriptor pointers, and compares the input key with descriptor dword `+0x50`
- Return: matching descriptor pointer or null
- Direct callers: 179
- Classification: `PROVEN_STATIC_GENERIC_DESCRIPTOR_RESOLVER`

This is generic reflection infrastructure. The caller key is not proven to be the numeric reflection index. It is therefore not a cursor callback and must not be hooked.

## Typed memberships

### Index 2670

- `0x1817920`: primary reflection registry entry; proven static membership.
- `0x19DF5C0`: generated metadata collection; no ECS query/system owner or code pointer.

### Index 2842

- `0x1817E80`: primary reflection registry entry; proven static membership.
- `0x17F3CA0`, `0x182FAC0`: generated metadata collections; no ECS query/system owner or code pointer.

### Supporting index 2766

- `0x1817C20`: primary reflection registry entry.
- `0x19E3200`: generated metadata collection; no typed owner or callback.

No non-primary bounded object contains a proven 2670/2842 or 2766/2842 typed pairing. Numeric proximity is not treated as correlation.

## System, callback, and field results

- Typed systems: none.
- Typed queries: none.
- Owned callbacks: none.
- Client/server side: unknown.
- `selectedObjectId +0x08` accesses inside typed callbacks: none.
- `hoveredVoxelMaterialId +0x8A` accesses inside typed callbacks: none.
- `previousSelectedEntityId +0xC0` accesses inside typed callbacks: none.
- Local-player/input correlation: none.

Because no typed callback establishes base-object provenance, whole-binary offset searches remain prohibited.

## Rejected paths

- `0x75E710` and `0x802F50`: generic infrastructure; concrete cursor type identity is not preserved into a callback.
- Non-primary descriptor-pointer collections: generated type metadata, with no query/system ownership or callback.
- Machine-code immediates equal to 2670, 2766, or 2842: rejected without structural context.
- Global `+0x08`, `+0x8A`, or `+0xC0` searches: rejected without a typed base object.
- Generic registry hook: explicitly disallowed and offers no stable target identity.

## Safety and next boundary

No runtime experiment is justified. The smallest future static step would require new evidence identifying the generated ECS query/system-registration format while preserving concrete descriptor membership into an owned callback. Without that new structure, the strict stop rule applies.

Machine-readable evidence is in `bridge/entity_cursor_system_map.json`. Regenerate it with:

```powershell
python tools\EntityInspector\recover_ecs_registry_consumers.py
```
