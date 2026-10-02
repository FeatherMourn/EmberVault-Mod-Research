# Clean Installation Verification — historical 1.0.1 record

This document records the completed 1.0.1 clean-install run. It is retained as
historical evidence and is not evidence that the 1.0.2 binaries have undergone
the same clean-install run.

## Results

- Installed into a fresh temporary directory successfully.
- Installed documentation files were present under `docs/`.
- Installed executable reported version `1.0.1`.
- Installed `EnshroudedModHub.exe --status --game-dir <game>` returned exit
  code 0 and produced `control_center.health.v1` with current runtime
  `healthy`.
- Normal installed GUI launch remained alive during the smoke-test window.
- Uninstall completed with exit code 0 when run after the GUI process stopped.
- Uninstall-only verification removed all installed files.
- Upgrade verification preserved a user-created profile and backup file.
- Final artifact sizes and SHA-256 values matched the 1.0.1 manifest.

User-created profiles, backups, logs, and projects are not treated as
installer-owned payload files and are preserved by uninstall policy.

## Current 1.0.2 verification

The active release is 1.0.2. Its artifact sizes and hashes are verified by
`tools/verify_release.py` against
`packaging/RELEASE_MANIFEST_1.0.2.json`.

A fresh isolated installer run was completed on 2026-09-27:

- Installer exit code: `0`.
- Upgrade/reinstall exit code: `0`.
- Installed payload contained the executable and four documentation files,
  plus the two uninstaller files.
- Uninstaller exit code: `0`.
- Fresh-install uninstall left zero files.
- A user-created `profiles/user-profile.json` survived the upgrade and also
  survived uninstall, confirming it is not installer-owned.

This verifies the 1.0.2 install, upgrade-preservation, and uninstall behavior
in an isolated temporary directory. It does not install or modify the live
Enshrouded game directory.

The repeatable command is:

`python tools/verify_installer_smoke.py packaging/Output/EnshroudedModHub-1.0.2-Setup.exe --output research/INSTALLER_SMOKE_1.0.2_20260927.json`

Its machine-readable result is valid and records the preserved user profile
and the expected uninstaller self-retention.
