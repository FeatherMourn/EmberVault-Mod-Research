# EML metadata-only lookup upgrade — 2026-09-27

The rebuilt EML source now exposes:

`game.assets.get_resource_metadata(guid, type, part)`

The function checks resource identity without creating a decoded
`ResourceInfo` value. It returns `{ guid, type, part }` or `nil`, allowing
unsupported resource families to be investigated without entering descriptor
reflection.

The release `dinput8-proxy` build completed successfully after the change.
The matching read-only probe is staged at
`research/probes/template_metadata_probe_1076226` and is intentionally not
installed into the live game while the user is playing.

The next controlled test requires installing the rebuilt proxy with the normal
backup/rollback procedure, then running only this probe. No mutation should be
attempted until metadata lookup returns safely.
