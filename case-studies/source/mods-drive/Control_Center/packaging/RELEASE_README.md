# Enshrouded Mod Hub 1.0.2

## Artifacts

- `../dist/EnshroudedModHub.exe` — portable application.
- `Output/EnshroudedModHub-1.0.2-Setup.exe` — Windows installer.
- `RELEASE_MANIFEST_1.0.2.json` — SHA-256 and size verification data.
- `../research/` — research-only probes and evidence; not a production mod pack.
- `../build/`, `../packaging/build/`, and `../tests/` — development artifacts; do not distribute.

## Installation

Run `Output/EnshroudedModHub-1.0.2-Setup.exe` and choose the installation directory.
The installer creates Start Menu and desktop shortcuts. The portable build can
be run directly without installation.

Before managing a live game installation, select the correct Enshrouded game
directory in the Control Center and create or select a profile. The platform's
deployment service creates ownership records and rollback backups before it
changes managed files.

## Verification

Run `python tools/verify_release.py` from the Control Center project root to
verify every listed artifact. The portable release was rebuilt with PyInstaller
6.22.3, the installer was rebuilt with Inno Setup 6.7.3, and the automated
suite passes 217 tests.

## Rollback

Use the Control Center restore/rollback actions for managed installations.
Do not delete backup directories manually while a deployment or game session
is active.
