# Current-source release verification — 2026-09-30

Control Center 1.0.2 was rebuilt from the current GitHub source after the
beginner builder workflow and research-profile isolation guard were integrated.

## Artifacts

- Portable: `dist/EnshroudedModHub.exe`
  - Size: `428492379` bytes
  - SHA-256: `ABC2B973C455BF5E662A673A839E380CB7330FC217B8ACA9286133D0B67F5AAD`
- Installer: `packaging/Output/EnshroudedModHub-1.0.2-Setup.exe`
  - Size: `412373395` bytes
  - SHA-256: `AE04E407B3D095CD9A5BDAF7B17F81DA654F9414808C0DBBE18D2C3FA22721A8`
- Documentation bundle: `dist/EnshroudedModHub-Docs-1.0.2.zip`
  - Size: `22990` bytes
  - SHA-256: `81B7B803B1CF10A0A63603A82A70BA25BF2BB3DBF9780D467C3FD872A086B149`

## Verification

- Full automated suite: 722 tests passed.
- Portable launch smoke: passed; the GUI responded and shut down cleanly.
- Installer smoke: passed; the installed executable matched the portable hash,
  upgrade preservation passed, uninstall completed, and the user profile was
  preserved.
- Release manifest verification: passed.
- Milestone gate: passed.
- PyInstaller: 6.22.3.
- Inno Setup: 6.7.3.
- Enshrouded was not started or modified during this verification record.

The release remains subject to the capability classifications in the current
capability snapshot. Research-only engine boundaries are not promoted by a
successful package build alone.
