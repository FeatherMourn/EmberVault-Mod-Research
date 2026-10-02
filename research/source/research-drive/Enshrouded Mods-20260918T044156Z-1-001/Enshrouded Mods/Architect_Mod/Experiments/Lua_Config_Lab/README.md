# Architect Lua Config Lab

A standalone Windows tool for editing Enshrouded resource configuration through
EML/Lua **before Enshrouded starts**.

This is a **startup configuration tool only**. It does not perform live process
memory modification, AOB scanning, DLL injection, runtime hooks, or hot reload.

All changes take effect when Enshrouded starts up. Restart the game after changing
a generated configuration.

---

## 2-Level Interface: Friendly Catalog & Advanced Editor

Phase 2 introduces a full 2-level interface designed for normal users and modders alike:

1. **Simple Catalog View (Default)**:
   - **Home Screen**: Browse resources organized cleanly into **16 functional categories** (Player & Game Balance, Combat, Shrouded Areas, Building, World & Time, etc.) or search dynamically.
   - **Category View**: Visual resource cards explaining what each resource does in plain English.
   - **Resource View**: Curated, friendly input controls with safety limits, restart reminders, and collapsible technical details.
   - **All Resources (131/131)**: Searchable alphabetical directory of every single known Enshrouded resource root.
   - **My Changes**: Central review screen for all pending edits before saving presets or building mods.

2. **Advanced Resource Editor**:
   - Preserves the full 3-panel workspace (`Resource Browser` | `Field Tree` | `Edit Panel`).
   - Accessible anytime via the top navigation bar or by clicking **"Browse Raw Fields"** on any resource card.
   - Directly exposes all 4,854 reflected classes and 21,442 fields.

---

## Directory layout

```
Lua_Config_Lab/
    run.py                         convenience launcher
    README.md
    docs/
        RESOURCE_CATALOG.md        resource taxonomy and schema guide
        CONTROL_CATALOG.md         friendly controls mapping guide
        PROFILE_FORMAT.md          profile / preset format specification
        LUA_GENERATOR.md           Lua generator details
        KNOWN_LIMITATIONS.md       documented engine limitations
    tests/                         automated test suite (105 tests)
    output/                        generated EML mods land here
        baseline_stamina_test/     pre-generated sample mod
    architect_lua_config_lab/
        app.py                     CLI entry + GUI launcher
        config.py                  source-file / directory discovery
        core/                      headless, testable library
            schema_model.py        reflected class and type definitions
            type_parser.py         parser for types.lua
            schema_parser.py       database builder
            kfc_roots.py           131 KFC root loader
            resource_catalog.py    catalog data loader and taxonomy validator
            control_catalog.py     friendly controls loader and translator
            display.py             status labels and vocabulary
            validation.py          input and schema validators
            field_paths.py         nested path resolution
            profile.py             preset profile serialization
            lua_generator.py       EML Lua code generator
            eml_template.py        mod package exporter
            lab.py                 main headless controller
        ui/                        tkinter GUI
            main_window.py         root container, banner, and navigation stack
            home_view.py           category grid, search, and quick links
            category_view.py       resource cards for a selected category
            resource_view.py       friendly controls + raw fields launcher
            search_view.py         global metadata and tag search
            all_resources_view.py  complete 131/131 root browser
            my_changes_view.py     pending edits review and preset builder
            advanced_workspace.py  3-panel raw reflection editor
        data/
            resource_catalog.json  catalog of all 131 resource roots
            control_catalog.json   curated friendly control definitions
            known_resource_roots.json
            examples/              example presets
```

---

## Requirements

* Windows
* Python 3.11+ (standard library only — no external dependencies)

`tkinter` + `ttk` are used for the GUI (included with standard Python on Windows).

---

## Quick start

### Launch the GUI

```powershell
cd "H:\...\Architect_Mod\Experiments\Lua_Config_Lab"
python run.py
```

### Run the automated tests

```powershell
python -m unittest discover -s tests -t .
```

### CLI (headless)

```powershell
python run.py parse                                  # load schema, print regression counts
python run.py search Balancing                       # search resource roots
python run.py generate data\examples\baseline_stamina.json   # print generated Lua
python run.py export   data\examples\baseline_stamina.json   # export an EML mod
```

---

## Generated EML Mod Structure

```
<ModDir>/
    mod.json                 { id, name, version, capabilities: ["patch","export"], description }
    src/
        mod.lua              the generated startup patch code
    profile.json             the exact profile that produced this mod
    generated_manifest.json  provenance and build metadata
```

---

## Status and Evidence Model

Every control and edit displays an explicit verification state:

* `PROVEN_STARTUP_EFFECT` (`? Tested`): Verified in-game to apply on startup.
* `SCHEMA_AVAILABLE` (`? Schema Available`): Validated against the Lua reflection type database.
* `EXPERIMENTAL` (`?? Experimental`): Under active testing; valid schema, runtime effects unproven.
* `KNOWN_NOT_WORKING` (`? Known Not Working`): Overridden at runtime or ignored by the engine.
* `UNSUPPORTED` (`? Unsupported`): Not mutable via startup Lua scripts.

Promote a control to `PROVEN_STARTUP_EFFECT` only after observing in-game behavior.

---

## Safety Rules

* The tool **never** modifies `types.lua`, `base.lua`, KFC archives, or the canonical game files.
* Generated mods go to a dedicated output directory; existing directories are versioned (`name_v2`, `name_v3`, ...) unless explicitly overwritten.
* `ALL` target mode requires confirmation before export.
