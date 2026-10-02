# Item Observer Descriptor / Type-Owner Bridge Research v5

## Proven

The four shared `+0x10` targets are relocation-backed `.rdata` objects with
no decoded `.text` xrefs and no field resolving into `.text` in the inspected
`+0x100` windows.

Their first fields resolve to readable type-like names:

| Candidate | `+0x00` / `+0x10` | `+0x20` |
| --- | --- | --- |
| `0x160BFC0` | `UiLocaTagReference` | `keen::ds::UiLocaTagReference` |
| `0x1857610` | `UiLocaTagReference` | `keen::UiLocaTagReference` |
| `0x1908FB0` | `VersionedData` | `keen::ds::VersionedData` |
| `0x18BAFA0` | `VersionedData` | `keen::VersionedData` |

This establishes a descriptor-like family relationship. It does not establish
an inventory action consumer, action handler, or standard MSVC RTTI layout.

## Descriptor comparison / relocations

49 relocations overlap the four bounded descriptor windows. Resolved targets
are `.rdata`; none is `.text`. The descriptors differ in later fields and are
not one identical fixed object.

## Incoming / outgoing references

The broad file-level incoming-reference scan yields many raw numeric candidates
(4,646) and no decoded code reference. Those values do not form a defensible
owner chain and are not elevated beyond raw scan evidence. Valid outgoing
pointer fields in the inspected windows point into `.rdata` only.

## Shared owner and family result

The strongest result is negative for inventory routing: the action entries
point at generic descriptor/type-like metadata associated with localized tag
and versioned-data representations. The four objects are not the missing
static bridge to executable inventory behavior.

## Disproven

* The `+0x10` targets are not direct function-pointer tables in the inspected
  windows.
* No static `.text` consumer was found for these descriptor RVAs.
* Previously rejected paths remain rejected: direct FNV storage, direct action
  handler pointer, and `0x389161` as a hook target.

## No-hook decision

**NOT READY.** No executable function, calling context, or safe observation
capture strategy emerged.

## Next research step

The evidence now suggests the action metadata may be consumed through runtime
registration or an indirect lookup not materialized as literal static xrefs.
The strongest next milestone is a narrowly scoped **Read-Only Runtime Metadata
Registration Discovery** design around these known static descriptors—not a
hook or broad process scan.
