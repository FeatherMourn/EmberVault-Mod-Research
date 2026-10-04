# Mod Research intake audit — 2026-10-04

## Authority and preservation

The authoritative destination is the `EmberVault-Mod-Research` repository.
The workspace at `I:\My Drive\Enshrouded Mods` remains the source archive and
was not altered or deleted. This intake copies evidence-bearing material; it
does not remove or rewrite the source files.

The older `Enshrouded_Mod_Research` checkout contains approximately 7,092
files, including categorized research, experiments, tools, implementations,
case studies, inventories, and historical source snapshots. Other major source
areas include `Architect_Mod`, `Control_Center`, `Emberworks`, `ENSHROUDED KFC
FILES`, and the EmberVault suite repositories. These areas contain substantial
overlap and are not independent evidence merely because they have different
paths.

## Triage rules

- **Promoted** — canonical or directly useful evidence with a source path,
  scope, and meaningful conclusion or limitation.
- **Partially verified** — useful material whose build, reproduction, coverage,
  or runtime boundary is incomplete.
- **Unverified** — lead material, plans, probes, or claims needing corroboration.
- **Blocked** — work prevented by a missing decoder, unsafe runtime boundary,
  unavailable artifact, or unresolved failure.
- **Unsupported** — claims outside the read-only research scope or without
  admissible evidence; retain only as historical context.

## Current audit result

| Area | State | Intake decision |
|---|---|---|
| Canonical research records | promoted | Copy into the module with original source path encoded in the filename and provenance retained. |
| Evidence indexes and dated Control Center findings | promoted / partially verified | Promote as evidence inputs, not as automatic capability approvals. |
| Donor and recipe research | partially verified | Promote discovery, schema, and requirement findings; defer normalized catalog rows until the record contract exists. |
| RenderModel and KFC3 findings | partially verified | Promote GUID/metadata and external-publication findings; retain decoder and coverage limits. |
| Blender and package work | partially verified | Promote offline validation and tool comparison findings; keep runtime rendering separate. |
| Runtime probing and hooks | blocked for new work | Preserve historical evidence and safety boundaries; do not run or extend runtime tests in this intake. |
| Large extracted archives, binaries, generated packages, and duplicate snapshots | unverified / provenance-only | Do not duplicate wholesale; reference by source path and hash in later indexed records. |
| EmberVault public catalog | publication-only | It is a consumer of reviewed, sanitized records, not a source for raw research. |

## Promoted first batch

The directory `research/promoted/2026-10-04/` contains 21 copied source
artifacts covering canonical records, evidence indexes, donor and recipe
research, RenderModel findings, Blender/package findings, runtime evidence
boundaries, provenance, and version leads. The flattened filenames preserve the
original relative source path with `__` separators; later record tooling should
replace this convenience layout with structured source references and hashes.

This batch is an intake slice, not a claim that every copied conclusion is
verified. Each record must be normalized, deduplicated, build-scoped, and linked
to evidence before it can feed Content Creator or Web Catalog.

## Next audit slices

1. Hash the promoted artifacts and build a duplicate/provenance map.
2. Extract structured donor, recipe, RenderModel, and KFC3 candidates without
   inventing missing identities.
3. Add record/evidence fixtures and import validation.
4. Review remaining source folders for unique material not represented by the
   canonical records or promoted findings.
5. Generate sanitized Content Creator and Web Catalog handoff candidates only
   after contradiction and evidence-gap review.
