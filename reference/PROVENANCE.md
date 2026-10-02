# Provenance and canonicalization policy

## Source layers

1. **Source archive** — local staging copy of authored files from the research drives. It preserves original paths and is ignored by Git because it contains temporary and pathologically nested working output.
2. **Categorized source** — committed copies under `research/source`, `experiments/source`, `tools/source`, `implementations/source`, and `case-studies/source`. These retain source paths but are organized by role.
3. **Canonical records** — concise, version-aware findings under `research/records`. These are the preferred citation targets.
4. **Registries and indexes** — `research/INDEX.md`, `research/FINDINGS.md`, `research/SOURCE_MAP.csv`, and the reference reports.

## Duplicate handling

`DUPLICATES.md` groups committed files by SHA-256. A duplicate is not automatically deleted: it may document a handoff, historical build, or project context. However, duplicate copies should not be cited as independent evidence. Promote one canonical record and list the other copies as provenance only.

## Version handling

`VERSION_MATRIX.csv` is an automatically extracted lead list, not authoritative version metadata. Canonical records must verify the build from the document's scope, executable hash, bundle hash, or another explicit source. If no exact version is known, record `unknown` rather than inferring one from a filename.

## Review states

- `unreviewed` — cataloged but not read into a canonical conclusion.
- `triaged` — topic and likely role identified.
- `synthesized` — represented by a canonical record.
- `verified` — evidence and reproduction details reviewed for the stated build.
- `obsolete` — retained for history but invalid for current work.
