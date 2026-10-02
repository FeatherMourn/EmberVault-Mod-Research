# EML mapped-variant `pairs()` upgrade — 2026-09-28

## Source change

The EML source at `H:\enshroudedresearch\external\kfc-parser-source` now gives
`MappedVariantValue` a `__pairs` metamethod. The implementation delegates
iteration to the variant payload while retaining the existing `.type` and
`.value` fields. Payload creation is cached through one bounded accessor.

This prevents the previous failure mode where a mod called `pairs()` directly
on a mapped variant and EML aborted mod initialization with:

```text
bad argument #1 to 'for iterator' (table expected, got MappedVariantValue)
```

## Verification

- `cargo check -p mod-loader-lua` passed.
- `cargo build -p mod-loader-lua --release` passed.
- `cargo build -p dinput8-proxy --release` passed.
- Existing warnings are unrelated unused imports, lifetime diagnostics, and
  Windows linker export warnings.

The rebuilt proxy was installed temporarily with a reversible backup at
`H:\Enshrouded_LiveBackup_20260928_041823_mapped_variant_runtime`.
A fresh isolated probe then completed successfully on build `1076226`:

- `pairs(behavior.actions)` iterated without the previous `MappedVariantValue`
  error;
- the first action entry exposed `state`, `minTime`, and `maxTime`;
- the probe recorded `FIELD_COUNT|behavior.actions|3`;
- the normal `enshrouded_mod_hub` subsequently applied all 1,910 patches;
- the probe was restored and the previous stable DLL was put back afterward;
- `verify_live_loader.py` returned `status: ready`, with one stable mod and no
  research or unclassified modules.

Runtime evidence is recorded in
`research/probe_sessions/enemy_behavior_pairs_runtime_cycle_20260928/evidence.json`.

A second fresh sequence probe also completed on the rebuilt proxy. It showed
that `behavior.actions` is traversable and exposes the same three fields, while
the selected donor's `attack.actions` and `attack.commands` are empty (`nil`).
That result distinguishes a real donor-schema boundary from the former Lua
wrapper failure. Evidence is recorded in
`research/probe_sessions/enemy_arsenal_sequence_pairs_cycle_20260928/evidence.json`.

An initial lookup of `keen::actor::ActionSequence` returned `COUNT|0`, but the
offline KFC archive search identified the actual owning family as
`keen::actor::ActorSequenceResource`. A corrected fresh probe then exposed
2,202 resources at runtime, including `resourceId`, `subSequences`, sequence
names, durations, and mapped event payloads. This corrected the earlier false
boundary caused by targeting the inner type instead of the resource type.
Evidence is recorded in
`research/probe_sessions/actor_sequence_resource_cycle_20260928/evidence.json`.

## Safety boundary

This source upgrade proves safe read-only traversal of one mapped AI action
payload. It does not prove that AI action payloads are constructible,
cloneable, persistent, or multiplayer-authoritative. AI enemy creation remains
research-only until the complete dependency closure is mapped and a
reversible write probe is verified.

The follow-up GUID lookup also succeeded: the sequence reference resolved to
an `ActorSequenceResource`, and its mapped event exposed both `.type` and
`.value` safely. This advances the AI work from registry discovery to a
concrete donor graph, but does not yet authorize mutation.

The resolved donor graph was then inventoried read-only across all 41 events;
animation, ability, audio, VFX, noise, impact, and camera-shake event schemas
were traversable without a loader panic. The graph is now understood well
enough to plan a donor-preserving clone, but mutation remains gated on
dependency closure and rollback validation.
