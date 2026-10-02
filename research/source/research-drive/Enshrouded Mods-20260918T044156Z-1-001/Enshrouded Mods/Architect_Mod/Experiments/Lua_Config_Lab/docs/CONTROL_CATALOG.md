# Lua Config Lab — Friendly Control Catalog

## Overview

The Friendly Control Catalog (`architect_lua_config_lab/data/control_catalog.json`) defines high-level, human-friendly configuration widgets that map directly to underlying engine fields and resources.

Rather than manually hunting for complex nested paths in the raw field tree (e.g. `sunSetup.zenithAngle` on `keen::IngameTimeConfig`), users can interact with curated, labelled controls with preset input bounds, descriptions, and restart notices.

---

## Architectural Guarantee: 1:1 Mapping to the Edit Backend

Friendly controls **do not** introduce an alternate backend or divergent code generation pipeline.

Instead:
1. Every control defines a `backend` block specifying `resource_type`, `target`, and `path`.
2. When the user sets a value in a friendly control, `Lab.make_control_edit(control, value)` is invoked.
3. This translates the control directly into an identical, fully validated `ProfileEdit` object via `Lab.make_edit(...)`.
4. The generated edit is serialized into the same profile format, previews identical Lua code, and exports through the standard EML builder.
5. Edits made through friendly controls appear in **My Changes** and can also be viewed, toggled, reordered, or edited directly in the **Advanced Resource Editor**.

```
[ Friendly Control Input ]
         ¦
         ?
[ control_to_edit(...) ] --> [ Schema / Type Validation ]
                                      ¦
                                      ?
                            [ ProfileEdit Object ]
                                      ¦
         +----------------------------+---------------------------+
         ?                            ?                           ?
[ My Changes View ]          [ Profile JSON Save ]       [ Lua Code Generator ]
```

---

## Evidence and Testing Status Vocabulary

Every friendly control carries a `status` reflecting empirical in-game validation:

* **`PROVEN_STARTUP_EFFECT`** (`? Tested`): Verified in-game to apply and alter gameplay when Enshrouded starts.
* **`SCHEMA_AVAILABLE`** (`? Schema Available`): Validated against the Lua reflection type database; field exists and accepts edits, but gameplay impact has not yet been verified.
* **`EXPERIMENTAL`** (`?? Experimental`): Under active testing; field is exposed and validated by the schema, but unexpected side effects or runtime overrides are possible.
* **`KNOWN_NOT_WORKING`** (`? Known Not Working`): Documented field where startup mutations have no observed effect in-game (e.g. overridden at runtime by save data or server sync).
* **`UNSUPPORTED`** (`? Unsupported`): Field type or complex pointer structure cannot currently be mutated via startup Lua scripts.

---

## Seeded Controls in Phase 2

Phase 2 seeds demonstration controls across multiple core resource types:

| Control ID | Name | Category | Resource Type | Target Field | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `balance.player_base_health` | Base Health | Player & Game Balance | `keen::BalancingTable` | `playerBaseHealth` | Experimental |
| `balance.player_base_stamina` | Base Stamina | Player & Game Balance | `keen::BalancingTable` | `playerBaseStamina` | Experimental |
| `balance.player_base_mana` | Base Mana | Player & Game Balance | `keen::BalancingTable` | `playerBaseMana` | Experimental |
| `balance.player_level_max` | Max Player Level | Player & Game Balance | `keen::BalancingTable` | `playerLevelMax` | Experimental |
| `settings.min_player_health_factor` | Min Player Health Factor | Player & Game Balance | `keen::GameSettingsPresetsResource` | `minValues.playerHealthFactor` | Experimental |
| `settings.min_player_stamina_factor` | Min Player Stamina Factor | Player & Game Balance | `keen::GameSettingsPresetsResource` | `minValues.playerStaminaFactor` | Experimental |
| `time.sun_zenith_angle` | Sun Zenith Angle | World, Time & Survival | `keen::IngameTimeConfig` | `sunSetup.zenithAngle` | Experimental |
| `time.sun_rise_angle` | Sun Rise Angle | World, Time & Survival | `keen::IngameTimeConfig` | `sunSetup.riseAngle` | Experimental |
| `slope.sliding_angle` | Sliding Angle | Terrain, Water & Materials | `keen::SlopeDefinition` | `slidingAngle` | Experimental |

---

## Schema for Control Catalog Entries

```json
{
  "id": "balance.player_base_health",
  "name": "Base Health",
  "category": "Player & Game Balance",
  "description": "Sets the player's base health value used by the game's balance resource.",
  "ui_type": "number",
  "status": "EXPERIMENTAL",
  "backend": {
    "resource_type": "keen::BalancingTable",
    "target": { "mode": "first" },
    "path": "playerBaseHealth"
  }
}
```

### Fields

* **`id`** *(string, required)*: Unique identifier for the control (e.g. `domain.setting_name`).
* **`name`** *(string, required)*: Human-readable display label.
* **`category`** *(string, required)*: Category matching the resource taxonomy.
* **`description`** *(string, required)*: Clear explanation of what adjusting this value does.
* **`ui_type`** *(string, required)*: Supported input widget type (`number`, `bool`, `enum`, `string`, `guid`).
* **`status`** *(enum)*: One of the evidence statuses (`EXPERIMENTAL`, `PROVEN_STARTUP_EFFECT`, etc.).
* **`backend`** *(object, required)*:
  * `resource_type`: Canonical KFC root type name.
  * `target`: Mode and optional selector (default `{"mode": "first"}`).
  * `path`: Dot-separated field path (e.g. `sunSetup.zenithAngle`).

---

## Adding a New Friendly Control

1. Identify the resource type and field using the **Advanced Resource Editor** (`Browse Raw Fields`).
2. Verify that the field resolves and is editable.
3. Open `architect_lua_config_lab/data/control_catalog.json` and append the new control definition.
4. Run tests to verify the schema parser accepts it:
   ```bash
   python -m unittest discover -s tests -t .
   ```
