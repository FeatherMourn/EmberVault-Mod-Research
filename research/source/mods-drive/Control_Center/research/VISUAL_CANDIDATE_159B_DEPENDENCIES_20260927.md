# Candidate dependency inventory — 159b5f47

Candidate:

`159b5f47-aa61-4db9-8e64-06db850de6f6_177394c7_0.json`

Evidence from the read-only dependency resolver:

- 5 unique GUID references were found.
- All 5 references resolve to extracted KFC resources.
- Four references resolve to `RenderMaterialResource` records.
- The candidate RenderModel itself is present in the archive.
- No missing archive-level dependencies were detected.

This establishes archive completeness for the discovered GUID references only.
It does not establish that the resources can be registered by EML, that their
packed mesh/texture dependencies are complete, or that the model will render
correctly when assigned to the cloned bed. The next gate is isolated typed
resource registration followed by a fresh-session visual inspection.
