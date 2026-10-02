# Stable loader smoke evidence — 2026-09-28

## Result

Verified fresh stable-profile launch on the pinned build:

`1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`

The game was started with the Enshrouded installation directory as its working directory, allowing the proxy to resolve the game files and produce a fresh EML log boundary.

## Evidence

- Log: `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-28.eml.log`
- Baseline byte offset: `162003`
- Final log size: `166999`
- Fresh session lines: `20`
- Stable module loaded: `enshrouded_mod_hub`
- Fresh-session panic/fatal/loader/init-error markers: none
- Game process remained responsive during startup and was stopped cleanly.
- Live isolation verifier returned `status: ready` and `isolation_ready: true`.

Historical errors earlier in the same rolling log were excluded from this verdict by parsing only the bytes written after the fresh-session baseline. This prevents stale invalid-probe messages from being misreported as current failures.

## Scope boundary

This verifies loader/profile health and does not promote any research-only content capability. Research probes were absent from the live profile during this smoke test.
