# Typed registry array findings

## Verified

- game.assets.register_resource(donor.data, 'keen::ItemInfo') returns a
  usable independent resource.
- ItemRegistryResource must be located by searching for a resource whose data
  contains itemRefs; selecting [1] is not reliable.
- #itemRefs reports growth after table.insert(itemRefs, clone).
- dbgNames is a parallel field and can be updated with the same slot.
- The stable furniture fixture changes clone.data.objectId to clone.guid
  before catalog-related registration.

## Not yet verified

- A table.insert into this Rust-backed typed array produces a readable Lua
  value at the new slot. Probe v29 observed length growth but a nil last slot.
- Direct numeric assignment to the next slot is rejected by the runtime
  before post-assignment logging (probe v30).
- Therefore registry length growth alone must not be reported as successful
  item indexing or UI visibility.

## Evidence

- v27: REGISTRY|3520->3521, INDEX_LOOKUP|false
- v28: REGISTRY|3523->3524, INDEX_LOOKUP|false
- v29: ENTRY_SHAPE|rawItem=nil|dataItem=nil|guid=nil
- v30: direct assignment stopped execution after clone registration

The next adapter should inspect the typed element schema and construct the
registry's expected value representation rather than assuming the
register_resource return object is directly insertable.
