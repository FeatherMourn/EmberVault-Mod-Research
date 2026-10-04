# EmberVault Mod Research Roadmap

## Purpose

Provide a read-only, evidence-backed research foundation for EmberVault. The
module organizes findings and searchable metadata for donor items, recipes,
RenderModels, KFC3 resources, Blender tooling, package experiments, and runtime
observations without modifying live game files or claiming behavior that has
not been directly observed.

## Current state — 2026-10-04

The repository intake is complete and the research corpus is present. The
module manifest declares an experimental, research-profile-only, read-only
worker boundary. Existing source material is valuable but is not yet a
first-class EmberVault research service: the durable catalog, indexes, schemas,
search, handoffs, migrations, and publication boundary are now implemented in
small verified slices. Broader normalization and recovery hardening remain.

| Capability | State | Current evidence / limitation |
|---|---|---|
| Research corpus and source map | partially verified | Categorized archive, indexes, provenance policy, and version matrix exist; canonical records still need normalized module ownership. |
| Evidence vocabulary and safety boundary | partially verified | Existing records distinguish offline/static, synthetic/staging, and live/runtime; shared contracts provide evidence references and promotion gates. |
| Donor and recipe catalog | partially verified | Durable SQLite catalog contains donor and recipe candidates plus recipe-schema findings; broader source import and identity normalization remain. |
| KFC3 / RenderModel metadata | partially verified | Durable catalog contains build-scoped offline KFC and RenderModel findings; decoder coverage and identity semantics remain source- and build-dependent. |
| Blender/package research | partially verified | Offline package validation and Blender handoff findings are cataloged; runtime rendering is explicitly separate. |
| Runtime evidence | blocked for this slice | No new runtime work is authorized; historical runtime records must retain exact build, setup, artifacts, and limitations. |
| Content Creator handoff | implemented, design-only | Read-only handoff carries donor, recipe, resource, evidence, provenance, confidence, limitations, and open questions without runtime approval. |
| Web Catalog publication | implemented, review-scoped | A deterministic generator reads the durable catalog and emits only an explicit reviewed-ID allowlist as sanitized public records; Web import remains a separate repository step. |
| Search/filtering and contradiction handling | implemented, evidence-aware | Deterministic search supports text, state, build, kind, confidence, and evidence-gap filters; contradictions have explicit open/resolved/accepted-uncertainty states. |

### Updated implementation snapshot

The read-only catalog slice now includes a durable SQLite store, 12 imported
records, provenance-checked evidence references, deterministic search filters,
explicit contradiction records/resolution states, a design-only Content Creator
handoff, and a deterministic, review-scoped Web Catalog publication generator.
Twenty tests pass.
Migration/recovery/package hardening and wider source ingestion remain active
work; runtime claims remain gated by direct evidence.

## Dependencies and exclusions

- Consume EmberVault Contracts and Module SDK; do not redefine their shared
  interfaces locally.
- Control Center remains authoritative for profiles, operations, recovery, and
  permissions.
- Content Creator consumes read-only donor/evidence metadata and never receives
  an implicit runtime approval.
- Web Catalog receives only sanitized, reviewed, build-aware records.
- No live game file mutation, mod installation, in-game testing, process hooks,
  save changes, or runtime claims without direct evidence.

## Milestones

1. Normalize the research record, evidence, provenance, build, and confidence
   models against Contracts v1 and add fixtures.
2. Build immutable donor/recipe/RenderModel/KFC3 indexes with source hashes,
   coverage, and build scoping.
3. Add deterministic search and filters, including evidence state, build,
   source type, content type, and contradiction/open-question status.
4. Add offline package and Blender research adapters that preserve original
   artifacts and never install them.
5. Add runtime-evidence ingestion with strict observation boundaries and no
   promotion from static or synthetic success.
6. Add Content Creator handoff records and Web Catalog publication records.
7. Add migration, corruption/recovery, packaging, clean-install, and GitHub
   backup verification.

## Definition of done

- [ ] Every record has stable identity, provenance, build context, evidence
  links, confidence, limitations, and review state.
- [ ] Conflicts and evidence gaps are visible and cannot be silently resolved.
- [ ] Donor and recipe metadata can be searched and handed to Content Creator
  without copying unsupported claims.
- [ ] Offline, synthetic, and runtime evidence remain distinct in storage,
  queries, UI results, and exports.
- [ ] Public exports are sanitized, reviewed, reproducible, and build-aware.
- [ ] Tests, migrations, package verification, recovery checks, documentation,
  focused commits, and GitHub backup pass.
