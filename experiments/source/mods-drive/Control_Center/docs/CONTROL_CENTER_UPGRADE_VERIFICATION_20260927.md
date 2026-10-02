# Control Center Upgrade Verification

Date: 2026-09-27  
Release: 1.0.1  
Game build: 1076226

## Result

The Control Center upgrade is verified for the portable application, the
per-user installer, and the current live mod configuration. The live health
report is healthy, the active mods directory contains no invalid manifest
directories, and both release artifacts match the release manifest.

## Verification gates

| Gate | Evidence | Result |
| --- | --- | --- |
| Automated tests | `python -m unittest discover -s tests -p 'test_*.py'` | 217 passed |
| Dashboard startup | Isolated launch of `dist/EnshroudedModHub.exe` | Passed |
| Runtime health | `python -m gui.launcher --status --game-dir ...` | Healthy; 0 current errors |
| Live mod layout | Direct inventory of the installed `mods` directory | 4 active directories; 0 invalid manifests |
| Deployment integrity | Ownership manifests, hash checks, state-classification tests | Passed |
| Portable release | `packaging/RELEASE_MANIFEST_1.0.1.json` | Size/hash/version match |
| Installer release | Per-user clean-directory install, launch, and uninstall-only pass | Passed; zero files remained |
| Stable bed fixture | `research/content_fixture_results_1076226.json` and retained visual evidence | Runtime and catalog-slot rendering verified |
| Rollback | Installer snapshot restoration test and timestamped backup path | Passed |
| Experiment isolation | `inactive_mods` and game backup locations | Passed |

## Release fingerprint

- Portable executable: `dist/EnshroudedModHub.exe`
- Version: `1.0.1`
- Size: `19,101,504` bytes
- SHA-256: `9CAD7436879E8135F2A66C55CE366AAA7D81864830A79F89E4E1B2BCB2D371EA`
- Installer: `packaging/Output/EnshroudedModHub-Setup.exe`
- Installer size: `20,705,396` bytes
- Installer SHA-256: `F824E6AAE51905271797086606998C671FA4DEAB4A64DD632788C5AB1FF8EEBA`
- Source test count recorded in the release manifest: `217`

## Architecture summary

The Control Center now has a registry-driven GUI over the backend service
families. Content creation flows through validation, donor/resource
relationships, publication planning, asset and package integrity checks, and
evidence records. Research-only operations remain explicitly marked and do
not silently become production deployments.

Deployment is transactional: generated files are staged, owned files are
hashed, previous versions are snapshotted, stale generated files are removed
only inside an owned package, and verification failure restores the complete
prior snapshot. Health reports now distinguish `verified`,
`updated_by_control_center`, `user_modified`, `missing`, and `untracked`
states. Historical EML errors are retained for diagnostics but do not make the
current runtime unhealthy after a newer successful registry session.

## Known limitations

- The existing bed evidence proves registration and an additional catalog
  slot rendering. Custom localization consumption and independent imported
  icon rendering remain research boundaries documented in the research notes.
- Broader content families still require their own controlled runtime fixtures.

