# Visual substitution guide

Icon, model, scene, material, texture, scale, and offset changes are separate
capabilities. Reusing a known-good reference is safer than assigning a file
path. Catalog rendering and placed-object rendering must be tested separately.
Visual substitution remains experimental or research-only until human-visible
same-build evidence and rollback are recorded.

## Authoring a variant

The reusable `research/templates/visual_variant_template.json` describes the
visual intent. A content definition may embed the same shape under
`visual_variant`; Control Center translates it into the research-gated asset
substitution plan automatically.

```json
{
  "donor_id": 2940001508,
  "new_item_id": 3987654501,
  "visual_variant": {
    "replacement_model_guid": "KNOWN_REFERENCE_GUID",
    "materials": [],
    "textures": [],
    "color_adjustments": [
      {"target": "frame", "color": "#884422"}
    ],
    "catalog_preview": "donor-fallback",
    "placement_preview": "donor-fallback"
  }
}
```

The compiler preserves donor mechanics and marks the resulting plan
`research-only`. A successful resource assignment is not proof that the game
renders the replacement. Promotion requires same-build catalog or placement
evidence, rollback evidence, and a fresh-launch persistence check where the
feature affects saved objects. File paths are not treated as engine resource
references; use typed, known-good resource GUIDs until original asset import
is separately verified.

For repeatable authoring, compile the template into a validated variant
definition without hand-editing the output:

```text
python tools/build_visual_variant.py research/templates/visual_variant_template.json research/variants/my_bed_variant.json 3987654501
```

The command rejects donor overwrite, malformed scale/offset vectors, unsafe
preview policies, invalid colors, and unapproved resource substitutions. The
output remains research-only and records resource-graph and promotion evidence
requirements.

## Blender-generated asset route

The community project
[EnshroudedBlenderTools](https://github.com/Baik90/EnshroudedBlenderTools) can
import KFC3 RenderModels into Blender and export EML mod folders containing a
replacement or a new placeable model chain. Its current route is useful for
research and authoring, but it is not automatically a stable Control Center
module. Review its AGPL-3.0 license before redistributing or incorporating any
implementation code.

For an exported folder, use this workflow:

1. Keep the export outside the live `mods` directory initially.
2. Run the Control Center Blender-export validator against the folder.
3. Confirm the module ID, target RenderModel GUID, mesh hash, vertex count,
   vertex stride, and every texture-patch hash.
4. Place it only in an isolated research profile whose game build matches the
   export manifest.
5. Capture catalog, item-info, placement, fresh-launch, and rollback evidence
   separately.
6. Remove the export and restore the stable profile before normal gameplay.

The current validator implementation is `core/blender_export_validator.py`.
A valid package means the artifact is internally consistent; it does not prove
that the engine renders it. Custom icons, arbitrary new components, freely
changed collider groups, and unsupported texture slots remain restricted until
fresh runtime evidence exists.

### BlenderTools limits to keep in mind

Control Center also checks the limits that can make an otherwise valid export
unsafe to test:

- A full-topology mesh must stay at or below **65,535 vertices**. If the export
  includes LOD metadata, every listed LOD must stay within that limit too.
- Collider metadata is accepted only for **Box, Sphere, Spheroid, Cylinder,
  Capsule,** and **Tapered Capsule** shapes. Changing collider counts or shapes
  is not yet proven safe for gameplay.
- Texture changes must target an existing material slot and preserve the
  source dimensions and compressed format. Custom icon registration is still
  unproven, so a package can validate while the game continues to use the
  donor icon.

These checks protect the test package; they do not establish engine support.
Rendering, collision, catalog behavior, persistence, and rollback still need
separate same-build evidence in Research Lab.

### Beginner click path in Control Center

1. Close Enshrouded.
2. Open **Content Studio** and click **Check BlenderTools export**.
3. Select the folder exported by BlenderTools. Do not select `render_data.bin`
   or the `src` folder by itself.
4. When validation succeeds, Control Center copies the package into its
   `custom_content/imports` review area. Nothing is installed into the live
   game at this step.
5. In the **Known Content Projects** list, find the entry labeled
   **RESEARCH-ONLY IMPORT** and click **Review import**.
6. Use **Research Lab** to prepare the isolated test. Only promote the asset
   after visible catalog/placement evidence, restart evidence, and rollback
   evidence have been recorded.

If validation is blocked, follow the missing-file or hash message shown by
Control Center. Do not copy the package into the live `mods` folder manually.
