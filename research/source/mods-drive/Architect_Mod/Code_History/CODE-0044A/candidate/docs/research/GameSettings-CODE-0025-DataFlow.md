# CODE-0025 — GameSettings static data-flow convergence

## Result

The deeper offline scan did not produce separate defensible write and readback
boundaries. GameSettings mutation remains blocked and no runtime hook was added.

The machine-readable result is `bridge/game_settings_dataflow_map.json`. It is
gated to revision 1076226, executable SHA-256
`AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`,
PE timestamp `0x6A4236C8`, and image size `0x02DA7000`.

## Registration and descriptor track

The scanner preserved 66 exact string/hash occurrences for `GameSettings`,
`AdminChangeGameSettingsAction`, `ServerConsumedPlayerInput`,
`GameSettingsChangedEvent`, and `GameSettingsPresetsResource`. It followed
bounded 64-bit image-VA and 32-bit RVA references through non-code sections for
three levels, producing 142 explicit edges: 101 in `.rdata` and 41 in `.data`.

The closure reached 79 small code-reference candidates. Seventy-eight fan out
from the broad `GameSettings` descriptor graph; none retains an independently
specific action/event/preset identity. This fan-out is negative evidence:
descriptor reachability alone is insufficient to call these functions action
constructors, consumers, event callbacks, owners, or getters.

Every candidate, exact RVA, apparent function bound, call relationship,
instruction, target data RVA, and propagated type index is recorded in the
JSON candidate table. All have:

- `runtimeHookEligibility: NO`
- no qualified unique signature;
- unknown calling convention and side;
- no understood overwrite span; and
- no proven aggregate argument.

## Versioned-action comparison

Reflection exposes 47 consumed-action version fields in
`ServerConsumedPlayerInput`. This proves a shared layout family, including
`consumedAdminChangeGameSettingsAction +0xC4`. It does not reveal any action's
submitter, generic version comparator, per-action server consumer, or resulting
event/state transition. The machine map therefore records all comparable rows
as layout-only `PROVEN_STATIC_BUILD_1076226`, with submitter, consumer, and
consequence `UNSOLVED`.

Static instructions using displacement `+0xC4` were deliberately treated as a
weak syntactic surface. No candidate intersected that surface with a specific
GameSettings descriptor reference and a substantial `0x90` aggregate
operation. Thus the scan cannot distinguish the consumed version field from
unrelated structures using the same offset.

## Server consumer and changed-event tracks

No function converged on both `AdminChangeGameSettingsAction` descriptor
ownership and `ServerConsumedPlayerInput +0xC4`. No function converged on the
`GameSettingsChangedEvent` descriptor and an aggregate copy/consumer operation.
There is consequently no producer/subscriber map beyond the proven reflection
layout, and no basis for calling any event consumer authoritative.

## Runtime owner and preset tracks

The bounded descriptor graph did not isolate a long-lived owner for the
aggregate. `GameSettingsPresetsResource` remained distinguishable in reflection
but did not converge on a code candidate that also performs a type-supported
full-aggregate copy, clamp, validation, dispatch, or changed-event emission.
Generic `0x90` immediates/displacements were not promoted without descriptor
and system evidence.

## Candidate summary

| Candidate group | RVAs | Evidence | Contradiction | Classification | Hook |
|---|---|---|---|---|---|
| Descriptor-reference closure | Full 79-row table in JSON; begins `0x4835`, `0x49C0`, `0x4AD5`, `0x4C40` | RIP-relative access reaches the bounded registration/data closure | Broad fan-out; no action/event role, aggregate argument, side, signature, or safe overwrite span | `INFERRED_BUILD_1076226` | `NO` |
| `+0xC4` accessors | Preserved as instruction evidence only when intersecting candidates | Possible structure displacement match | Offset is non-unique; no containing-type proof | `UNSOLVED` | `NO` |
| `0x90` aggregate-like operations | Preserved as instruction evidence only when intersecting candidates | Possible size/displacement match | Generic size/offset; no type provenance | `UNSOLVED` | `NO` |
| Dispatch/consumer | none | none met convergence threshold | No specific descriptor + version + payload intersection | `UNSOLVED` | `NO` |
| Readback/event | none | none met convergence threshold | No specific event + aggregate consumer/owner intersection | `UNSOLVED` | `NO` |

No candidate is `OBSERVE_CANDIDATE` or `STRONG_OBSERVE_CANDIDATE`.

## Smallest discriminating experiment

The next useful step remains static, not runtime: load the PE in a tool that can
recover generated registration object boundaries and cross-references with
relocation/type information, then select the descriptor object specifically
owned by type index 2703 or 3410. Trace only the callback/function pointer slots
inside that one object. A runtime experiment becomes justified only if this
yields a unique function with understood arguments and overwrite span.

Mutation remains blocked until both a vanilla action dispatch/consumer and an
independent authoritative aggregate/event readback are separately proven.
