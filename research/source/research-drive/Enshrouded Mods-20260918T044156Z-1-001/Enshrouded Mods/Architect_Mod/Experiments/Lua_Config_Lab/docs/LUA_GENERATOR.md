# Lua generator

The generator produces the `src/mod.lua` body for a startup EML patch mod. The
output is **deterministic**: identical input produces byte-identical output (no
random GUIDs or timestamps in the behavior code; the timestamp lives only in
`generated_manifest.json`).

## Behavior contract

Generated Lua:

1. Resolves the requested resource type through `game.assets.get_resources_by_type(...)`.
2. Validates resource selection (FIRST / ALL / MATCH).
3. Navigates the requested field path.
4. Optionally compares the expected original value.
5. Applies the replacement value, then **reads it back** to detect a failed write.
6. Records diagnostics via `print` and `io.export(...)`.

It never performs live process modification, and never invents missing
resources or fields.

## Structure

A shared helper section is emitted once, followed by a compact edit table:

```lua
local EDITS = {
    { resourceType = "keen::BalancingTable", mode = "first",
      path = { "playerBaseStamina" }, value = 500, hasExpected = false },
    ...
}
```

Helpers:

* `read_path(root, path)` — navigate a path (string components are fields,
  number components are 1-based array indices).
* `write_path(root, path, value)` — write the leaf of a path.
* `resolve_resources(edit)` — FIRST / ALL / MATCH resolution.
* `apply_one(edit, resource, result)` — precondition check, write, readback.
* `lua_string` / `path_string` — diagnostics formatting.

## Literal serialization

Profile input is treated as **data**. Values are never pasted raw into the Lua.

* strings are escaped (quotes, backslashes, `\n`, `\r`, `\t`, and control
  characters as `\ddd`);
* numeric values are emitted from parsed numbers (integers for integer kinds,
  floats with a decimal point for float kinds); non-finite floats are rejected;
* booleans are emitted as `true`/`false`;
* resource type / path values come from validated schema entries.

## Target modes

| Mode | Generated behavior |
|---|---|
| `first` | `resources[1]` only |
| `all` | iterate all resources |
| `match` | filter by `selectorField == selectorValue`; 0 matches → skip, >1 → fail closed |

## Diagnostics

The mod writes a JSON status object with `io.export("<mod_id>/status.json", ...)`
and prints a summary line. Per-result fields include resource type, mode, path,
GUID, status (`applied`/`error`), and an error string (including
`precondition mismatch`, `readback mismatch`, `enumeration_failed`,
`selector_no_match`, `selector_multiple_matches`, ...).

## Known-good baseline

The EML layout (`mod.json` + `src/mod.lua`, `capabilities: ["patch","export"]`,
`io.export`, `print`, `game.assets`, `game.version`) was copied from the existing
working Architect EML mod (`mods/architect_toolkit`).
