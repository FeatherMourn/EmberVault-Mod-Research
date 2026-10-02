# Current UI → Conceptual Workspace Migration v1

**Document type: ARCHITECTURE / MIGRATION.** This is a mapping plan only; the
v0.32 UI is not rewritten.

| Current surface | Future workspace | Rationale |
|---|---|---|
| Shapes | CREATE / Primitives | Procedural and primitive authoring share the same intent model. |
| Structure Recorder | STUDY / Recorder | Recording is evidence collection, not immediate editing. |
| Plan | PROJECT / Structures or BUILD / Transform | Destination depends on whether the user is organizing or editing. |
| Build Catalog | STUDY / Codex plus BUILD selectors | Catalog evidence and active selection should remain distinct. |
| Diagnostics | F7 / Diagnostics | Keep low-level evidence out of the creative path. |
| Admin | F7 / Admin | Administrative controls remain separate from build workflow. |

Existing F8/F7 controls and unsupported-operation labels remain authoritative
until an adapter capability is proven.
