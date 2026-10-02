# CODE-0032 — First Live Reversible F7 Cheat Sprint

## Result

`NO_SAFE_MUTATION_CANDIDATE_FOUND`

No target was registered and no F7 mutation was enabled. The executable is the canonical revision 1076226 / Hotfix #42 build: SHA-256 `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`, PE timestamp `0x6A4236C8`, image size `0x02DA7000`.

The raw INC-0010 intake was inspected directly where available. Old signatures were used as locators, never as proof. Several match build 1076226 uniquely, which establishes instruction-family continuity but not player ownership or writable scalar identity.

| Feature | External evidence | Current-build mechanism | Result | Reason |
|---|---|---|---|---|
| Camera FOV | `enshrouded_1013216.CT` and `Ember.zip` contain no FOV mechanism | Reflected configuration and `ClientCamera.fovY +0x2C` only | Rejected | No live owner, consumer, refresh path, or independent readback |
| Movement speed | CT captures a 24-byte candidate object and conditionally doubles planar integration | Unique acquisition `0x2CBB33`; arithmetic `0x23AE34` | Rejected | Velocity hook, not an owned speed scalar; local-player correlation absent |
| Full stamina | CT copies indexed sibling `+8` into current or writes `999` | Unique family at `0x23423F`; generic reader at `0x27D8CF` | Rejected | Dynamic selector and sibling semantics unproven; generic reader is overbroad |
| Full mana | CT copies an adjacent indexed value into current | Unique family at `0x2343F5` | Rejected | Maximum semantics and authoritative readback unproven |
| No durability loss | CT returns from a function or changes `ADD` to `SUB` | Unique delta instruction at `0x331A7A` | Rejected | Could increase persisted durability and is unsuitable as the first session-local proof |
| GameSettings stamina/mana/durability | Ember extends preset/UI resource data | Reflected fields `+0x08`, `+0x04`, `+0x14` | Rejected | Live aggregate, dispatch, event/readback, and restoration remain unresolved |

## Why the strongest hooks were not promoted

The movement and stamina candidates are credible `CURRENT_BUILD_STATIC_CANDIDATE` hook sites, not named scalar targets. Neither provides the required original scalar value, bounded direct write, immediate authoritative scalar readback, and restoration of that scalar. Byte restoration proves only that a patch can be removed; it does not prove restoration of game state. Registering either as `NATIVE_MEMORY` would misstate the evidence.

The generic stamina reader is especially unsafe: its signature does not encode the attribute selector, so writing `999` could affect an unrelated indexed attribute. The durability candidates may change persisted item state.

## F7 and harness decision

No control or mutation harness was added because there is no eligible target to test. Existing mutation gates remain unchanged. The next bounded experiment is observe-only: correlate the unique movement acquisition/arithmetic contexts during idle, walk, and sprint, and independently correlate the stamina indexed cell while draining and recovering stamina. Only a unique local-player context with a stable original/readback model may graduate to an experimental named target.

Run the deterministic offline remap audit with `python tools/CheatSprint/analyze_candidates.py`. It writes `bridge/first_cheat_sprint.json`.
