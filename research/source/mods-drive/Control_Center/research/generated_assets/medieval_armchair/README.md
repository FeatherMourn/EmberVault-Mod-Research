# Medieval armchair source asset

This folder contains a procedural low-poly OBJ/MTL source mesh generated for
the Control Center original-asset import test.

- `medieval_armchair.obj` — mesh source
- `medieval_armchair.mtl` — wood, leather, and metal materials

This is not yet an Enshrouded or BlenderTools runtime export. BlenderTools is
required to produce the target `render_data.bin`, resource graph, collision,
LOD, and EML package. Preserve the separate material names when importing so
the material-substitution test can address the chair frame and upholstery
independently.

Suggested test identity: `cc_medieval_armchair_001`.
