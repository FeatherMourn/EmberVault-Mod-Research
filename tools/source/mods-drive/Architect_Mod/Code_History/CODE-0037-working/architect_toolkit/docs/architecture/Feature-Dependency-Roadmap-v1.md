# Feature Dependency Roadmap v1

**Document type: ROADMAP.** Build from shared primitives, not isolated UI
excitement. The dependency graph in
`bridge/feature_dependency_graph.json` is validated for duplicate IDs,
unknown references, and cycles.

## Highest-leverage sequence

1. Target Resolver contract and a safe, read-only target observation milestone.
2. Continue index-backed Codex/Search, which is already offline-proven.
3. Preserve Structure Recorder and offline transforms/history.
4. Study manual selection and runtime blueprint authority only with a safe,
   low-frequency observer; the old tracking-item mutation is permanently
   disallowed.
5. Defer placement submission, terrain writes, replacement, and multiplayer
   actions until the relevant vanilla authority is proven.

Features such as Copy, Paste, Move, Rotate, Mirror, Line, Wall, Floor, Arrays,
Symmetry, Undo/Redo, Material Eyedropper, Replace, Landscape tools, Wayfinder,
Freecam, and Codex are represented with explicit blockers and milestones.

`tools/ArchitectCore/recommend.py` derives a bounded candidate list from the
validated graph; `bridge/next_capability_recommendation.json` is generated
output, not a hard-coded single winner.
