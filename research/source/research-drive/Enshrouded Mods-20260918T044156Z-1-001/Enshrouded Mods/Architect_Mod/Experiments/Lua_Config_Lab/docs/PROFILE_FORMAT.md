# Profile format

A profile is the tool's own stable JSON configuration format. Application state
is never written into the generated Lua.

`profile_version` is carried from day one.

## Top-level

```json
{
  "profile_version": 1,
  "name": "Baseline Test",
  "description": "Startup-only Lua resource experiment",
  "game_build": "1076226",
  "types_lua_sha256": "ff345a2e...",
  "edits": [ ... ]
}
```

| Field | Type | Meaning |
|---|---|---|
| `profile_version` | int | format version (currently `1`) |
| `name` | string | profile name |
| `description` | string | optional description |
| `game_build` | string | source game build/revision |
| `types_lua_sha256` | string | SHA-256 of the `types.lua` this profile was created against |
| `edits` | array | the edits (see below) |

If `types_lua_sha256` is empty, no compatibility mismatch is reported.

## Edit

```json
{
  "enabled": true,
  "resource_type": "keen::BalancingTable",
  "target": { "mode": "first" },
  "path": "playerBaseStamina",
  "schema_type": "u32",
  "value": 500,
  "evidence_state": "EXPERIMENTAL",
  "expected_original": 250
}
```

| Field | Type | Meaning |
|---|---|---|
| `enabled` | bool | whether the edit is applied |
| `resource_type` | string | qualified type, e.g. `keen::BalancingTable` |
| `target` | object | resource selection (see below) |
| `path` | string | dotted field path, e.g. `playerBaseStamina`, `sunSetup.zenithAngle`, `values[1]` |
| `schema_type` | string | resolved leaf type signature (e.g. `u32`, `f32`, `string`, `guid`, enum alias name) |
| `value` | scalar | the replacement value (typed) |
| `evidence_state` | string | one of the evidence states |
| `expected_original` | scalar | optional precondition (build-update protection) |

`expected_original` is optional. When present, generated Lua skips the edit (and
records a diagnostic) if the current value no longer matches.

## Target

```json
{ "mode": "first" }
```

```json
{ "mode": "all" }
```

```json
{ "mode": "match", "selector": { "field": "itemId.value", "operator": "eq", "value": 123 } }
```

| `mode` | Meaning |
|---|---|
| `first` | modify only the first resource of the type |
| `all` | modify every resource of the type (requires confirmation in the UI) |
| `match` | modify the resource whose `selector.field` equals `selector.value` |

Selectors support **scalar equality only** (`operator` must be `"eq"`). At
startup, zero matches → skip + diagnostic; multiple matches → fail closed.

## Field path syntax

Paths are dotted, with `[n]` array indices (1-based, matching Lua `ipairs`):

* `playerBaseStamina`
* `gliderConfig.accelerationForward`
* `sunSetup.zenithAngle`
* `values[1]`
* `components[2].value`
