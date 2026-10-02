# World-generation research guide

World-generation support is currently research-only. The Control Center can
identify and read bounded metadata from scene, solid-voxel, fog-voxel, water,
and mapping resources for a pinned Enshrouded build. It cannot yet generate,
register, mutate, attach, or save a new world resource.

## Safe workflow

1. Generate or copy `research/templates/world_generation_plan_template.json`.
   The generator is faster for a pinned donor:
   `python tools/build_world_generation_plan.py --build <build> --scene-guid <guid> --output <plan.json>`
2. Pin the plan to the exact game build and donor scene GUID.
3. Describe intended layers and preview-only operations.
4. Run `tools/validate_world_generation_plan.py` before staging anything.
5. Use a research profile and a bounded read-only probe.
6. Record runtime evidence before considering a capability for promotion.

The validator rejects unsupported operation kinds, pre-approved operations,
missing safety prohibitions, and promotion flags set to true. Research probes
must not write the live world or save. Runtime evidence currently confirms
mapping-payload access only; it does not establish terrain authoring, world
generation, persistence, or multiplayer authority.
