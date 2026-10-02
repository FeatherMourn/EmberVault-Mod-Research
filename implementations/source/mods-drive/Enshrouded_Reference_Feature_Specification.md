# Enshrouded reference-table feature specification

## Scope and evidence standard

This is an independent description of the supplied working Cheat Engine table. The reference file was inspected read-only. It was not copied, edited, or executed, and the game executable was not modified. Exact addresses, AOB byte strings, symbol identifiers, table hierarchy, comments, offsets, and assembler blocks are intentionally omitted.

Evidence labels used below:

- **Behavior confirmed by working reference** — the table exposes the feature and the requester reports it works; the precise in-game side effect still needs controlled testing.
- **Static implementation understood** — the XML structure clearly identifies the implementation family and enable/disable shape.
- **Semantics inferred** — the likely mechanic follows from labels and data flow, but was not proven dynamically.
- **Requires runtime evidence** — pointer lifetime, server authority, save behavior, or exact field meaning cannot be established from the table alone.
- **Unsafe to reimplement yet** — the risk is high enough that dynamic validation is a prerequisite.
- **Ready for independent implementation** — only for a narrowly scoped, low-risk concept after a fresh signature and data-flow investigation.

## 1. Reference-table inventory

The table has these functional areas:

| Area | User-visible entries | Implementation family | Main uncertainty |
|---|---|---|---|
| Player resources | Full health, stamina, mana | Auto Assembler hooks with allocated code | Whether the write changes authoritative state or only a derived value |
| Combat/survival | Easy parry; no fall damage; no durability loss; no shroud/oxygen/cold depletion; stealth mode | Auto Assembler hooks | Exact event and branch semantics |
| Crafting/skills | Free crafting / infinite consumption; available skill points minimum; used skill points zero | Hooks and table-controlled values | Inventory transaction and save implications |
| Rested bonus / XP | Maximum rested multiplier; XP multiplier | Hook plus editable multiplier value | Whether limits are validated elsewhere |
| Movement | Super movement speed; super jump; gravity handler | Hooks, user-editable values, and a thread/hotkey-style control | Physics stability, stack/register preservation, multiplayer behavior |
| Read-only stat tools | Get stats, float and integer stat fields | Pointer records populated by a scan/hook | Field layout and whether values are cached or persistent |
| Inventory/item tools | Item pointer, amount, change item, reroll, item level/upgrades, delete, hash display | Pointer records, hooks, Lua/table interface | Object ownership, serialization, and world-save effects |
| Time/glider | Temporary day-time edit; glider parameters | Hook plus pointer records | Persistence and validity across transitions |
| Teleport | Manual slots, dynamic slots, fixed destinations | Lua/table-interface logic and coordinate/state writes | Collision, map streaming, and save/world state |

The table also contains informational entries and a large fixed-location catalog. Those labels are not independent executable features.

## 2. Feature behavior matrix

| Feature | User-visible behavior | Class | Target category | Status |
|---|---|---|---|---|
| Full health | Restores or maintains the health value observed by a relevant calculation | Auto Assembler hook / code cave | Calculation or cached/player-state value | Behavior confirmed by working reference; semantics inferred |
| Full stamina | Prevents or repairs stamina loss at a relevant use/update site | Auto Assembler hook / code cave | Calculation or player-state value | Behavior confirmed by working reference; requires runtime evidence |
| Full mana | Prevents or repairs mana loss at a relevant use/update site | Auto Assembler hook / code cave | Calculation or player-state value | Behavior confirmed by working reference; requires runtime evidence |
| Easy parry | Alters the timing/qualification path for parry recognition | Auto Assembler hook | Calculation/branch | Behavior confirmed by working reference; semantics inferred |
| Free crafting / infinite consume | Suppresses or compensates an item-consumption operation | Auto Assembler hook | Inventory object/transaction | Behavior confirmed by working reference; unsafe to reimplement yet |
| Skill points | Raises available points to a floor and/or clears used points | Auto Assembler hooks | Player-state value | Behavior confirmed by working reference; save impact requires evidence |
| No fall damage | Bypasses or neutralizes fall-damage application | Auto Assembler hook | Calculation | Behavior confirmed by working reference; semantics inferred |
| No durability loss | Bypasses a durability decrement | Auto Assembler hook | Inventory object/player equipment | Behavior confirmed by working reference; transaction semantics require evidence |
| No shroud/oxygen/cold decrease | Suppresses depletion timers or decrements | Auto Assembler hooks | Calculation/cached value | Behavior confirmed by working reference; exact shared subsystem unknown |
| Stealth mode | Changes an enemy-detection/visibility decision when conditions are suitable | Auto Assembler hook | Calculation/player-state | Behavior confirmed by working reference; condition boundaries require runtime evidence |
| Rested bonus | Replaces a maximum bonus multiplier with a user value | Hook plus editable scalar | Calculation or cached value | Static implementation understood; semantics inferred |
| Super movement speed | Scales movement speed | Hook plus editable scalar | Calculation/player-state | Behavior confirmed by working reference; requires physics testing |
| Super jump | Scales jump force/vertical impulse | Hook plus editable scalar | Calculation/player-state | Behavior confirmed by working reference; requires physics testing |
| XP multiplier | Scales awarded experience | Hook plus editable scalar | Calculation | Behavior confirmed by working reference; persistent progression risk |
| Read character stats | Populates editable/displayed float and integer stat records after armor/equipment activity | Pointer records plus discovery hook | Cached/player-state value | Behavior confirmed by working reference; field semantics inferred |
| Item pointer/amount | Captures an inventory object and exposes amount | Pointer record | Inventory object | Behavior confirmed by working reference; stale-pointer risk |
| Change/reroll/delete item | Mutates item identity or item contents, rerolls gear, or removes an item | Hooks/table logic | Inventory object and persistent save data | Behavior confirmed by working reference; unsafe to reimplement yet |
| Item upgrade fields | Exposes item level, enhancement amount, and unlocked-upgrade fields | Pointer records | Inventory object | Static implementation understood; requires runtime evidence |
| Hash display | Prints or exposes an item identifier/hash | Table/Lua-interface logic | Metadata/display | Behavior confirmed by working reference; semantics inferred |
| Temporary day time | Writes a temporary time value | Hook plus pointer record | Cached/world/session value | Behavior confirmed by working reference; persistence unknown |
| Glider fields | Exposes/edit glider speed, lift, descent, and turn parameters | Pointer records | Player-state/configuration | Behavior confirmed by working reference; save/network behavior unknown |
| Teleport slots/destinations | Saves, loads, deletes, or writes player positions; includes named locations | Lua/table-interface logic and state writes | Player-state/world/session state | Behavior confirmed by working reference; high runtime risk |

## 3. Implementation-pattern catalog

### AOB hook pattern

The executable features use module-scoped signature scans rather than hard-coded absolute addresses. A matching instruction sequence is located, a nearby allocation is reserved, and execution is redirected to replacement logic. The replacement performs the feature-specific operation, reproduces the displaced instructions, then returns to the instruction after the overwritten region. Disable logic restores the original bytes, unregisters the scan symbol, and releases the allocation.

Confirmed structural facts: the XML contains module AOB scan directives, allocations, symbol registration/unregistration, explicit original-byte restoration, and jump-back flow. Exact scan patterns and identifiers are deliberately not reproduced here.

### Pointer-record pattern

Several entries are address records backed by symbols populated by a discovery hook or table script. The records expose typed fields at relative offsets, including item amount, item metadata, stat blocks, time, and glider parameters. A record is useful only while its captured object remains valid.

### Code-cave pattern

The allocated region is a small replacement body, not a general-purpose engine extension. It must preserve displaced instructions and all live registers/flags that the original continuation expects. Any user value is stored in a separate data cell or table-controlled record.

### Thread/hotkey pattern

The movement/gravity and teleport areas include table-side hotkey behavior and scripts that repeatedly or conditionally write state. Treat these as thread procedures or polling callbacks until runtime tracing proves otherwise. They are not equivalent to a one-time pointer edit.

### Lua/table-interface pattern

Lua is used for activation, UI text, hotkeys, dynamic slot management, value initialization, and helper actions. This layer can orchestrate a hook or pointer record but does not itself prove the underlying memory is stable.

## 4. Feature-by-feature reverse-engineering notes

For every hook, an independent implementation should rediscover: a unique current-build signature, instruction boundaries, the exact displaced instruction semantics, register/flag liveness, and the correct enable/disable restoration. The reference proves a working behavioral target, not portable offsets or safe semantics.

### Resources and survival

Health, stamina, and mana appear to intercept scalar reads/updates and force a favorable result. This is most consistent with a calculation or cached-value modification, not proof of a durable player-record write. Test damage, regeneration, resource spending, relogging, map transfer, and multiplayer authority separately.

Fall damage, durability, shroud, oxygen, and cold depletion likely intercept decrement or damage calculations. The labels support that interpretation; static inspection cannot establish whether all sources share one path or whether some effects bypass the hook.

Easy parry and stealth alter conditional game logic. They are especially sensitive to branch flags, timing, and context. Do not assume a binary branch replacement is safe merely because the table works in the reported build.

### Crafting, skills, rested bonus, and XP

Consumption suppression can affect both the visible count and the serialized inventory transaction. Skill-point edits may touch a player progression object rather than a display cache. Rested and XP multipliers are likely scalar substitutions in calculations, but their valid range and server-side acceptance are unknown.

### Movement and gravity

Speed and jump features use user-controlled scalar values. Gravity handling has separate hook/script structure and hotkey information. Physics code often depends on SIMD state, flags, and calling-convention assumptions; runtime tests must include landing, gliding, slopes, water, shroud, ragdoll, and disabling mid-motion.

### Stats

The stat editor has separate float and integer regions and a discovery action that requires equipment activity to populate fields. This strongly suggests a cached/derived stats structure or equipment-calculation result. It does not prove that editing a displayed stat changes the underlying equipment or persists to a save.

### Items

The item workflow captures an object pointer after moving an item, exposes amount and metadata, and provides mutation actions such as change, reroll, upgrade-field editing, deletion, and hash output. These are the highest-risk features because they may alter serialized item identity, ownership, stack invariants, or world/inventory indexes. Independent work should first use a disposable test world and nonessential items.

### Time, glider, and teleport

Time and glider records appear to expose direct fields or nearby values. Teleport uses stored positions and named destinations with manual, dynamic, and fixed-slot organization. Position writes can cross streaming cells, collision boundaries, or world-authoritative logic. Static inspection cannot distinguish a safe local player transform from a world-state mutation.

## 5. Safe candidates for independent reimplementation

The safest conceptual starting points are read-only observation tools: a fresh AOB that identifies a stat-population event, a pointer record that displays a value without writing it, and a disposable-session display of a captured item identifier. A bounded, reversible scalar hook such as a temporary calculation multiplier may follow after register/flag validation.

Concepts that can be reused: the separation between discovery hooks and pointer records, the enable/disable lifecycle, the need to replay displaced instructions, and the grouping of UI controls by mechanic.

Must be independently rediscovered: all signatures, addresses, symbols, allocation locations, instruction lengths, offsets, register roles, data types, return paths, valid ranges, and persistence/network semantics.

## 6. High-risk features requiring runtime evidence

Item mutation/deletion/reroll, inventory consumption suppression, skill-point writes, teleportation, gravity manipulation, stealth, and any feature that appears to alter progression or serialized state should not be reimplemented from static evidence alone. Risks include stale pointers, object replacement after inventory movement, invalid flags, stack/register corruption, misaligned stack use in injected calls, and incomplete cleanup after disable.

## 7. Recommended build order

1. Establish a disposable test world and a versioned process/build fingerprint.
2. Build read-only observation for one scalar and one pointer record.
3. Add a reversible calculation hook with strict signature uniqueness and byte restoration checks.
4. Validate resource and movement features one at a time.
5. Add progression calculations only after save/reload and multiplayer tests.
6. Investigate item pointers without mutation; then test amount-only edits on disposable items.
7. Leave deletion, reroll, crafting suppression, and teleport for last, with backups and rollback checks.

## 8. Test procedure for each feature

For every feature: record the baseline, activate one feature only, exercise the smallest relevant action, observe both UI and gameplay, disable it, verify the original bytes, and restart the process. Repeat after map transition, save/reload, and reconnect where applicable. Capture whether the effect is a displayed value, cached value, player-state value, calculation, inventory object, or persistent world/save data.

Safety checks must include pointer validity before every dereference, unique scan count, instruction-boundary verification, register and flag comparison, stack alignment for any call, and confirmation that disable removes allocations and symbols. Never treat a successful enable as proof of functional correctness or safety.

## 9. Attribution and originality guidance

Use the reference only as a behavioral oracle and document that relationship. Reimplement from independently observed current-build behavior and fresh signatures. Do not transplant code, comments, labels, symbols, offsets, table hierarchy, AOB strings, or implementation blocks. Keep an audit log of your own observations, hypotheses, tests, and failure cases.

## 10. Unresolved questions

- Which effects are client-local versus server-authoritative?
- Which scalar fields are cached displays versus canonical player state?
- Do item edits update all inventory indexes and serialization metadata?
- What exact lifecycle invalidates each captured pointer?
- Are teleport coordinates safe across streamed cells and collision volumes?
- What save-file changes occur after progression, item, time, or stat edits?
- Do hooks preserve all flags and vector/register state on every branch?
- Does disabling during an active hook/thread fully stop callbacks before deallocation?
