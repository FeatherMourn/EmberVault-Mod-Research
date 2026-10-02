# Localization-to-item transition evidence — 2026-09-28

The isolated research probe `localization_item_transition_20260928` was run against game/EML build `1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z` in a fresh session.

Verified in sequence:

- new localization tag registration;
- new localization collection registration;
- lookup of donor bed `2940001508`;
- independent `keen::ItemInfo` clone registration;
- item ID mutation to `3987654701`;
- debug-name mutation;
- name and description GUID assignment;
- object ID reassignment;
- normal completion marker.

The session produced no loader panic or error marker. This narrows the earlier combined localized-bed failure: collection registration itself does not prevent item cloning or display-field mutation. Catalog visibility, recipe/placement text, persistence, fallback behavior, and the original combined probe sequence remain unverified and stay research-only.

Structured evidence: `research/probe_sessions/localization_item_transition_evidence_20260928.json`.
