# Control Center Phase 1 capability matrix

| Capability | State | Evidence / boundary |
|---|---|---|
| Clone an existing ItemInfo resource | Verified | Minimal generated probe: donor lookup, register_resource, and new item ID succeeded. |
| Preserve donor resource | Verified | Registration returns an independent resource; stable fixture never mutates the donor in place. |
| Change scalar identity fields | Experimental/verified per field | Requires donor schema validation and field-specific runtime evidence. |
| Change objectId to avoid donor de-duplication | Verified in stable fixture | Stable furniture fixture assigns clone.data.objectId = clone.guid. |
| Register a new recipe | Verified in stable fixture and generated probe | The generated route now reaches `REGISTERED_RECIPE` after matching by recipe ID or donor output; see `FULL_ICON_MODEL_BED_PROBE_V2_EVIDENCE_20260927.md`. |
| Add a recipe to the crafting UI | Verified for the furniture fixture | Clone the containing FbUiBundle set; do not append to fixed-size set.entries. |
| Add a new visible furniture slot | Verified for the stable furniture fixture | Existing combined localized bed fixture rendered an additional bed slot in-game. |
| Mutate ItemRegistryResource itemRefs from Lua | Partially verified | Array length grows, but typed contents are opaque/unreadable from Lua; do not treat length growth as catalog proof. |
| Custom localization payload | Research/partially verified | Runtime localization resources can register; same-startup ItemInfo display resolution remains build-sensitive. |
| Custom icon import / catalog preview | Research-only, catalog tile verified | In build 1076226, the isolated `catalog_icon_fallback_probe_20260928` accepted a typed `UiTextureResource` GUID, registered the clone, and produced a nonblank Carpenter catalog tile; see `research/probe_sessions/catalog_icon_fallback_runtime_evidence_20260928_r2.json` and `catalog_icon_fallback_nonblank_tile_20260928.png`. Placed-object appearance and save persistence remain unverified, so this route must remain research-only. |
| Color/material/texture/model substitution | Experimental/research-only by field | Clone-only `ItemInfo.iconModel` assignment and visible placed-model substitution are runtime-verified. A disposable external-copy probe accepted archive registration, but direct `ItemInfo.color` and `ItemInfo.material` runtime assignments aborted EML with `panic in a function that cannot unwind`; no live installation was touched. Keep color/material/texture routes research-only until a supported typed route is found and visibly verified. |
| Replace a bed visual while retaining mechanics | Verified for clone-only RenderModel assignment | The cloned bed retained its mechanics, appeared in a separate catalog slot, rendered in-world, and persisted after a fresh launch; original asset-graph substitution remains unverified. |
| Brand-new meshes or enemy/quest systems | Unsupported through current verified route | Requires original asset import, new graph construction, and authority/serialization research. |

## Authoring rule

Generated projects remain research-only unless the relevant row has current
runtime evidence for the same resource family and game build. Registry length,
successful Lua execution, or a green static test is not sufficient evidence of
in-game visibility.
