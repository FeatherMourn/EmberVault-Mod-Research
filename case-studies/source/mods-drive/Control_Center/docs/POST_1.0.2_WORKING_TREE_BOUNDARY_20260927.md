# Post-1.0.2 working-tree boundary — 2026-09-27

The portable 1.0.2 artifact was rebuilt from the current source and its hash
was updated in `packaging/RELEASE_MANIFEST_1.0.2.json`. Inno Setup is not
installed on this host, so the 1.0.2 installer remains the previously built
and hash-verified artifact; it was not rebuilt during this refresh.

Post-release source changes include:

- generated-probe donor-scan log reduction;
- Research Lab generated-item/recipe evidence fields and compact event capture;
- oversized-log preflight warnings;
- explicit research-only module inventory reporting;
- fresh-session log baseline and stale-log detection;
- synchronized localization payloads and research-only localization probes;
- machine-validated four-phase capability audit;
- release verification now validates the capability audit and its evidence links;
- additional regression coverage.

At the time of this boundary the source tree passed 388 tests. Subsequent
research-cycle validation, compiler policy, and update-resilience coverage
raised the source total to 399 tests at that point; the latest current source
total is 421 tests. The packaged portable artifact was
built from the preceding source boundary and is hash-verified in the 1.0.2
manifest. A future release refresh should
rebuild the installer as well and publish a new manifest before claiming full
portable/installer parity.

The refreshed portable executable also completed the packaged
`--status --game-dir H:\\SteamLibrary\\steamapps\\common\\Enshrouded` command
with exit code 0. The windowed build does not stream its JSON report to the
terminal, so this verifies executable startup and command completion rather
than duplicating the source-side health-report contents.
