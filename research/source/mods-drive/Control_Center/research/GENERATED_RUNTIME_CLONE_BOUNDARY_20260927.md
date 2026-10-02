# Generated Runtime Clone Boundary — 2026-09-27

## Verified

- Steam-managed launch is required for a valid EML smoke session.
- EML accepts loader capabilities such as `patch`; Control Center-only capability names must remain metadata.
- `src/mod.lua` is executed as a top-level patch script on the current build.
- Generated modules are cached by manifest identity; diagnostic probes require unique IDs.
- The generated module can enumerate `keen::ItemInfo` resources.
- The verified donor GUID `01474f79-6b5a-4bcd-999d-7e9339fda91c` is found during the first resource scan.
- The scan completes successfully when the donor is selected by GUID.

## Current boundary

The generated probe reaches `DONOR_SCAN_DONE|true` but has not yet produced `CLONED_ITEM`. The remaining boundary is the call that registers a new `ItemInfo` from the donor resource. The existing combined furniture fixture remains the runtime baseline because it performs the same operation successfully in its established script path.

## Safety state

- Every generated probe was installed under a unique folder and moved to `H:\Enshrouded_ControlCenter_Backups` after testing.
- No experimental generated probe remains in the live mods directory.
- The vanilla donor and existing stable probes were not overwritten.
- Full Control Center test suite: **236 tests passed**.

## Next experiment

Compare the generated clone call against the stable fixture at the smallest possible scope: a top-level script that performs only donor lookup, closure-wrapped `game.assets.register_resource`, and one success/failure log. Do not add recipe, localization, icon, or UI operations until that minimal registration call is independently verified.
## Minimal compiler probe v21

The compiler now supports a `minimal_probe` definition mode that emits only a
top-level donor lookup, `pcall(game.assets.register_resource(...))`, and marker
logs. The generated package was validated and temporarily staged as
`minimal_clone_probe_20260927_v21` with a unique manifest ID and the valid EML
`patch` capability. It was then moved to
`H:\Enshrouded_ControlCenter_Backups\20260927-minimal-clone-probe-v21`.

The first immediate launch check did not observe a refreshed session, but the
EML log subsequently contained fresh probe events:

- `DONOR|true`
- `REGISTER|true|Resource: ...`
- `CLONED_ITEM|3987654369`

This verifies that the generated direct `game.assets.register_resource` route
can clone an `ItemInfo` resource in the current runtime. It does not yet prove
that the clone is indexed in the item registry, linked to a recipe, visible in
the UI, or safe from duplicate-ID collisions. The probe was removed from the
live mods directory and preserved at
`H:\Enshrouded_ControlCenter_Backups\20260927-minimal-clone-probe-v21`.

