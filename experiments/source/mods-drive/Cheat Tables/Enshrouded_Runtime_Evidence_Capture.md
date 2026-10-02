# Offline runtime evidence capture worksheet

Use one copied disposable save. Capture one feature at a time. Do not enable any existing trainer entry during discovery. Record the executable hash and Cheat Engine version at the top of every session.

## Session header

- Date/time:
- Executable SHA-256:
- Save backup path:
- Offline/local confirmation:
- Feature under test:
- Baseline scenario:
- Changed scenario:

## Per-feature record

- Intended behavior:
- Observable value/action:
- Data type searched: 4-byte / 8-byte / float / double / unknown
- Baseline value and scan result count:
- Trigger action repeated exactly:
- Changed value and rescan result count:
- Candidate address(es):
- What accesses candidate: instruction address, disassembly, count:
- What writes candidate: instruction address, disassembly, count:
- Registers and operands at access/write:
- Surrounding instructions:
- Structure/base pointer hypothesis:
- Gameplay state, cache, UI, or temporary calculation classification:
- Candidate hook/data record:
- Original bytes/value:
- Independent AOB candidate:
- Current-executable match count:
- Instruction boundary review:
- Return-flow review:
- Register/flags/stack review:
- Allocation/symbol ownership:
- Disable restoration result:
- Save impact:
- Multiplayer risk:
- Status: Confirmed / Ready for testing / Needs evidence / Failed / Unsafe

## Feature-specific trigger matrix

| Feature | Baseline | Repeatable trigger | Edge case |
|---|---|---|---|
| Health | Full health in safe area | Same enemy hit repeatedly | Healing, near-death |
| Stamina | Full stamina, stationary | Sprint/dodge/action repeatedly | Regen delay |
| Mana | Full mana | Same spell cast repeatedly | Zero mana, regen |
| XP | Known level and XP | Same controlled award repeatedly | Level-up boundary |
| Durability | One equipped item with known durability | Same use/action repeatedly | Near-zero durability |
| Fall damage | Full health at known safe height | Repeated controlled falls | Non-lethal vs lethal fall |
| Movement speed | Fixed route and timer | Walk/sprint same route | Slope, collision |
| Jump height | Flat ground | Repeated jumps from same start | Ceiling, landing damage |
| Shroud timer | Timer value in shroud | Equal exposure intervals | Shelter transition |
| Oxygen | Full breath | Equal underwater intervals | Surface transition |
| Body heat | Stable warm/cold state | Equal cold-area intervals | Warmth/shelter transition |
| Crafting cost | Known ingredient count | Same recipe crafted once per trial | Missing ingredient, cancellation |

## Stop conditions

Stop immediately if the candidate address is shared by unrelated actions, the instruction writes a UI/cache-only value, the AOB has zero or multiple matches, the hook would overwrite partial instructions, stack alignment is uncertain, or disable does not restore all original state. Mark the feature `Needs evidence`, `Failed`, or `Unsafe` as appropriate.
