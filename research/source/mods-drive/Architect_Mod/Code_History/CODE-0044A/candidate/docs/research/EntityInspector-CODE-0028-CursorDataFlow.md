# CODE-0028 — Cursor Target Data-Flow Recovery

## Result

`NO_CURSOR_DATAFLOW_CONVERGENCE`

The offline pass was limited to the two requested fields and exact executable SHA-256 `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`. It did not launch or attach to Enshrouded. Runtime v0.38.0 and the CODE-0027 zero-hook state are unchanged.

## Recovered metadata roots

| Field | Descriptor | Qualified-name string | Field-name string | Primary registry entry |
|---|---:|---:|---:|---:|
| `CursorSelectObjectAction.selectedObjectId +0x08` | `0x196D820` | `0x1C33C30` | `0x13FBC50` | `0x1817920` |
| `ClientCursor.previousSelectedEntityId +0xC0` | `0x17B4320` | `0x1C70818` | `0x1C6FCE0` | `0x1817E80` |

Both registry entries prove one indexed descriptor table:

```text
0x1817920 - 2670 * 8 = 0x18125B0
0x1817E80 - 2842 * 8 = 0x18125B0
```

Thus `0x18125B0` is supported as the primary reflection descriptor registry base with eight-byte entries. This is type metadata identity, not a live ECS component registry or entity resolver.

Additional absolute references were preserved in `bridge/cursor_target_dataflow.json`. Field-name pointers are not unique field identities because the same strings participate in multiple generated metadata records.

## Relocation-aware code-xref result

The analyzer followed the two exact descriptors, their field-name pointer sites, their descriptor reference sites, and the correlated primary registry base. It decoded the executable `.text` section using x86-64 instruction semantics and checked RIP-relative memory operands and immediates.

No function directly references any exact rooted address. Consequently, there is no bounded descriptor-rooted function in which a `+0x08` or `+0xC0` memory access can be assigned to either requested field.

| Requested boundary | Result | Reason |
|---|---|---|
| `selectedObjectId` producer | `UNSOLVED` | No proven live action base or writer |
| `selectedObjectId` consumer | `UNSOLVED` | No proven live action base or reader |
| `previousSelectedEntityId` writer | `UNSOLVED` | No proven live `ClientCursor` base or writer |
| `previousSelectedEntityId` reader | `UNSOLVED` | No proven live `ClientCursor` base or reader |
| Live `ClientCursor` instance | `UNSOLVED` | Reflection registry contains descriptors, not components |

Scanning arbitrary instructions for displacement `0x08` or `0xC0` would generate many unrelated matches. Without base-object provenance, such a match is explicitly rejected as field evidence.

## Hook decision

No candidate RVA or signature exists. Function boundary, arguments, result structure, target lifetime, unique signature, and relocatable overwrite span are therefore absent. No observer hook is justified or installed.

There are no changes to entity state schema, F7 routing, Building, Inventory, Player, GameSettings, command bridges, or mutation behavior.

## Artifacts and reproduction

Run:

```powershell
python tools\EntityInspector\recover_cursor_dataflow.py
python -m unittest discover -s tools\EntityInspector\tests -v
```

Machine-readable output: `bridge/cursor_target_dataflow.json`.

## Next narrow boundary

The next defensible static step is to recover the generic ECS descriptor-index consumer that obtains descriptor entries indirectly rather than through a direct RIP-relative reference, then identify systems whose declared query/component sets include reflection indices 2670 or 2842. This must remain descriptor/query rooted; a global `+0x08`/`+0xC0` instruction search or heap scan is not justified.
