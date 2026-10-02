# Item Observer Owner / Relocation Research v4

## Proven

The owner scanner parsed base relocations and found four relocation-backed,
repeated `.rdata` clusters. Each has a structural **candidate stride of 0x30**:

| Cluster anchor | Entries at `+0x00` | Shared `+0x10` target |
| --- | --- | --- |
| `0x1663D60` | `backpackActions`, `backpackSplitStack`, `backpackDeleteItem`, `backpackSalvageItem` | `0x160BFC0` |
| `0x19CF130` | same four names | `0x1857610` |
| `0x19ECB30` | `consumedCursorChangeGrowthLimitAction`, `consumedInventoryTransferAction`, `consumedSortInventoryAction`, `consumedSelectSongAction` | `0x1908FB0` |
| `0x1A13580` | same four names | `0x18BAFA0` |

The fields are relocation-backed absolute pointers in `.rdata`. This proves the
target names belong to repeated metadata-like structures, not isolated string
pool entries. It does **not** prove the meaning of `+0x10`.

## Owner candidates / reference chains

The two target names occur in two parallel candidate clusters each. The
`backpackSplitStack` clusters also include delete/salvage action names;
the transfer clusters include sort-inventory action names. These are the best
current owner candidates.

## Relocation findings

42 relocations occur within the bounded windows. Relevant fields resolve into
`.rdata`; none resolves into `.text`. Four zero-valued `relative_offset32`
results are self-adjacent artifacts and remain candidates, not meaningful
reverse-owner links.

## Structural clusters

The `0x30` layout is **HEURISTIC**: it is supported by recurring relocated
pointer positions and neighboring readable action strings, but owner boundaries
and field meanings remain unproven.

## Code xrefs / candidate functions

No decoded `.text` reference to any candidate entry was found. No candidate
function exists.

## Disproven

* Direct `.text` handler pointer in v3 candidate entries.
* Direct-storage FNV-1a-32 for the two target action names.
* RVA `0x389161` as an inventory-operation hook.

## No-hook decision

**NOT READY.** The metadata layout is now defensibly clustered, but no code
consumer, calling context, or argument-capture strategy has been identified.

## Run

```powershell
python tools\ItemObserver\scan_item_observer_callgraph.py
python tools\ItemObserver\scan_item_observer_metadata.py
python tools\ItemObserver\scan_item_observer_owners.py
```

## Next research step

Trace the shared `+0x10` `.rdata` targets (`0x160BFC0`, `0x1857610`,
`0x1908FB0`, `0x18BAFA0`) outward as potential descriptor/type-owner objects.
The strongest unresolved question is how code reaches these parallel metadata
clusters—possibly through runtime registration or a non-literal lookup table.
