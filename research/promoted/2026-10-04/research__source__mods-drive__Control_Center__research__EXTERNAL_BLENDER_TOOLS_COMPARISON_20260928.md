# EnshroudedBlenderTools research comparison

Date: 2026-09-28  
Source: [Baik90/EnshroudedBlenderTools](https://github.com/Baik90/EnshroudedBlenderTools)  
Reviewed revision: `3e204071bb5356aa0640cc30d35cfe0e8223c63a`

## Executive finding

This is the strongest external evidence found so far for the original-asset
and visual-variant branch of the project. The Blender extension reads KFC3
`keen::RenderModel` resources, imports mesh data and materials, exports
replacement model data, creates isolated material copies, and generates EML
mod folders. It also describes a separate new-model path that clones a
placeable template, ItemInfo, recipe, and localization data.

It does not make arbitrary engine components available, does not solve custom
catalog icons, and does not prove every generated asset works in a fresh game
session. Its README explicitly identifies build targeting, texture-slot
constraints, a 65,535-vertex full-topology limit, inherited recipe behavior,
and unresolved icon registration.

## Capabilities relevant to our goal

- RenderModel search by debug name or GUID.
- Import of geometry, UVs, normals, tangents, bitangent handedness, LODs,
  materials, and supported textures.
- Topology-preserving replacement export.
- Full-topology export with regenerated vertex/index streams, limited to
  65,535 generated vertices.
- Primitive collider import/export while preserving the existing collider
  group count and shapes.
- Isolated `keen::RenderMaterialResource` copies with custom texture files.
- New RenderModel, entity-template, ItemInfo, recipe, and localization output
  from an existing placeable base.
- EML mod-folder generation without patching the original KFC or DAT archives.

## Important limitations

- Custom catalog icons are exported but reported blank in the game UI; icon
  texture registration remains unresolved.
- New models inherit the selected base recipe's ingredients, workstation,
  category, comfort, and unlock conditions in the current workflow.
- Custom textures must preserve the target slot's dimensions and compressed
  format, and the target material must already contain that slot.
- Arbitrary new entity components are not implemented.
- Collider shapes cannot yet be freely added or removed.
- All target LODs currently use the same generated replacement mesh.
- The project targets a documented game build and Blender 5.2 LTS; build drift
  must invalidate or revalidate the evidence.
- The repository is AGPL-3.0. We should use it as an external tool/reference
  or obtain compatible licensing guidance before copying implementation code
  into Control Center.

## Effect on our capability classifications

This evidence strengthens the `original_mesh_asset_import` and
`icon_color_material_texture_model` research paths, but does not by itself
promote them to verified. The existing promotion rule remains appropriate:
one fresh isolated target-build session must prove registration, dependency
resolution, visible catalog/placed use as applicable, and rollback.

The external sample package was independently checked by the Control Center
validator. Evidence is recorded at
`research/probe_sessions/blender_export_package_validation_20260928.json`.
That record intentionally contains no runtime claim.

The practical next experiment is no longer “can a mesh be serialized at all?”
It is a controlled round trip:

1. Export one topology-preserving replacement from Blender Tools.
2. Install it only in an isolated research profile.
3. Capture EML logs, catalog/item-info/placement screenshots, and a fresh
   launch readback.
4. Verify that unrelated models and the donor item remain unchanged.
5. Remove the generated module and restore the stable profile.

For a genuinely new bed variant, use the tool's New Model + Recipe route with
the existing bed as the placeable base, then compare the generated resource
chain against our Control Center clone definition. Treat the resulting item as
experimental until its save persistence and icon behavior are independently
verified.

## Development acceleration decision

Control Center should integrate with this workflow at the package boundary:
validate the generated EML module, check its build and resource metadata, stage
it through the isolated research profile, and collect the same rollback and
runtime evidence used by native probes. We should not duplicate the Blender
mesh/material serializer until a reproducible round trip demonstrates a gap
that the external tool cannot cover.
