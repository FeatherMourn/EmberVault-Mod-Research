# Settings metadata probe — 2026-09-27

This probe targets `keen::GameSettingsPresetsResource` and `keen::FbUiBundle`
through `game.assets.get_resource_metadata_by_type`. It enumerates only resource
identity rows and never asks EML to decode reflected payloads or perform writes.

The probe is `research-only` and requires the rebuilt EML API. A successful run
will establish whether these families can be discovered safely before a future
guarded payload-access API is attempted.
