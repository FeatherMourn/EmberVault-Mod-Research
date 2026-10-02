# Stable Loader Smoke Evidence — 2026-09-27 21:50 UTC

## Scope

Controlled live launch of the installed Enshrouded build using the production
stable profile. Research-only and unclassified modules were not enabled.

## Environment

- Game directory: `H:\SteamLibrary\steamapps\common\Enshrouded`
- Game build: `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`
- Live module: `enshrouded_mod_hub`
- Live module feature state: `stable`
- Live module capabilities: `patch`
- DLL present: yes
- Log: `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-27.eml.log`

## Observed results

- A fresh EML session was observed after the baseline log timestamp.
- EML reported `No changes detected, skipping patching`.
- The type registry loaded successfully.
- The stable module was discovered and the runtime loader attached.
- The observed build exactly matched the expected EML build:
  `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`.
- The Enshrouded process remained running after the controlled launch.
- The latest log contained no `ERROR`, `error`, `panic`, or `fatal` entries.
- Live preflight reported `status: ready` and `isolation_ready: true`.

## Verification commands

```text
python tools/verify_live_loader.py H:\SteamLibrary\steamapps\common\Enshrouded --mod-id enshrouded_mod_hub --require-isolated --log-since <baseline-mtime>
```

Result: exit code 0; `fresh_session_observed: true`; no research-only or
unclassified modules; `build_compatibility.status: compatible`.

## Limitations

This is a loader/runtime smoke test, not proof that every gameplay setting is
visible or correct in a save. No save data was modified and no research-only
content was enabled.
