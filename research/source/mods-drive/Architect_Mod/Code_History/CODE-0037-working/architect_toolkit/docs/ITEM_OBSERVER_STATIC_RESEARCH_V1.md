# Item Observer Static Research v1

This is static discovery evidence only. It does not establish a callback,
calling convention, argument layout, item structure, or a safe hook location.
No native observer was installed from these strings.

The offsets below apply only to the inspected executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.
They are file offsets, not RVAs and not hook addresses.

The current `enshrouded.exe` contains these unique inventory-operation strings:

| Candidate string | File offset | Static interpretation |
| --- | ---: | --- |
| `backpackSplitStack` | `0x1C4D960` | Candidate split-stack UI/action path; no code reference validated. |
| `consumedInventoryTransferAction` | `0x1C58970` | Candidate transfer-action state; no structure or event semantics established. |
| `[inventory] Deleted %k items from stack of %k.` | `0x1403890` | Has one direct string-loading reference at RVA `0x389161`, but it is a diagnostic/log call context, not an inventory-operation hook candidate. |

Related type/action strings have multiple references and are intentionally not
treated as signatures: `ecs::Inventory` (29 hits),
`AdminApplyInventoryCommand` (4 hits), and `ItemStackInfoResource` (9 hits).

## Next research test

For one candidate string at a time, find code references in a disassembler,
then derive a **unique build-specific signature** and validate its surrounding
instructions. Install only an observe-only, argument-preserving hook after
that validation. The hook must publish `bridge/item_capture.json` using schema
v1 and should initially report raw `unknownInventoryArgN` pointers/values only.
Compare distinct item transfers and stack splits before naming any field
`itemId` or `amount`.

`tools/ItemObserver/Find-ItemObserverCandidates.ps1` regenerates
`bridge/item_observer_static_scan.json`. It performs an offline PE scan only;
it never opens Enshrouded or creates a hook. The current scan confirms no
direct RIP-relative code reference for the split-stack or transfer-action
candidate strings.
