# Item Observer Metadata / Hash-Dispatch Research v3

## Proven

`scan_item_observer_metadata.py` consumes the v2 call-graph output and inspects
the five `.rdata` objects that directly store a target-name reference.
All candidate pointer-like fields resolve either to `.rdata` or nowhere; none
resolves to `.text`. No repeated entry stride was established.

FNV-1a-32 was tested as a project-supported hypothesis:

| Input | FNV-1a-32 | Matching binary locations |
| --- | ---: | ---: |
| `backpackSplitStack` | `0x823963CB` | 0 |
| `consumedInventoryTransferAction` | `0xAE1161E0` | 0 |

## Inferred

The observed `.rdata` relationships are compatible with metadata, reflection,
or registration data. They do not demonstrate a dispatcher, action hash, or
callback relationship.

## Candidate structures / hashes / code pointers

Five objects are retained as `candidate_metadata_entry_only`. No candidate
hash location or candidate code pointer was found.

## Disproven

The tested FNV-1a-32 values are not stored as direct 32-bit values in this
executable. That does not disprove a transformed or runtime-generated hash;
it eliminates only this direct-storage hypothesis.

## No-hook decision

**NOT READY.** There is no target-specific code pointer, stable entry layout,
or understood argument context.

## Run

```powershell
python tools\ItemObserver\scan_item_observer_callgraph.py
python tools\ItemObserver\scan_item_observer_metadata.py
```

## Next research step

Inspect the larger `.rdata` owner structures around the two VA-backed entries,
including references that may be relocation-mediated or hash-table based. Do
not infer a hook target until that structure reaches validated executable code.
