# Resource Metadata Runtime API Boundary

## Controlled result

Build `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`
was tested with the rebuilt EML proxy and an isolated, read-only probe.

The fresh EML log reported:

```text
API|assets=table|metadata=function|resources=function
```

This proves that the live Lua environment exposes both
`game.assets.get_resource_metadata_by_type` and
`game.assets.get_resources_by_type`. The earlier conclusion that the metadata
API was absent was caused by testing an older runtime boundary and is no longer
correct.

## Remaining boundary

The probe emitted the API-surface marker but did not emit `TYPE_ERROR`,
`COUNT`, or `RESULT` before the controlled session ended. Therefore the API's
presence is verified, but successful enumeration of `keen::TemplateResource`
is not yet verified. Possible boundaries are type lookup, enumeration cost,
or an exception/hang during the call.

## Bounded single-resource result

The bounded probe was run through the reliable Steam launch path on the same
build. It emitted:

```text
API|metadata=function
BEFORE_CALL|keen::TemplateResource|9b1b68dd-1d4f-408d-aaf8-5bb82badd7d5
```

It did not emit `AFTER_CALL` before the controlled session ended. This proves
the call enters the EML boundary but does not return for this descriptor family
under the current runtime. It is therefore not safe to use this API for
`keen::TemplateResource` discovery yet.

## Next acceleration step

Use a bounded probe that calls `get_resource_metadata` only for a known small,
already-supported type and records before/after markers. Keep
`keen::TemplateResource` behind an explicit timeout/quarantine boundary. This
separates API invocation from descriptor-family behavior and avoids another
opaque or blocking call.

## Recovery

The probe was removed after the session. Stable preflight passed afterward:
only `enshrouded_mod_hub` remains installed, with no research-only or
unclassified modules.

## Known-safe comparison

The same bounded probe was run against the proven bed donor as
`keen::ItemInfo` (`01474f79-6b5a-4bcd-999d-7e9339fda91c`). It returned:

```text
AFTER_CALL|ok=true|result=table
IDENTITY|guid=01474f79-6b5a-4bcd-999d-7e9339fda91c|type=keen::ItemInfo|part=0
```

This establishes a type-specific boundary:

- `keen::ItemInfo` single-resource metadata lookup: **verified**.
- `keen::TemplateResource` single-resource metadata lookup: **blocking / research-only**.
- EML metadata API exposure: **verified**.

Evidence record:
`research/probe_sessions/iteminfo_metadata_single_20260928.json`.
