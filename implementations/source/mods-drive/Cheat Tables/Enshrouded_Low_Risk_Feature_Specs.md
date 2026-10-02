# Low-risk feature specifications

Current build: `H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe` SHA-256 `AF2F5A1227911D8AA06B3908D6BD021183821CAE14EA91099CB57D0DF990781`.

These are behavior specifications, not implementations. No address, offset, pointer, AOB, or hook is asserted. Each feature remains **Needs evidence** until controlled runtime scans and access/write traces are captured.

| Feature | Intended behavior | Observable | Candidate scan | Key risks |
|---|---|---|---|---|
| Health | Prevent or scale damage without changing max-health rules | Current health falls after enemy hit; death threshold | Unknown numeric type; scan exact current value, then rescan after hit/heal | Authority/cache confusion; save and multiplayer desync |
| Stamina | Prevent or scale action stamina drain while preserving regeneration | Stamina changes after sprint/dodge/glide | Unknown numeric type; scan while stationary and after repeated actions | Infinite-loop/regen interactions; movement desync |
| Mana | Prevent or scale spell cost while preserving regen | Mana decreases after a spell cast | Unknown numeric type; scan before/after identical cast | Spell cost may be temporary calculation |
| XP | Apply configurable multiplier to awarded XP only | XP changes after a known enemy/quest award | Scan exact XP before and after one controlled award | Level-up/save corruption; overflow |
| Durability | Prevent or scale wear on one equipped item | Durability decreases after one controlled use | Scan item durability before/after identical use | Item cache and persistence risk |
| Fall damage | Suppress damage caused by a controlled fall | Health changes after safe-height versus test-height fall | Scan health and trace fall event; do not assume health write is fall-specific | False-positive health hook; death/crash |
| Movement speed | Scale locomotion speed without changing animation state | Distance/time over fixed ground route | Measure externally first; then trace speed calculation | Physics, animation, multiplayer desync |
| Jump height | Scale jump impulse while preserving gravity | Apex height over repeated jumps | Measure apex externally; trace jump input/impulse | Physics instability and fall damage interaction |
| Shroud timer | Pause or scale exposure depletion only | Timer decreases while exposed to shroud | Scan timer while exposed and sheltered | World/UI timer confusion; save/world state |
| Oxygen | Pause or scale underwater breath depletion only | Breath meter decreases underwater | Scan breath during controlled submerged interval | Shared stamina/health fallback; death risk |
| Body heat | Pause or scale cold-area heat loss only | Heat meter changes in cold/warm test areas | Scan heat across equal intervals in each area | Weather/temperature cache confusion |
| Crafting cost | Suppress or scale material consumption for one recipe | Inventory counts before/after one craft | Scan one ingredient count and craft result | Inventory/save corruption; recipe-side effects |

## Required evidence record per feature

For each feature, capture baseline value, changed value, scan type, repeated trigger, access instructions, write instructions, registers/operands, structure context, authoritative-vs-cache classification, instruction boundaries, original bytes, independent AOB uniqueness, preservation analysis, cleanup analysis, and offline test results.

## Status rule

All rows are currently **Needs evidence**. A candidate address is not a confirmed target. A script is not ready merely because it assembles. No live-game claim may be made without an offline disposable-save test performed by the user.
