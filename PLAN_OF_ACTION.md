# EmberVault Mod Research — Plan of Action

## Operating rules

Work in small slices. Each slice must have a contract/fixture, implementation,
focused tests, documentation, a clean status check, a coherent commit, and a
push to `FeatherMourn/EmberVault-Mod-Research`. Research is read-only: do not
modify live game files, install mods, run in-game tests, attach to a live
process, or infer runtime behavior from static/package success.

## Slice 1 — Research record and evidence foundation

Define stable IDs for research records, findings, experiments, artifacts,
resources, donors, recipes, and handoffs. A record should carry source path or
URI, source hash, author/tool, captured time, game build, mod/tool versions,
experiment class, reproduction steps, inputs/outputs, limitations, related
records, and review state. Evidence should distinguish observed, inferred,
hypothesis, verified, blocked, and unsupported claims; confidence is a bounded
assessment of the stated claim, not a substitute for missing evidence.

Use the shared evidence-reference, promotion-evidence, recovery-reference,
module-manifest, and content-project-export contracts. Add valid, incomplete,
contradictory, stale-build, and unsafe-path fixtures before adding persistence.

## Slice 2 — Donor and recipe cataloging

Create immutable donor and recipe records with stable identity, display names,
ItemInfo/resource references, recipe inputs/outputs, stations, localization
references, RenderModel links, source/build scope, and evidence coverage.
Import prior donor catalogs and recipe studies once, record their canonical
source and duplicate provenance, and preserve unknown or unavailable fields.
Never calculate identity from a debug name or GUID alone and never treat a
missing local row as proof of absence.

## Slice 3 — KFC3 and RenderModel metadata indexing

Index only fields supported by verified extraction: resource type/hash, GUID,
part index, ContentHash, debug name, source file, build, relationships,
coverage, and evidence state. Keep decoder capability separate from indexed
metadata. Mark unavailable families explicitly. RenderModel records should
link meshes, materials, textures, icons, package paths, and donor resources
only where the source proves the relationship.

## Slice 4 — Search and filtering

Add deterministic offline search over IDs, names, GUIDs, resource types,
recipes, donor families, builds, tool versions, evidence states, source class,
and coverage. Filters must support verified/partial/unknown/blocked, static vs
synthetic vs runtime, current-build vs historical, and contradiction/open-
question presence. Search results must show provenance and limitations.

## Slice 5 — Provenance, confidence, contradictions, and gaps

Model source lineage as a graph rather than flattening citations. Detect exact
duplicates and near-duplicates, but retain historical copies as provenance.
Represent contradictions as explicit competing claims with independent
evidence, scope, and resolution status. Represent evidence gaps as required
questions or missing artifacts. A contradiction or gap must lower readiness and
block promotion where relevant; it must never be silently overwritten.

## Slice 6 — Offline package and Blender research

Ingest Blender/export metadata, package manifests, hashes, validation reports,
and generated-file inventories without changing the original folder. Verify
paths, expected files, schemas, versions, and package safety offline. Preserve
the distinction between generated package evidence, visual preview evidence,
and runtime rendering/interaction evidence. Do not install packages or call
external tools as a runtime authority.

## Slice 7 — Runtime-test evidence boundary

Provide an import format for historical or user-supplied runtime evidence with
exact build identity, environment, setup, test steps, observed result,
artifacts, rollback/recovery notes, and tester/source. The module may catalog
runtime evidence but must not initiate tests in this phase. Registration,
recipe visibility, icon/name display, model visuals, placement, interaction,
persistence, and multiplayer remain separate claims. Static, synthetic, or
successful packaging evidence cannot promote any runtime claim.

## Slice 8 — Content Creator handoff

Expose read-only donor, recipe, resource, RenderModel, package, and evidence
summaries keyed by stable IDs. Handoffs must include build/tool compatibility,
source hashes, confidence/review state, open questions, contradictions, and
explicit unsupported fields. Produce the Content Project Export evidence
summary without granting runtime approval or mutating source artifacts.

## Slice 9 — Web Catalog publication records

Generate a separate sanitized publication record containing title, summary,
content type, compatibility/build scope, evidence state, provenance summary,
authors/licensing, review status, public-safe artifacts, and related records.
Exclude local paths, save paths, credentials, private logs, process details,
unreviewed claims, and sensitive runtime evidence. Publication is a reviewed
export, not a mirror of the research store.

## Slice 10 — Testing, packaging, migration, recovery, and backup

Add unit and contract tests, index determinism tests, duplicate/contradiction
tests, unsafe-path tests, clean-install/package tests, migration fixtures,
corruption and interrupted-write recovery tests, and export sanitization tests.
Use atomic writes and backups for the research store, retain unknown fields
where safe, reject incompatible schemas, and provide recovery references.
Verify the module manifest and SDK boundary, then commit and push every slice
to GitHub. Do not mark a slice complete until its intended tests and backup
are confirmed.

## First implementation target

The first code slice is the record/evidence contract and fixture set. It should
be independent of the large archive, use only read-only local inputs, and end
with a machine-readable status report that can be consumed by Content Creator
and later by Web Catalog.
