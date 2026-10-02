# AI Attack Dependency Mapping — build 1076226

## Evidence

The isolated dependency probe read the first sampled attack description without mutation. It exposed:

- `actionSequence`: `a837f190-d163-4ef5-a48e-3ea7caac7296`
- `attackStyle`: `Normal`
- `selectionChance`: `1`
- threat and range scalars
- zero-valued `executionAttackSequence`

The probe was removed and the stable profile was restored. This is read-only evidence; it does not prove that the referenced sequence can be cloned or registered.

A follow-up fresh-session probe confirmed a boundary in the runtime wrapper: the sampled attack is readable, but `attack.actions` and `attack.commands` are not enumerable userdata (`type=nil`), while `behavior.actions` is exposed as userdata. This means the attack’s sequence reference is currently visible only through the serialized description, not through a directly traversable attack-action collection.

A targeted behavior-action probe showed that the exposed `behavior.actions` value is a `MappedVariantValue`, not a Lua table. Attempting to enumerate it produced a recoverable EML error (`bad argument #1 to 'for iterator' ... table expected, got MappedVariantValue`); EML skipped mod initialization for that session, the game process remained running, and the probe was rolled back. This establishes a wrapper boundary and confirms that probes must type-check mapped variants before iteration.

## Reflected schema mapping

The current build’s reflected registry contains the following relevant types:

| Runtime graph role | Reflected type | Relevant fields |
|---|---|---|
| Arsenal entry | `keen::enemy01::AttackCommand` | `constraints`, `actions` |
| Attack mode data | `keen::enemy01::AttackCommandData` | `mode` |
| Attack action | `keen::enemy01::PlayActionSequenceAction` | `sequence`, `waitUntilFinished` |
| Behavior settings | `keen::enemy01::BehaviorSettings` | timing bounds, cooldown bounds, chance |
| Behavior entry | `keen::enemy01::BehaviorDesscription` | `mode`, `settings` |
| Behavior resource graph | `keen::enemy01::BehaviorDesscriptionResource` | execution/abort constraints, actions |
| Sequence family | `keen::actor::ActionSequence` | trigger and playback context |

The reflected type inventory also includes `keen::ActionSequenceEvent`, but the sampled runtime value has not yet been mapped to a registered resource or a constructible resource graph.

## Clone implications

An AI clone cannot safely be treated as an `EnemyArsenal` plus a new GUID. The minimum dependency closure currently includes:

1. Arsenal identity and registry membership.
2. Attack and behavior collections.
3. Constraints and action collections.
4. `PlayActionSequenceAction.sequence` references.
5. Referenced action-sequence resource identity and nested playback/event data.
6. Spawn/template linkage, animation/VFX dependencies, loot, navigation, persistence, and authority contracts.

The owning `keen::actor::ActorSequenceResource` family is runtime-enumerable with 2,202 resources. A fresh read-only lookup resolved sampled GUID `a837f190-d163-4ef5-a48e-3ea7caac7296` to resource-table key 1450; its sequence was named `Enemy_Fogger_Heavy_Attack03_Chain_3hit_more_turn_events`, contained 41 mapped events, and exposed the first event as `keen::actor::EnableAbilityEvent` with a readable `.value` payload. Evidence is recorded in `research/probe_sessions/actor_sequence_guid_lookup_cycle_20260928/evidence.json`. A write probe is still prohibited until the remaining dependency closure and rollback plan are complete.

A follow-up event-graph inventory read all 41 events and their field names. The graph includes `SetAnimationEvent`, `EnableAbilityEvent`, `DisableAbilityEvent`, `TriggerNoiseEvent`, `SfxNotifierEvent`, `VfxNotifierEvent`, `SpawnImpact`, and `CameraShakeEvent`. The probe completed alongside the stable mod, which applied 1,911 patches, and was then rolled back. Evidence is recorded in `research/probe_sessions/actor_sequence_event_graph_cycle_20260928/evidence.json`.

The offline closure report is now recorded in `research/AI_EVENT_DEPENDENCY_CLOSURE_20260928.md`. It maps 17 of the donor's 45 unique GUID values to known KFC resource archives and classifies the rest conservatively as event-local or unresolved references.

## Status

AI enemy archetype creation remains `research-only`. This document strengthens the donor-preserving clone plan; it does not promote the capability.
