# Localization UI validation runbook — build 1076226

This runbook is the next gate after the successful tag-only smoke test. It is
required before marking custom localization as UI-verified.

## Candidate

Use the research-only pair:

- `research/probes/bed_clone_injection_1076226`
- `research/probes/localized_bed_label_v2_1076226`

The second module depends on the first. Do not install the older collection-
mutating localization probes for this test.

## Controlled procedure

1. Confirm the live preflight reports one stable module and zero research-only
   modules.
2. Prepare a fresh session boundary with `tools/prepare_probe_session.py` or
   the Research Lab button.
3. Install both candidates into an isolated profile, preserving the stable
   module and recording ownership backups.
4. Launch the game and wait for the Carpenter crafting catalog to load.
5. Locate the additional bed slot and capture the item details panel. The
   expected custom label is the probe's declared localized label, not the
   donor label.
6. Close the game, parse only the fresh-session log range, and save a boundary
   report plus the screenshot-backed catalog entry.
7. Restore the recorded stable-only live state and run live preflight again.

## Promotion criteria

Localization may move beyond experimental only if all of these are present:

- fresh-session tag and item/recipe registration markers;
- the custom label visibly rendered in the in-game details panel;
- the cloned item remains a separate catalog slot;
- donor behavior and stable module are preserved;
- rollback leaves zero research-only or unclassified live modules.

If the label remains donor text or the probe stops before registration, keep the
capability research-only and record the exact boundary. A successful runtime
tag alone is not UI evidence.
