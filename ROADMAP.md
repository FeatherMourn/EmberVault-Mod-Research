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

The read-only catalog slice now includes a durable SQLite store, 19 imported
records, provenance-checked evidence references, deterministic search filters,
explicit contradiction records/resolution states, a design-only Content Creator
handoff, and a deterministic, review-scoped Web Catalog publication generator.
Twenty-six tests pass. Identity normalization, broader intake, and the
Research Lab interface remain planned; runtime claims remain gated by direct
evidence.

## Research Lab evolution

The long-term product is an offline-first evidence-engineering platform, not
only a record catalog. The advanced capabilities below are intentionally phased
after the integrity foundation so the system remains useful at every stage.

### Phase A — Integrity and identity hardening

- [ ] Normalize canonical identities for donors, recipes, RenderModels, KFC3
  resources, Blender outputs, packages, and experiments.
- [ ] Detect duplicates and near-duplicates across files, records, and builds
  without merging distinct provenance or evidence boundaries.
- [ ] Add migration, corruption, recovery, clean-install, and export fixtures.
- [ ] Resolve or explicitly accept the open RenderModel evidence tension.

### Phase B — Provenance and relationship intelligence

- [ ] Add a provenance graph linking sources, hashes, records, claims,
  experiments, tools, builds, and generated outputs.
- [ ] Add a resource graph connecting donors, recipes, RenderModels, registries,
  packages, Blender outputs, and evidence records.
- [ ] Add evidence scoring, contradiction detection, evidence-gap prioritization,
  and human review states.
- [ ] Add build-aware diffs for KFC3 metadata, records, packages, and findings.

### Phase C — Offline research tooling platform

- [ ] Define pluggable parser and analyzer interfaces for KFC3, RenderModels,
  recipes, archives, Blender exports, and logs.
- [ ] Add reproducible pipelines recording inputs, tool versions, output hashes,
  transformations, and limitations.
- [ ] Add sandboxed offline tool execution with explicit filesystem boundaries
  and no live-game or network mutation.
- [ ] Add versioned research bundles that can be recovered and shared offline.

### Phase D — Research Lab application

- [ ] Build an offline-first Lab browser over the authoritative catalog rather
  than creating a second store in the UI.
- [ ] Add faceted search, relationship views, build comparisons, evidence review,
  contradiction workflows, and capability matrices.
- [ ] Add research notebooks combining structured records, notes, comparisons,
  experiment outputs, and generated reports.
- [ ] Add a plugin API so new research tools can be introduced independently
  from the catalog core.

### Phase E — Ember Vault integration and publication

- [ ] Connect the Lab to Control Center for profiles, permissions, and recovery
  context while preserving Mod Research ownership of evidence.
- [ ] Provide reviewed donor and recipe metadata to Content Creator.
- [ ] Generate sanitized, reproducible Web Catalog publication records.
- [ ] Add cross-repository contract fixtures and CI for every handoff path.

Every advanced feature must preserve the same rule: conclusions are traceable,
reproducible, comparable across builds, and never promoted beyond their
evidence.

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
