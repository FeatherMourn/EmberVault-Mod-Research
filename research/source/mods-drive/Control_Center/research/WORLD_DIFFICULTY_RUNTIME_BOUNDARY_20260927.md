# World and Difficulty Runtime Boundary — 2026-09-27

## Finding

The `world_and_difficulty` module caused the native EML error `panic in a function that cannot unwind` immediately after entering its initializer. The log showed all preceding verified modules completing, followed by:

```text
[ModBrain] Applying World Rules & Game Settings modifications...
panic in a function that cannot unwind
```

No successful lookup or field-write message followed. The failure therefore occurs on the first reflected access to `keen::GameSettingsPresetsResource` or the adjacent `keen::FbUiBundle` path, before Lua can handle an error with `pcall`.

## Safety decision

The module is now fail-closed and classified `research-only`. It does not call `get_resources_by_type` for either unsafe family. It was removed from the verified deployment allowlist, while the other five tuning modules remain available.

## Required next step

Add an EML-side guarded settings-resource API or metadata/preflight capability, then retest one resource family and one field at a time. A Lua `pcall` alone is insufficient because the panic crosses the native boundary and cannot unwind through Lua.
