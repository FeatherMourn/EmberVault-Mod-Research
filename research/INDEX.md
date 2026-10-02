# Research index

This is the entry point for the Enshrouded mod-development knowledge base.

## How to read this repository

1. Start with [`FINDINGS.md`](FINDINGS.md) for conclusions and their evidence status.
2. Follow the source paths attached to each finding into the categorized research and experiment material.
3. Use [`RECORD_TEMPLATE.md`](RECORD_TEMPLATE.md) when promoting a new investigation into a durable research record.
4. Check [`MODDING_SURFACE.md`](MODDING_SURFACE.md) for the current practical capability map.

## Topic map

| Topic | Primary area | Questions covered |
|---|---|---|
| Runtime and native behavior | `runtime/`, `static-analysis/` | What code paths, hooks, and native boundaries can be observed safely? |
| Entities and observers | `entities-and-observers/` | How are players, items, containers, and ECS entities discovered and identified? |
| Building and placement | `building-and-placement/` | How do selection, previews, snapping, blueprints, and placement commit work? |
| Inventory and items | `inventory-and-items/` | How are item metadata, ownership, slots, and transfers represented? |
| Settings and administration | `settings-and-admin/` | What settings, admin actions, multiplayer, and server behaviors are exposed? |
| Data formats | `data-formats/` | What can KFC and extracted game data tell us, and how reproducible is the extraction? |
| Lua modding | `../implementations/` | What can be changed through existing Lua mod patterns? |
| Tooling | `../tools/` | Which tools collect, correlate, or validate evidence? |

## Project-to-research links

- Architect: `../case-studies/source/mods-drive/Architect_Mod/`
- Control Center variants: `../case-studies/source/mods-drive/Control_Center/` and related paths
- EmberVault: `../case-studies/source/mods-drive/EmberVault/`
- Emberworks: `../case-studies/source/mods-drive/Emberworks/`
- Cheat tables: `../experiments/source/mods-drive/Cheat Tables/`
- External research workspace: `../research/source/research-drive/`

## Status

This index is the canonical navigation layer. The source archive is retained locally for provenance, while durable conclusions should be summarized in `FINDINGS.md` and linked to evidence rather than copied without context.
