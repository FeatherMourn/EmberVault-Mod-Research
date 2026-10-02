# Animation graph variant authoring

Animation graph variants remain research-only. The supported authoring route
clones one verified `AnimationGraphResource2_0`, redirects one state to an
existing pose in that same graph, and attaches the clone through one
`keen::NpcCollection.uiRendering.animationGraph2` owner reference.

Start from
`research/templates/animation_graph_variant_template.json`. Give every probe a
new module ID and collision-safe clone GUID. The donor GUID, owner GUID, state
ID, original pose ID, and replacement pose ID must come from build-matched
evidence rather than guesses.

Generate a probe with:

```text
python tools/build_animation_graph_variant_probe.py DEFINITION.json OUTPUT_DIRECTORY
```

The generator rejects donor GUID reuse, template owners, arbitrary owner
fields, non-positive node IDs, identical before/after poses, non-research
classification, and missing safety prohibitions. Generated probes still must
use the normal prepared research cycle, transactional installer, isolated
launch, evidence capture, and restore workflow.

The current verified fixture redirects the Hunter NPC's `idle` state from pose
`2585692075` to its existing `idle_Var_02` pose `3890759935`. Structural edit
and attachment are verified. Visible changed behavior is not yet verified and
must not be claimed until an in-world observation is recorded.

Do not use this workflow to modify vanilla donors, animation payloads,
templates, entities, world state, saves, or multiplayer authority. Those are
separate capability gates.
