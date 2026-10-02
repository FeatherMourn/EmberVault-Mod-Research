# Independent feature status matrix

Current executable build: `AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781`.

All rows currently have status **Not implemented**. A row may only advance after its target instruction/data structure, original bytes/value, exactly-one AOB result, instruction-boundary/return-flow review, register/flag/stack review, complete disable proof, risk notes, and offline test procedure are attached.

| Phase | Feature | Intended behavior | Risk class | Status |
|---|---|---|---|---|
| 2 | Health | Prevent or configure health loss | gameplay | Not implemented |
| 2 | Stamina | Prevent or configure stamina loss | gameplay | Not implemented |
| 2 | Mana | Prevent or configure mana loss | gameplay | Not implemented |
| 2 | No fall damage | Suppress fall-damage application | gameplay | Not implemented |
| 2 | Shroud timer | Configure or pause shroud timer | gameplay | Not implemented |
| 2 | Oxygen/breath | Prevent or configure breath depletion | gameplay | Not implemented |
| 2 | Body heat | Configure body-heat change | gameplay | Not implemented |
| 2 | XP multiplier | Apply configurable XP factor | progression/save | Not implemented |
| 2 | Durability loss | Suppress or scale durability loss | gameplay/save | Not implemented |
| 2 | Ammunition consumption | Suppress or scale ammunition use | inventory/save | Not implemented |
| 2 | Movement speed | Apply configurable movement factor | gameplay/multiplayer | Not implemented |
| 2 | Jump height | Apply configurable jump factor | gameplay/multiplayer | Not implemented |
| 2 | Glider parameters | Configure glider behavior | gameplay/multiplayer | Not implemented |
| 2 | Time of day | Read/write world time safely | world/save | Not implemented |
| 3 | Free crafting | Bypass recipe material checks | save/inventory | Not implemented |
| 3 | Material-consumption multiplier | Scale consumed materials | save/inventory | Not implemented |
| 3 | Stack size | Configure stack capacity | save/inventory | Not implemented |
| 3 | Skill points | Configure awarded skill points | save/progression | Not implemented |
| 3 | Used skill-point override | Alter spent-point accounting | save/progression | Not implemented |
| 3 | Upgrade-limit controls | Configure upgrade limits | save/progression | Not implemented |
| 4 | Coordinate display | Read and display player coordinates | read-only first | Not implemented |
| 4 | Save/load position slots | Store and restore positions | world/save | Not implemented |
| 4 | Fixed-location teleportation | Teleport to one validated destination | world/save/multiplayer | Not implemented |
| 4 | Map discovery | Alter map discovery state | save/world | Not implemented |
| 4 | Building reach | Configure placement reach | world/multiplayer | Not implemented |
| 4 | Building restrictions | Alter placement restrictions | world/multiplayer | Not implemented |
| 4 | Structural support | Alter support checks | world/save | Not implemented |
| 4 | Prop placement | Alter prop placement checks | world/save/multiplayer | Not implemented |
| 5 | Free flight | Detach normal flight constraints | experimental | Not implemented |
| 5 | No-clip | Bypass collision | experimental/multiplayer | Not implemented |
| 5 | Item editing | Alter item fields | experimental/save | Not implemented |
| 5 | Item deletion | Remove selected items | experimental/save | Not implemented |
| 5 | Item rerolling | Regenerate item properties | experimental/save | Not implemented |
| 5 | Inventory quantity manipulation | Alter stored quantities | experimental/save | Not implemented |
| 5 | Terrain destruction | Bypass terrain destruction checks | experimental/world/save | Not implemented |
| 5 | Voxel reskinning | Alter voxel visual/material data | experimental/world | Not implemented |
| 5 | Automated building | Place structures programmatically | experimental/world/save | Not implemented |

## Promotion rules

- **Static-analysis complete** requires disassembly evidence and a reviewed target; assembly success alone is insufficient.
- **Ready for live testing** requires static-analysis completion, exact-one AOB verification on the recorded executable, and a complete disable path.
- **Live-tested** may only be assigned after the user performs the documented offline disposable-save test.
- **Failed** records the reproducible failure and leaves the feature disabled.
- **Unsafe** records why the feature cannot be responsibly enabled.
- Experimental, progression, inventory, and world-mutating rows remain disabled by default regardless of status until separately approved for testing.
