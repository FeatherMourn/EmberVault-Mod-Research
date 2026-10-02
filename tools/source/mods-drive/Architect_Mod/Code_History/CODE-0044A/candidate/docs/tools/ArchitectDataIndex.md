# ArchitectDataIndex v1

ArchitectDataIndex builds a deterministic, searchable SQLite database for
Enshrouded revision 1076226. It is an offline subsystem: it reads the local
executable only to verify its SHA-256 and ingests existing Architect exports and
research files. It does not decode or modify KFC archives, launch the game,
attach to a process, or interact with the native runtime.

## Build

From the Architect Toolkit root:

```powershell
python tools/ArchitectDataIndex/builder.py
```

The output is `data/architect_game_data_1076226.sqlite`. An existing database
whose revision, executable hash, or schema version differs is rejected. Use
`--replace-incompatible` only when intentionally replacing such a database.

The generator recreates the database through a temporary file, inserts records
in stable order, and uses the newest verified input timestamp as its reproducible
generation timestamp. Rebuilding identical inputs produces an identical file.

## Queries

Human-readable output is the default:

```powershell
python tools/ArchitectDataIndex/query_index.py item 631520303
python tools/ArchitectDataIndex/query_index.py item-name Foundation
python tools/ArchitectDataIndex/query_index.py material-id 128
python tools/ArchitectDataIndex/query_index.py template 00000000-0000-0000-0000-000000000000
python tools/ArchitectDataIndex/query_index.py impact 00000000-0000-0000-0000-000000000000
```

Append `--json` for JSON output. No result means that the requested identity is
not present in the locally audited subset; it does not establish absence from
the game.

## Schema and identity

The schema includes all requested core tables plus `input_sources`, `coverage`,
`scene_entity_templates`, `actor_sequence_events`, and generic
`resource_relationships`. Resource identity preserves GUID, type hash, part
index, ContentHash, debug name, source file, evidence status, and source build
where supplied. ItemId is accepted only from an explicit source field or
research statement and is never calculated from a debug name or GUID.

Recipe inputs and outputs, registries, blueprint mappings, templates/components,
skill/perk/impact relationships, and actor-sequence events have normalized
tables. Empty tables are intentional when no verified local export supports the
family.

## Provenance

`builds` records revision 1076226, the validated executable SHA-256, schema
version, optional reflection identity, and generation timestamp. `input_sources`
records the absolute path and SHA-256 of every ingested source. `coverage`
distinguishes partially available families from unavailable ones.

Current sources include the audited files under `export/architect_toolkit` and
the v0.17 ItemStack/terrain-stone research statement. The large `.kfc` and
`.kfc_resources` files are present locally, but this project contains no
verified decoder that preserves their GUID/type/part/ContentHash semantics;
v1 therefore does not scrape or guess records from them.

## Limitations

The local exports provide a useful but partial item, item-registry, recipe-output,
and blueprint subset. They do not currently provide verified recipe inputs,
terrain/building configuration bodies, snap rules, templates, attributes,
perks, skill nodes, impacts, actor sequences, map markers, or camera states.
Those tables remain empty and are marked `UNAVAILABLE` in `coverage`.

Run tests with:

```powershell
python -m unittest discover -s tools/ArchitectDataIndex/tests -p "test_*.py" -v
```

Generate the player-facing read-only semantic catalog from the index:

```powershell
python tools/ArchitectDataIndex/build_catalog.py
```

This emits `bridge/build_catalog.json` and `bridge/snap_rule_catalog.json`.
The v0.24.1 builder first verifies and ingests
`data/incoming/architect_building_kfc_bundle_1076226.zip` (the expected SHA is
recorded in the builder), extracting it under
`data/kfc_sources/building_1076226/`. It also emits
`bridge/build_catalog_validation.json` via:

```powershell
python tools/ArchitectDataIndex/build_validation.py
```

Coverage is explicit. Supplied building-focused families are populated from
the bundle; families not present in verified sources remain `UNAVAILABLE` and
no rows are invented.
