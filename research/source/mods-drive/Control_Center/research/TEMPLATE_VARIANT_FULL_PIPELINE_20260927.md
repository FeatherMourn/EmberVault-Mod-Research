# Real bed template variant pipeline — 2026-09-27

The compiler was run against the extracted bed `TemplateResource`, not a
synthetic fixture.

## Result

- Project validation: `valid = true`
- Component inventory: `34`
- Selected model path: `components[23].$value.model`
- Donor hash: 64-character SHA-256
- Candidate hash: 64-character SHA-256
- Runtime mutation: disabled
- Mechanics policy: preserve all other components

The generated candidate is staged as a project artifact and remains
research-only until an EML runtime route can consume the template graph.

Promotion is now explicitly gated on five conditions: the replacement model
must exist on the target build, the runtime must accept the TemplateResource
graph, the placed object must visibly use the replacement, gameplay components
must be preserved, and rollback must restore the recorded donor graph.
