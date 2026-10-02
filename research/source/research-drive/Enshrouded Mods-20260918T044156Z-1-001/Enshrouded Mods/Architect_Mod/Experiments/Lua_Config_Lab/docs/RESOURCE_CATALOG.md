# Lua Config Lab — Resource Catalog

## Overview

The Resource Catalog (`architect_lua_config_lab/data/resource_catalog.json`) provides a human-navigable taxonomy over the **131 known Enshrouded KFC resource roots** discovered via Lua reflection.

Rather than forcing users to sift through technical C++ / KFC type names (e.g. `keen::SlidingSlopeDefinition` vs `keen::SlopeDefinition`), the catalog organizes all resources into **16 functional categories** with clear, plain-English names, descriptions, and searchable tags.

The catalog acts as an information-architecture layer over the raw engine, preserving full access to every underlying field and class while making the system intuitive for non-technical users.

---

## The 16 Approved Categories

Every one of the 131 resource roots belongs to exactly one primary category from the approved taxonomy:

1. **Player & Game Balance** — Core stats, progression, character leveling, scaling curves, game balance tables.
2. **Combat, Damage & Equipment** — Weapon handling, damage types, armor stats, combat timings, equipment slots.
3. **World, Time & Survival** — Time of day, day/night cycles, sun zenith, weather, basic survival parameters.
4. **Shrouded Areas & Hazards** — Deadly fog / shroud mechanics, hazards, contamination timers.
5. **Terrain, Water & Materials** — Voxel terrain properties, slope sliding angles, water simulations, physics materials.
6. **Building, Snapping & Voxels** — Construction grids, snapping tolerances, structural integrity, block placing rules.
7. **Farming, Flora & Vegetation** — Plant growth rates, crops, flora density, harvest yields.
8. **Creatures, Spawning & AI** — Monster populations, AI archetypes, aggro ranges, spawn rates.
9. **Loot, Drops & Economy** — Chest drop tables, item drop chances, vendor pricing, economic parameters.
10. **Camera, Controls & Input** — Field of view, sensitivity curves, gamepad deadzones, camera orbit dynamics.
11. **UI, Audio & Presentation** — Sound banks, HUD indicators, notifications, user interface configuration.
12. **Rendering, Shaders & Atmosphere** — Lighting setup, atmospheric scattering, post-processing, shader definitions.
13. **VFX, Particles & Lighting** — Visual effects, emitters, particle systems, light intensities.
14. **Animation, Movement & Physics** — Player movement speeds, jump physics, collision bounding, ragdolls.
15. **Networking, System & Streaming** — World streaming chunks, network sync intervals, replication settings.
16. **Tools, Debug & Experimental** — Developer flags, diagnostic hooks, debug renderers.

---

## Schema for Resource Catalog Entries

Each entry in `resource_catalog.json` adheres to the following structure:

```json
{
  "resource_type": "keen::BalancingTable",
  "friendly_name": "Player & Game Balancing",
  "primary_category": "Player & Game Balance",
  "family": "BalancingTable",
  "description": "Core gameplay balance multipliers including player health, stamina, mana, and level limits.",
  "tags": ["balance", "health", "stamina", "mana", "level", "player"],
  "access_level": "STANDARD",
  "friendly_controls_available": true
}
```

### Fields

* **`resource_type`** *(string, required)*: The canonical C++ KFC root type identifier matching the schema (e.g. `keen::BalancingTable`).
* **`friendly_name`** *(string, required)*: Plain-English title for display in cards, lists, and headings.
* **`primary_category`** *(string, required)*: One of the 16 approved categories.
* **`family`** *(string, required)*: The underlying KFC family name (matches the raw resource root family).
* **`description`** *(string, required)*: Explanation of what this resource governs and how modifying it affects the game.
* **`tags`** *(array of strings)*: Search keywords for fast discovery across synonyms and game concepts.
* **`access_level`** *(enum: `STANDARD` | `ADVANCED`)*: Standard entries are commonly tweaked; advanced entries represent specialized or lower-level engine constructs.
* **`friendly_controls_available`** *(boolean)*: Automatically flagged if curated friendly controls exist for this resource.

---

## Validation and Integrity

The catalog is strictly validated on load by `ResourceCatalog.validate(roots, db)` in `core/resource_catalog.py`:
- **Completeness**: All 131 known roots must have a catalog entry (131/131 coverage).
- **Exactness**: No orphan or phantom entries that do not exist in the root list.
- **Taxonomy Enforcement**: Every entry must reference an approved category.
- **Fail-Closed**: If the catalog is out of sync with `types.lua` or `roots`, the system halts with a descriptive error rather than generating corrupt mods.

---

## Adding or Editing Catalog Entries

1. Open `architect_lua_config_lab/data/resource_catalog.json`.
2. Locate or add the entry matching the `resource_type`.
3. Ensure the `primary_category` matches one of the 16 categories in `CATEGORIES`.
4. Run the automated test suite to ensure schema validation passes:
   ```bash
   python -m unittest discover -s tests -t .
   ```
