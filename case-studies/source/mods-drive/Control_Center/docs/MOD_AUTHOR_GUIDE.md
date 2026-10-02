# Mod-author guide

Use a unique manifest ID, declare the target game/EML build, and mark every
module `stable`, `experimental`, or `research-only`. Start from the supplied
clone and probe templates. Validate offline, test in an isolated profile, and
ship only evidence-backed capabilities. Never edit donor resources in place.

Research probes must include rollback instructions, required resource types,
and a versioned evidence report. Keep `TemplateResource` and other unverified
resource families quarantined. Imported original assets may include a
structured provenance record (`source`, `license`, `author`, `attribution`,
`url`, or `notes`); the record is integrity-checked and packaged, but does not
claim that the game engine can import or render the asset yet.

## Blender-generated visual modules

For model or material work, EnshroudedBlenderTools can export an EML package
without modifying the original KFC or DAT archives. Before staging an export,
run:

`python tools/verify_blender_export.py <export-folder>`

The check verifies the manifest, target RenderModel GUID, generated mesh
integrity, texture metadata, and optional icon metadata. A valid package is
still `research-only`: install it only through an isolated profile, capture
fresh catalog/placement evidence, and remove it with the ownership-aware probe
cleanup path before considering promotion.
