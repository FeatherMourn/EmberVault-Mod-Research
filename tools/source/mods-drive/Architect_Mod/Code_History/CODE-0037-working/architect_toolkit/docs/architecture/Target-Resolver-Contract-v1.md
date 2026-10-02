# Target Resolver Contract v1

**Document type: ARCHITECTURE.** Offline contract only; no acquisition,
process access, or mutation is implemented. The concrete contract is
`tools/ArchitectCore.target.ArchitectTargetObservation`.

`TargetResolver.resolve(request)` may return a partial target. `kind` is one of
`building`, `terrain`, `entity`, `plant`, `item`, or `unknown`. Optional fields
are `worldIdentity`, `itemIdentity`, `entityIdentity`, `material`, `transform`, `bounds`,
`resourceIdentity`, and `projectMembership`. Each populated field carries a
provenance source and confidence/status. Missing fields are normal and must not
be fabricated from nearby values. The immutable observation contract bounds
confidence to 0..1 and requires provenance for semantic payloads attached to
an `unknown` kind; it does not imply a live resolver exists.

Actions such as inspect, measure, copy, select-connected, and Codex search
consume capabilities declared by the vanilla adapter map; they are not
hard-coded assumptions about a particular UI or native object.
