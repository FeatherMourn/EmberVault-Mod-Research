# Independent Enshrouded table build plan

## Objective

Build a new table from independently gathered observations, using the supplied table only to define the desired behavior and test targets.

## Phase 0 — controls and evidence

Create a disposable world, backup saves, record executable/build identity, and define a one-feature-at-a-time test log. Keep a clean process restart between risky experiments.

## Phase 1 — observation

Start with read-only stat and item-pointer discovery. Confirm scan uniqueness, pointer lifetime, field type, and invalidation events. Do not write values yet.

## Phase 2 — low-risk calculation hooks

Investigate one resource or multiplier site. Prove the calculation by observing inputs, output, and continuation behavior. Implement a reversible hook with explicit original-byte restoration and a disable test.

## Phase 3 — movement and survival

Add speed/jump and depletion-related features separately. Test normal movement, slopes, gliding, falling, combat, zone transition, save/reload, and disable while active. Check physics and stack/register state.

## Phase 4 — progression and stat writes

Only after observation confirms the target is canonical state should you test XP, skills, rested bonus, or stat edits. Test rollback, save/reload, new character, and multiplayer authority.

## Phase 5 — inventory object mutation

Use disposable items. First validate amount-only edits, then inspect upgrade metadata, then consider reroll/change/delete. After each action verify inventory count, UI, save reload, reconnect, and world/container consistency.

## Phase 6 — teleport and time

Implement manual slots before fixed destinations. Validate player identity, streamed-area readiness, collision, fall state, and world context. Treat time edits as potentially persistent until proven otherwise.

## Feature acceptance template

For each feature, record:

```text
Behavior:
Implementation class:
Fresh scan strategy:
Observed data type:
Pointer lifetime:
Original instructions and continuation: documented privately, not copied from reference
Enable/disable proof:
Displayed/cached/player-state/calculation/inventory/world category:
Mechanic hypothesis:
Confirmed observations:
Interpretations:
Risks:
Save/reload result:
Multiplayer result:
Status:
```

## Required status progression

Use these exact statuses: Behavior confirmed by working reference; Static implementation understood; Semantics inferred; Requires runtime evidence; Unsafe to reimplement yet; Ready for independent implementation. A feature may carry several statuses when behavior is known but implementation safety is not.

## Stop conditions

Stop and return to observation if a scan is non-unique, a pointer survives unexpectedly after object replacement, a disable leaves modified bytes, a save changes unexpectedly, or a hook alters unrelated behavior. Do not infer missing offsets, registers, AOBs, or semantics.

## Suggested test matrix

| Test | Low-risk calculations | Pointers | Inventory/progression | Teleport/time |
|---|---:|---:|---:|---:|
| Enable/disable/re-enable | yes | yes | yes | yes |
| Process restart | yes | yes | yes | yes |
| Zone/map transition | yes | yes | yes | yes |
| Save/reload | yes | yes | mandatory | mandatory |
| New character/world | useful | useful | mandatory | mandatory |
| Multiplayer/host/client | useful | useful | mandatory | mandatory |
| Byte/symbol/allocation cleanup | mandatory | mandatory | mandatory | mandatory |

## Attribution and originality

Document the reference as a behavioral target. Maintain fresh notes and signatures, and avoid copying reference-specific names, comments, hierarchy, AOB strings, offsets, or code. Publish only independently derived implementation details and clearly mark hypotheses.
