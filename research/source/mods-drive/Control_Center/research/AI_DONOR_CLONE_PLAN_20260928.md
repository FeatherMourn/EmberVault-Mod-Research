# AI donor clone plan — build 1076226

This is a research-only plan. It is not a claim that new AI is currently constructible or multiplayer-safe.

## Verified starting point

The runtime registry `keen::enemy::EnemyArsenalRegistryResource` resolved successfully at GUID `cd861d95-a79c-4c11-8b48-8fae34a4156c`. Its `arsenals` collection contained 170 entries. A sampled arsenal exposed `attacks` and `behaviors` userdata collections without mutation.

One sampled attack exposed `description`, `selectionConstrain`, `executionConstrain`, `abortConstraints`, `commands`, and `data`. One sampled behavior exposed `mode`, `settings`, `executionConstrain`, `abortConstraints`, and `actions`.

The reflection registry contains matching graph types including `keen::enemy01::AttackCommand`, `AttackCommandData`, `BehaviorDesscriptionResource`, and `BehaviorSettings`.

## Planned clone boundary

The first write experiment must deep-copy one donor arsenal and its nested attack/behavior graph, assign a new identity only to the clone, validate all nested dependencies before registration, and prove that the donor remains unchanged. The experiment must remain isolated and recoverable.

The dependency probe subsequently identified an `actionSequence` GUID inside the sampled attack description. The reflected schema mapping in `research/AI_ATTACK_DEPENDENCY_MAPPING_20260928.md` shows that this reference belongs to the action-sequence portion of the graph and must be resolved before any clone write is attempted.

## Still unknown

- how EML constructs a new `EnemyArsenalResource`;
- whether nested command, constraint, animation, and VFX references can be cloned safely;
- which spawn/template resource selects an arsenal;
- whether the game accepts a newly registered arsenal at runtime;
- save persistence, server authority, and multiplayer replication.

The next gate is read-only dependency inventory for one donor arsenal. No write probe should be attempted until that inventory and rollback plan are complete.
