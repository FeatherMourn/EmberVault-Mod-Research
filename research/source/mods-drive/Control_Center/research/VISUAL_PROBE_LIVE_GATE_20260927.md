# Visual candidate probe live gate — 2026-09-27

The generated candidate probe is ready, but the live game profile was not
modified because the isolation preflight did not pass.

Current gate results:

- EML proxy, mods directory, and logs directory are present.
- `isolation_ready` is false.
- Five research-only probes are installed.
- Three installed modules lack explicit `feature_state` metadata.
- The smoke profile leaves `emberworks_worldwright_probe` unaccounted for.
- The dry-run profile planner returned `review_required`; no quarantine or
  other live filesystem mutation was performed.

Required before a controlled run:

1. Classify or explicitly exclude every installed module, especially
   `emberworks_worldwright_probe`.
2. Apply the reversible isolated profile only after that review.
3. Install the generated visual candidate probe inside that isolated profile.
4. Capture the EML log and restore the profile before any production use.

The candidate remains research-only and runtime-unverified.
