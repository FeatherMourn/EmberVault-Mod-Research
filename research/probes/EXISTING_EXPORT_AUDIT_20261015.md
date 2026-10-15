# Existing EML export audit — 2026-10-15

This is a read-only audit of the existing export root:

`H:\SteamLibrary\steamapps\common\Enshrouded\export`

No files were changed, copied, deleted, or executed.

## Findings

- 20 files were present, including two ZIP archives and 18 JSON/text exports.
- Existing coverage includes architecture/item identity, blueprint identity,
  hammer categories, workbench/UI references, resource registration, world
  probes, and registry/procedural-building experiments.
- Existing exports are historical probe outputs from September 18–27, 2026.
- No platform-wide `get_resource_types()` inventory was present.
- No complete resource-by-type inventory was present.
- No standardized probe manifest with game build, EML version, input hashes,
  output hashes, and evidence states was present in the export root.

## Evidence boundary

These files are candidate source evidence only. Their contents must be hashed,
reviewed, and imported into Mod Research before they become authoritative
records. Existing probe claims remain build-scoped and do not establish
universal runtime behavior.

## Next collection priority

Run the new `platform_inventory_probe.lua` only after explicit approval for
live EML collection. It should be compared against this audit before import so
we do not repeat the existing item, blueprint, UI, resource-registration, and
world probe work.
