# Enshrouded Mod Hub & Control Center - Complete User & Technical Manual

Welcome to the **Enshrouded Mod Hub & Visual Builder**! This guide details **every category, slider, toggle, tool, hotkey, and next-gen feature** built into the application, explaining what each feature does in the game, how it works under the hood, and best practices for using it.

---

## Table of Contents
1. [Quick-Start Overview & Workflow](#1-quick-start-overview--workflow)
2. [🧙 Character Sheet (Vitals, Resistances & Progression)](#2--character-sheet-vitals-resistances--progression)
3. [🔨 Building & Terraforming Tools (Hopper & Chisel Bits)](#3--building--terraforming-tools-hopper--chisel-bits)
4. [📐 Shape & Blueprint Studio (3D Orbit & Multi-Material)](#4--shape--blueprint-studio-3d-orbit--multi-material)
5. [🎮 In-Game Runtime Hotkeys, Undo/Redo & Area Scanner](#5--in-game-runtime-hotkeys-undoredo--area-scanner)
6. [⚡ In-Game Floating Mini-Dashboard & Ghost Wireframe Guide](#6--in-game-floating-mini-dashboard--ghost-wireframe-guide)
7. [⚔️ Combat, Elemental Spells & Boss Balancing](#7-️-combat-elemental-spells--boss-balancing)
8. [🦅 Glider & Flight Aerodynamics](#8--glider--flight-aerodynamics)
9. [💰 Loot, Chests & Blacksmith Economy](#9--loot-chests--blacksmith-economy)
10. [🌍 World, Farming, Kilns & Dynamic Weather](#10--world-farming-kilns--dynamic-weather)
11. [🛡️ Intelligent Pre-Launch Crash Diagnostic Shield](#11-️-intelligent-pre-launch-crash-diagnostic-shield)
12. [⚡ Live Memory Cheats & Teleportation](#12--live-memory-cheats--teleportation)
13. [📜 Generated Lua & 📋 Game Logs](#13--generated-lua--game-logs)
14. [Troubleshooting & FAQ](#14-troubleshooting--faq)

---

## 1. Quick-Start Overview & Workflow

For first-time content creation, use the separate
[Beginner Content Wizard Guide](BEGINNER_CONTENT_WIZARD_GUIDE.md). Content
Studio's **Open Content Wizard** is the recommended path; the advanced donor
and resource tools are optional and hidden until explicitly opened.

### How the Mod Builder Works
1. **Zero Coding Required**: Adjust visual sliders and flip toggles in the application.
2. **Instant Profile Sync**: Changes automatically save to your local profile (`visual_builder_profile.json`).
3. **Live Hot-Swapping (Option 9)**: Update settings in the GUI while Enshrouded is running; settings dynamically sync in-game without needing to restart!
4. **Pre-Launch Diagnostic Shield (Option 15)**: Automatically validates all Lua queries against `types.json` before touching your game files to ensure zero crashes.
5. **One-Click Deploy & Launch**:
   - Clicking **`▶ DEPLOY & LAUNCH`** copies the generated script into Enshrouded's Enshrouded Mod Loader (`EML`) directory and starts the game via Steam.

---

## 2. 🧙 Character Sheet (Vitals, Resistances & Progression)

Mimics an RPG character sheet to customize your Flameborn's core attributes.

### Primary Vitals & Constitution
- **Max Health Multiplier (`1.0x` – `10.0x`)**: Multiplies your base health pool.
- **Max Mana Multiplier (`1.0x` – `10.0x`)**: Scales total magical energy for staves, wands, and spells.
- **Max Stamina Multiplier (`1.0x` – `10.0x`)**: Expands stamina for sprinting, jumping, climbing, and heavy attacks.
- **Enable True Infinite Stamina**: Bypasses the stamina depletion check entirely in game memory/presets so stamina never drops.
- **Infinite Weapon & Tool Durability**: Prevents pickaxes, axes, weapons, and armor from wearing out or breaking.

### Environmental Resilience & Survival
- **Body Heat / Freezing Resistance (`1.0x` – `10.0x`)**: Multiplies your resistance against freezing temperatures in alpine peaks.
- **Underwater Diving Breath Time (`1.0x` – `10.0x`)**: Extends your lung capacity before drowning when swimming underwater.
- **Hunger-to-Starvation Delay (`1.0x` – `10.0x`)**: Extends the grace period between hunger and starvation damage.
- **Base Rested Buff Duration (`1.0x` – `5.0x`)**: Multiplies how long your home comfort rested bonus lasts in the wild.
- **Shroud Survival Timer Multiplier (`1.0x` – `20.0x`)**: Extends your base survival timer inside the deadly Shroud fog.

### Leveling & Mountain Mobility
- **Player & Gear Level Cap (`25` – `100`, Vanilla: 45)**: Raises the level cap for late-game progression.
- **Skill Points Awarded Per Level (`2` – `25`, Vanilla: 5)**: Gives extra skill points every time you level up.
- **Mountain Slope Climbing Angle (`45°` – `89°`, Vanilla: ~50°)**: Allows sprinting up sheer cliffs without sliding.

---

## 3. 🔨 Building & Terraforming Tools (Hopper & Chisel Bits)

### Flame Altars & Base Bounds
- **Flame Altar Protection Radius (`1.0x` – `5.0x`)**: Expands base build boundaries per flame altar tier.
- **Max Flame Altars Limit (`2` – `100`)**: Increases total simultaneous flame altars allowed in your world.

### Storage & Base Automation (Option 12)
- **Universal Magic Storage**: Converts all normal wooden and iron chests into Magic Storage across your base.
- **Smart Base Automation Hopper Loop (Option 12)**: Background tick loop that scans production stations (kilns, smelters, seedbeds) and auto-routes outputs to maintain continuous flow.

### Precision Masonry & Microvoxels (Option 6 & Option B)
- **Unlock Native 1x1x1 Microvoxel Blueprints**: Exposes native 1x1x1 and 2x2x2 voxel pieces in your building tools for micro-sculpting.
- **Chisel Carving Damage Scale (`0.1x` – `1.0x`)**: Precise micro-voxel removal without breaking entire walls.
- **Vintage Story Decorative Presets**: Pre-calculated stamps for *Beveled 45° Corner Trim* and *Roman Arch Headers*.

---

## 4. 📐 Shape & Blueprint Studio (3D Orbit & Multi-Material)

### 3D Interactive Orbit Viewport (Option 1)
- **3D Isometric Engine**: Real-time projection on Canvas.
- **Mouse Drag to Rotate**: Hold Left Mouse Button to rotate Yaw and Pitch angles.
- **Mouse Wheel to Zoom**: Smoothly zoom in and out.
- **Segmented View Toggle**: Switch instantly between `3D Orbit` and `2D Top-Down` projection.

### Multi-Material Gradient Theming (Option 2)
- Automatically splits structural layers by height:
  - **Foundation (`Bottom 25%`)**: Stone / Masonry blocks.
  - **Walls (`Middle 50%`)**: Treated Timber / Wood panels.
  - **Roof (`Top 25%`)**: Weathered Slate / Shingles.

---

## 5. 🎮 In-Game Runtime Hotkeys, Undo/Redo & Area Scanner

All hotkeys run in a high-efficiency background dispatcher and can be **fully customized and reprogrammed** in either the Studio tab or directly inside the Floating Mini-HUD:

| Default Hotkey | Action | Feature | Description |
| :---: | :---: | :---: | :--- |
| **`[Insert]`** | **Toggle Mini-HUD** | Option 14 Overlay | Opens or hides the floating in-game mini-dashboard on demand. |
| **`[F]`** | **Anchor Point 1** | Runtime Overlay | Sets Anchor coordinate at your crosshair / player location. |
| **`[G]`** | **Commit Zoop / Shape**| Runtime Overlay | Generates active procedural shape and writes live `active_zoop.json`. |
| **`[H]`** | **Cycle Tool Mode** | Runtime Overlay | Cycles `Line Zoop` ➔ `Circle Ring` ➔ `Cylinder` ➔ `Dome` ➔ `Stairs` ➔ `Box`. |
| **`[Ctrl+Z]`** | **Undo Placement** | Option 5 Buffer | Rolls back the last placement batch piece by piece. |
| **`[Ctrl+Y]`** | **Redo Placement** | Option 5 Buffer | Re-applies the most recently undone batch. |
| **`[Shift+F]`** | **Area Scan Corner 1** | Option 7 Scanner | Sets Corner 1 for microvoxel volume capture. |
| **`[Shift+G]`** | **Area Scan & Export** | Option 7 Scanner | Captures Corner 2 and exports complete bounding volume to JSON blueprint. |

> [!TIP]
> **Reprogramming Keys**: Don't have an `[Insert]` key or prefer different binds? Click **"⚙️ Rebind Keys"** in the Studio tab or **"Rebind"** on the Mini-HUD to remap any action to your preferred keys (e.g. `[F8]`, `[Tilde]`, `[Tab]`, `[End]`, etc.).

---

## 6. ⚡ In-Game Floating Mini-Dashboard & Ghost Wireframe Guide

### Floating Mini-Dashboard (Option 14)
- **Topmost & Draggable**: Floats directly over Enshrouded while in Borderless Windowed mode.
- **Quick Controls**: Instant toggles for Infinite Stamina, Durability, Hammer Reach slider, and Glider Boost slider.
- **Time & Weather Controller (Option 13)**: Live 0–24 hour time scrubber and weather state triggers (Clear, Rain, Snow).

### Ghost Wireframe Placement Guide (Option 4)
- Displays active tool mode, anchor coordinates, cursor distance, and bounding box dimensions in real-time on the overlay before committing.

---

## 7. ⚔️ Combat, Elemental Spells & Boss Balancing

### Per-Spell Customizer & Elemental Tuning (Option 11)
- **Fire Spells Multiplier**: Boosts *Eternal Fireball* and *Flame Arrows*.
- **Ice Spells Multiplier**: Boosts *Ice Bolt* and *Frost Nova*.
- **Shock Spells Multiplier**: Boosts *Chain Lightning* and *Shock Waves*.
- **Shroud Spells Multiplier**: Boosts *Shroud Meteor* and *Acid Bite*.
- **Fast Casting (`0.1x` – `1.0x`)**: Cast spells up to 10x faster.
- **Mana Cost Scaling (`0%` – `100%`)**: Set to 0% for free spellcasting.

---

## 8. 🦅 Glider & Flight Aerodynamics

- **Forward Acceleration Propulsion (`1.0x` – `6.0x`)**: Rocket forward when deploying your glider.
- **Infinite Hover / Vertical Descent (`1.0x` – `5.0x`)**: Reduces vertical fall drag to glide across the entire world map.
- **Updraft Launch Power (`1.0x` – `5.0x`)**: Launches you high into the sky on steam vents.

---

## 9. 💰 Loot, Chests & Blacksmith Economy

- **Dungeon Chest Loot Multiplier (`1.0x` – `10.0x`)**: Multiplies items inside chests and boss sarcophagi.
- **Resource Harvest Drop Multiplier (`1x` – `10x`)**: Multiplies gathered mushrooms, resin, fibers, and ores.
- **Item Stack Multiplier (`1x` – `100x`)**: Expands inventory stack limits up to 100x vanilla size.

---

## 10. 🌍 World, Farming, Kilns & Dynamic Weather

- **Dynamic Day/Night & Weather (Option 13)**: Independently configure daytime/nighttime minutes and set world sun dial.
- **Crop Growth Speed (`1.0x` – `50.0x`)**: Speeds up seedling growth for instant harvests.
- **Smelting & Kiln Speed (`1.0x` – `100.0x`)**: Instant charcoal, bars, and refined goods.
- **Fog of War Reveal Radius (`1.0x` – `10.0x`)**: Clear world map fog rapidly.

---

## 11. 🛡️ Intelligent Pre-Launch Crash Diagnostic Shield (Option 15)

- Automatically validates all Lua queries against `H:\SteamLibrary\steamapps\common\Enshrouded\.cache\types.json`.
- Flags missing types, duplicate hooks, or malformed queries before deployment.
- Prevents game crashes before they can happen!

---

## 12. ⚡ Live Memory Cheats & Teleportation

Real-time AOB memory engine operating directly on `enshrouded.exe`:
- **God Mode**, **Infinite Mana**, **Infinite Stamina**, **Free Crafting Bypass**, and **Freeze Shroud Timer**.
- Verified 3D world coordinates for instant Ancient Spire and Vault navigation.

---

## 13. 📜 Generated Lua & 📋 Game Logs

- **Generated Lua Tab**: Real-time preview of the clean Lua code generated by your visual selections.

## Inspecting Blender exports

Open **Content Studio** and choose **Inspect Blender Export** to validate an
EnshroudedBlenderTools-generated folder before staging it. Control Center checks
the module metadata, target RenderModel identity, generated mesh and texture
integrity, and optional icon metadata. Inspection is read-only: a valid export
is still research-only and is not installed until you deliberately use the
separate staging workflow.
- **Game Logs Tab**: Direct log streaming from `logs/*.eml.log` with a single-click refresh button.

---

## 14. Troubleshooting & FAQ

### Save protection and recovery

From Control Center Settings, use **Back Up Save Folder** before testing
research modules or tuning changes. Use **Compare Save Backups** to review
added, removed, and changed files, and **Restore Save Backup** to restore a
verified snapshot into a separate folder. These actions are blocked while
Enshrouded is running and never overwrite the live save folder.

**Inspect Save Progress (Read-only)** can inventory the active character save
and its supported KSC1 blob types. It does not edit saves and does not claim
world-save or quest-state editing support.

If the save folder is unknown, run the read-only discovery action first. It
checks standard Windows locations and reports which one contains
`characters-index`; it does not create or modify any save data.

For a beginner-friendly route, use **Save Safety → Back Up My Saves**. Control
Center finds the standard save folder, requires Enshrouded to be closed, and
creates a verified snapshot under `Control_Center/profiles/save-backups`. You
can give the snapshot a memorable name such as `before-new-bed-test`.

Use **Restore a Copy Safely** to inspect an older snapshot. Select the snapshot
and a separate destination folder; the live Enshrouded saves are never
overwritten.

#### Q: How do I open the In-Game Floating Mini-HUD?
- Click the **`⚡ Launch Mini-HUD`** button in the sidebar or click **`⚡ Mini-HUD`** on the bottom-right status bar.

#### Q: Do I need to restart the game when I change settings?
- No! Thanks to the **Live Hot-Swapping Bridge (Option 9)**, adjusting settings automatically writes to `runtime_sync.json` and updates the active game session.

#### Q: How do I undo an accidental block placement?
- Simply press **`[Ctrl+Z]`** while the game is focused. To re-apply it, press **`[Ctrl+Y]`**.

#### Q: How do I scan an existing building and save it as a blueprint?
- Aim at Corner 1 and press **`[Shift+F]`**. Move to Corner 2 and press **`[Shift+G]`**. The complete voxel blueprint is saved directly to your `blueprints/` directory!
