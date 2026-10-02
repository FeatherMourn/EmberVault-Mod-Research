# Current-source release verification — 2026-09-29

Control Center 1.0.2 was rebuilt from the current GitHub source after the
Research Lab wizard and release-versioning improvements were integrated.

## Artifacts

- Portable: `dist/EnshroudedModHub.exe`
  - Size: `383542903` bytes
  - SHA-256: `D414B6A2088600074C2549328E9D7244A89A058F4B75E22D9CCB2A9BAACC524F`
- Installer: `packaging/Output/EnshroudedModHub-1.0.2-Setup.exe`
  - Size: `367498682` bytes
  - SHA-256: `B956DB84C13267FDA5DF1966D48FF6025F8973A249BDD76408E51A7FDD0BCBD1`
- Documentation bundle: `dist/EnshroudedModHub-Docs-1.0.2.zip`
  - Size: `19809` bytes
  - SHA-256: `67E78F99F7F6132E9266D975485DCECCEC0923FDB990C6DEA59D8BC3E3F0DF67`

## Verification

- Full automated suite: 667 tests passed.
- Portable launch smoke: passed; the GUI responded and shut down cleanly.
- Installer smoke: passed; installed executable matched the portable hash,
  upgrade preservation passed, and uninstall preserved the user profile.
- PyInstaller: 6.22.3.
- Inno Setup: 6.7.3.
- Enshrouded was not started or modified during this verification record.

The release remains subject to the capability classifications in the current
capability snapshot. Research-only engine boundaries are not promoted by a
successful package build alone.
