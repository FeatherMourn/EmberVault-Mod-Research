# Current-source release verification — 2026-09-28

Control Center 1.0.2 was rebuilt after integrating runtime EML API detection
and pre-deployment API compatibility enforcement.

## Artifacts

- Portable: `dist/EnshroudedModHub.exe`
  - Size: `32965140` bytes
  - SHA-256: `771D33BBF1BE52B000A1B8BDEEC32CA20E20AD83773E91FBBCDD3E5FD6692010`
  - Product version: `1.0.2`
- Installer: `packaging/Output/EnshroudedModHub-1.0.2-Setup.exe`
  - Size: `34411149` bytes
  - SHA-256: `5A3E58CC3733616E2A8A23BFB7E82DB15CFB4394C6380CF48D29F3B0383AEA24`
  - Product version: `1.0.2`
- Documentation: `dist/EnshroudedModHub-Docs-1.0.2.zip`
  - Size: `16948` bytes
  - SHA-256: `726EE39D82B8A57F9BB037BD8312F695CC8476C4777173A1D31FA5081F159ACB`

## Verification

- PyInstaller 6.22.3 produced the portable executable from current source.
- Inno Setup 6.7.3 produced the installer from current source.
- The portable GUI opened the Control Center window, remained responsive,
  closed through its normal window action, left no process behind, and did
  not launch Enshrouded.
- The isolated installer test confirmed that the installed executable SHA-256
  exactly matches the portable executable.
- Clean installation and same-version upgrade returned success.
- A user profile created after installation survived the upgrade and uninstall.
- Uninstall removed all owned application and documentation files.
- Release manifest size and SHA-256 verification passed.

The previous artifacts are recoverable from
`packaging/release_backups/20260928_api_deployment`.
