# EML metadata enumeration release — 2026-09-27

## Change

Added `game.assets.get_resource_metadata_by_type(type)` to the Lua asset API.
The function enumerates resource GUID, qualified type name, and part index from
the KFC index without constructing reflected resource payloads.

## Build evidence

- Package: `dinput8-proxy`
- Build: release
- Artifact: `H:\enshroudedresearch\external\kfc-parser-source\target\release\dinput8.dll`
- Size: `10677760` bytes
- SHA-256: `2681DF37AA8F4D0B6EF77450904638D85395946B0B965589C681148EC08365B0`
- `cargo check -p mod-loader-lua`: passed
- `cargo build --release -p dinput8-proxy`: passed
- Live installation: not replaced

## Safety boundary

This API is discovery-only. It does not prove that payload decoding or writes
are safe for a resource family. The settings module remains research-only until
a separately guarded payload-access path is established.
