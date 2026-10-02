# ItemInfo Material Runtime Boundary — 2026-09-29

The isolated external EML route attempted to assign a donor
`keen::RenderMaterialResource` GUID to a cloned `ItemInfo.material` field on
build `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z`.

The EML process aborted with `panic in a function that cannot unwind` before
archive registration completed. The transaction removed the research probe
after the failure, and the live game installation was not touched.

Conclusion: direct `ItemInfo.material` assignment is not a promotable runtime
route. The Content Wizard must continue to classify material and color changes
as research-only until a typed resource-graph route is proven.
