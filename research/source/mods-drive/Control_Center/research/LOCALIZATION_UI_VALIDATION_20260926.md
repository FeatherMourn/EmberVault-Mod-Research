# Localization UI validation boundary

## Latest controlled runtime rerun

On `2026-09-27T05:51:27Z` the live-KFC combined fixture completed the full
runtime path after the portable FNV-1a fallback and donor-recipe fallback were
deployed. The authoritative log records:

- `LOCALIZATION_TAG|ok=true`;
- `LOCALIZATION_COLLECTION|ok=true`;
- custom display-field hashes;
- `REGISTERED|itemId=3987654323|recipeId=3987654324`;
- item registry growth from `3520` to `3521` and recipe growth from `1954` to
  `1955`;
- unique recipe GUID `b3c6d8a1-2e47-5f90-8c13-7a6b4d9e2051`;
- `UI_LINKS|1|matching_sets=1`;
- no panic or fatal loader error in the run.

This upgrades custom localization from registration research to
`runtime-verified` on build `1076226`. It does not yet prove that the custom
label is visibly consumed by the Carpenter menu; that still requires a fresh
in-game screenshot.

## Fresh custom-name runtime result

The fresh-ID rerun at `2026-09-27T05:56:22Z` exercised the previously
unverified item-name path rather than the existing-recipe guard. The log shows
`DISPLAY_FIELDS|name=b80640f9-95dd-f64b-bf36-0bfb297efd90`, where that GUID is
the newly registered `LocaTag`, followed by:

- `RECIPE_IDENTITY|guid=c4d7e9b2-3f58-6a01-9d24-8b7c5e0f3162|id=3987654334`;
- `REGISTERED|itemId=3987654333|recipeId=3987654334`;
- `UI_LINKS|1|matching_sets=1`.

This proves the loader can construct a fresh item whose name reference points
to a newly registered localization tag. The remaining boundary is client-side
visual consumption: a Carpenter-menu screenshot must still confirm that the
custom text is rendered rather than merely accepted by the runtime registry.

## Visual boundary result

The follow-up Carpenter/Beds screenshot shows the inserted slot present but
blank when the fresh item uses the newly registered tag as `ItemInfo.name`.
This is direct evidence that build `1076226` accepts the runtime localization
resources but does not consume a same-startup custom `LocaTag` reference during
the catalog rendering pass. The stable production fixture therefore keeps the
donor name reference while retaining and testing custom localization
registration separately.

## Runtime result

The atomic combined probe `combined_localized_bed_probe_1076226` ran on build
`1076226` after the localization tag and matching locale entry were created and
before the cloned `keen::ItemInfo` was registered. In the isolated run at
`2026-09-27T01:40:18Z`, the current EML log records:

- a successful new `keen::LocaTag` registration;
- successful cloned `LocaTagCollectionResource` registration;
- successful item and recipe registration;
- item-registry growth from `3520` to `3521`;
- recipe-registry growth from `1954` to `1955`;
- a cloned UI set with the new recipe ID at index `8`;
- one matching UI set link;
- no runtime panic or fatal error from the corrected fixture.

The game reached the private world successfully after this run. The isolated
run removed the older bed-clone probe temporarily so it could not mutate the
donor recipe registry first; that probe was restored afterward. The controlled
Carpenter-menu screenshot from the earlier run showed the extra bed slot, but
its custom label did not resolve and the details panel still displayed the
donor bed label. The corrected run could not expose that panel through the
available saved-world navigation, so visual localization consumption remains
unproven.

The retained visual evidence is:

- `C:\Users\JoelT\.codex\visualizations\2026\09\26\01a0de47-d0c8-7283-8ee9-a73e635fe9d5\localized-bed-world3.png` — Carpenter → Beds visibly contains an additional slot; the slot has no proven custom label.

## Current conclusion

Localization registration is a usable platform capability and is packaged in
the SDK. The corrected atomic route is now `runtime-verified`, but the feature
remains `UI-research-only` until a game-facing label resolves in a fresh
Carpenter-menu screenshot. The next research step is to identify the exact
locale collection root or UI lookup linkage used by the active build, then
repeat the fixture with fresh visual evidence.

The probe was removed after testing. No vanilla game files were modified.

The latest-run structured evidence is cataloged in
`research/content_fixture_results_1076226.json`.
