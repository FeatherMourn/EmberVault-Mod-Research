# Public EML/KFC resource lookup study

Scope: public/open-source EML/KFC documentation and the public
`Brabb3l/kfc-parser` project only. No restricted mod source was copied or
mechanically translated. This is an offline research note; it does not attach
to the game or expose a native pointer.

## PROVEN FROM SOURCE

The public resource documentation describes a resource as a typed binary asset
identified by a GUID, qualified type name, and (where applicable) part index.
`game.assets.get_resource(...)` returns a Resource userdata value, while its
`data` member exposes the typed, reflected fields. The API also documents
`game.assets.get_resources_by_type(typeName)` for obtaining all resources of a
qualified type. The getting-started examples use the returned resource's
`.data` table and export results through the documented export directory.

Public references:

* <https://brabb3l.github.io/kfc-parser/eml/api/assets/resource.html>
* <https://brabb3l.github.io/kfc-parser/eml/api/assets/>
* <https://brabb3l.github.io/kfc-parser/eml/develop/getting_started.html>
* <https://github.com/Brabb3l/kfc-parser>

The public repository is a parser/EML tooling project. It establishes the
shape of the Lua-facing resource abstraction and reflection-driven field
access; it does not promise that a Resource userdata value is a raw native
object pointer.

## INFERRED

The current toolkit's `game.assets` bridge likely resolves a typed resource
through an internal resource manager and wraps that result as Lua userdata.
That is consistent with the documented GUID/type lookup and with the
repository's reflected `.data` fields, but the public API does not expose the
manager address, cache slot, allocator metadata, or a stable native pointer
contract. Any native pointer relationship must therefore be established from
current-build executable evidence, not from a Lua GUID or a guessed layout.

Likewise, a resource returned by `get_resources_by_type` can be enumerated and
read through its documented fields, but this does not prove that its backing
object is the placement cache record used by the native construction path.

## NOT APPLICABLE TO CURRENT EML BUILD

No public documentation reviewed here exposes a supported native pointer
lookup endpoint equivalent to:

```
resource type descriptor/hash -> resource manager -> loaded native pointer
```

`loader.runtime.register_dll(...)` is not a public resource-manager lookup
API in the cited EML resource documentation, and no public source reviewed in
this batch establishes a contract for obtaining Enshrouded game-memory
pointers from it. The toolkit therefore leaves the native registry endpoint
unresolved and keeps the future diagnostic plan read-only and disabled.

This note intentionally does not treat GUID stringification as an asset API
input, and it does not recommend arbitrary process-memory scanning.
