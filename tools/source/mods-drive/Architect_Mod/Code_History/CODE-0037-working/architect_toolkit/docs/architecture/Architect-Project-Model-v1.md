# Architect Project Model v1

**Document type: ARCHITECTURE.** A project is a small semantic envelope around
existing recordings and plans, not a giant database.

```yaml
projectId: string
name: string
worldIdentity: optional object
boundaries: optional spatial registry references
phase: optional string
layers: []
palette: []
structures: []
surveyPoints: []
guides: []
markers: []
history: []
versions: []
collaborators: []
permissions: optional object
```

Runtime/network fields remain optional and unresolved. Existing
`architect.structure.v1` recordings and `architect.placement_plan.v1` plans
are referenced by ID/path rather than rewritten.

## Shared spatial registry

One registry serves project boundaries, survey points, waypoints, road plans,
structure anchors, camera points, notes, and work zones. Entries carry a kind,
stable ID, optional world identity, coordinates, bounds, tags, provenance, and
visibility. Proven Q32.32 helpers may be used for recorded placement
coordinates; arbitrary world coordinates must not be labeled Q32.32 without
evidence.

## Target Resolver contract

Target kinds are `building`, `terrain`, `entity`, `plant`, `item`, and
`unknown`. A resolved target may include world identity, item identity,
material, transform, bounds, resource identity, and project membership. Every
field is optional and provenance-bearing; actions consume capabilities rather
than assuming a specific UI.

## Assist Engine and operation planner

The non-mutating Assist Engine accepts selection, structure, project,
materials, dimensions, and constraints and returns suggestions, guides,
alternatives, preview candidates, and warnings. `ArchitectOperationPlan`
unifies place, remove, replace, transform, terrain, and entity intent with
adapter requirements, validation/preview state, risk, and inverse metadata.
`architect.placement_plan.v1` remains supported as a specialized plan.
