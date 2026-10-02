# EML API guide

The Lua `game` table exposes two independent compatibility values:

- `game.version` is the detected Enshrouded/KFC game build.
- `game.api_version` is the EML Lua API contract version (`1.3` in the current source).

Modules should check both values before using resource or registration APIs.
Manifests use `required_loader_api` for named capabilities and
`required_loader_api_version` for version constraints such as `>=1.2`.

EML writes its API contract version to the fresh-session log when the Lua
`game` table is initialized. Control Center reads that event only after the
latest type-registry session boundary and uses it for module compatibility
and health reports. If the loader does not report a version, compatibility is
shown as unconfirmed; it is not inferred from the source checkout.

Deployment checks enabled modules against the observed API version before
writing package files. An enabled module with an explicit API requirement
is blocked when the version is unknown or incompatible. Invalid version
constraints are rejected. Modules without an API requirement retain their
existing deployment behavior; disabled modules do not impose API requirements
on the active package. Consult the release manifest to identify the packaged
build and its verification evidence.

The verified runtime route supports typed resource registration, GUID/part
assignment, type-index retention, enumeration, metadata lookup, and bounded
cloning for the proven resource families. Use the packaged Lua helper rather
than guessing fields. API behavior is build-specific; check compatibility
before execution and fail closed for unsupported types.

API 1.2 adds bounded metadata enumeration:

```lua
local rows = game.assets.get_resource_metadata_by_type(type_name, 32)
```

The optional limit caps returned identities without decoding resource payloads.
Type-specific enumeration no longer preallocates a Lua table sized for the
entire game database. Use this route for discovery before any payload lookup.

API 1.3 adds metadata-only reverse lookup by GUID:

```lua
local identities = game.assets.get_resource_metadata_by_guid(resource_guid)
```

Each returned row contains `guid`, qualified `type`, and `part`. The function
returns every matching identity because one GUID can legitimately be used by
multiple descriptor types. It does not decode or materialize payloads. The
first verified use resolved all 32 dependencies of a known animation graph to
42 identities across six resource types in one bounded session.

## Mapped variant values

Some reflected fields are exposed as `MappedVariantValue` userdata. They are
not ordinary Lua tables, so calling `pairs()` on the wrapper can abort module
initialization. Use the packaged helper:

```lua
local variant = kfc.read_mapped_variant(resource.data.someField)
if variant.available then
    print(variant.variant_type)
    local iterator, state, initial, err = kfc.try_pairs(variant.payload)
    if iterator then
        for key, value in iterator, state, initial do
            -- inspect only the bounded payload
        end
    else
        print(err)
    end
end
```

This is read-safe and fail-closed. It does not make an unknown variant
constructible or promote any capability without fresh runtime evidence.

The EML source also contains a pending mapped-variant improvement that
delegates `pairs()` to the variant payload. It has passed Rust compilation but
must be installed and runtime-tested before being treated as the live loader
behavior. See `research/EML_MAPPED_VARIANT_PAIRS_UPGRADE_20260928.md`.
