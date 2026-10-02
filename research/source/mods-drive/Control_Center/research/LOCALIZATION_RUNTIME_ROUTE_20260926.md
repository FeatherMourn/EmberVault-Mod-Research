# Localization runtime route

The EML source contains a concrete binary-content route for localization:

1. Read the existing `keen::LocaTagCollectionResource`.
2. Resolve each locale's `ContentHash` with `game.guid.from_content_hash`.
3. Read the binary blob as `keen::LocaTagCollectionResourceData`.
4. Clone the `tags` array and add `HashKey32` IDs generated with the EML FNV-1a helper.
5. Serialize the data with `Buffer:write_resource` and create a new content asset.
6. Clone the collection resource and replace its English and locale content hashes.
7. Register the cloned collection through `game.assets.register_resource`.

Item-facing labels additionally use `keen::LocaTag` object references. The
helper exposes `register_tag` for creating those descriptors so an item clone
can point at a new label instead of reusing a vanilla GUID.

The reusable implementation is `research/runtime/kfc_localization_registry.lua`.
It is packaged into generated projects through the SDK. This proves that the
loader exposes the required primitives, but it does not yet prove that the
game's UI resolves newly-created localization tags. Runtime registration was
verified on build `1076226` using the generated standalone and atomic probes;
the result is recorded in `research/localization_probe_results_1076226.json`.
The helper remains UI-research-only until a controlled in-game test confirms
that a game-facing label resolves to a newly-created tag and the result is
captured with visual evidence.
