# EML runtime evidence

Captured from the installed Enshrouded EML session logs. This document records
what the runtime proved; it does not authorize live mutation by EmberVault.

## Environment identity

- Enshrouded build: `1076226`
- Game branch: `/game38/branches/ea_update_08`
- Game build timestamp: `2026-06-29T10:27:39.052394Z`
- EML Lua API: `1.3`
- Type registry: `.cache/types.json`
- KFC source: `enshrouded.kfc`
- Evidence log: `H:\SteamLibrary\steamapps\common\Enshrouded\logs\2026-09-30.eml.log`

## Proven runtime behavior

The EML session log repeatedly records:

- successful type-registry loading;
- Lua API initialization at version `1.3`;
- execution of the `enshrouded_mod_hub` module;
- access to `keen::BalancingTable`;
- a resolved BalancingTable GUID:
  `82706b40-61b1-4b8f-8b23-dcec6971bda1`;
- successful application of the Mod Hub's progression-balancing patch;
- EML applying the patch set and attaching its runtime loader.

This proves that EML can execute a Lua mod and that the installed Mod Hub can
reach and mutate a BalancingTable resource in this build. The broader
workspace contains a controlled write/readback/restore session for
`BalancingTable.baseCritChance` that completed without a panic, removed the
probe, and restored the stable profile.

Evidence file:
`Control_Center/research/probe_sessions/balancing_table_scalar_write_safe_20260929_evidence.json`

That session proves reversible runtime mutation for one scalar field. It does
not prove that every individual field is accepted or that every mutation
changes gameplay behavior.

## Adapter implication

The first EML adapter can use the existing Mod Hub's declared progression
boundary, with one field changed at a time. The initial scalar write has
already been evidenced on the pinned build using `baseCritChance`; the next
adapter work is integration and evidence ingestion, not repeating that probe.

`player_level_cap` remains a useful future behavior candidate because it has a
clear input mapping and an observable in-game result.

The adapter must still provide its own ownership marker, verified backup,
closed-game gate, exact before/after record, post-launch observation, and
rollback test. The current log is runtime evidence, not a completed adapter
review packet.

## Current status

`experimental`: runtime registration and resource access evidenced.

Verified experimentally: controlled single-field change, in-process readback,
clean restoration, probe removal, and stable-profile restoration.

Still not verified: broad field compatibility, authoritative gameplay effect
for every setting, multiplayer scope, and compatibility after a fresh build
change.
